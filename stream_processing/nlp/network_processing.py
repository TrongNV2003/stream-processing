import time
import torch
import onnxruntime
from datetime import datetime, timezone
from prometheus_client import Counter, Histogram
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from stream_processing.nlp.data_loader import DataLoader
from stream_processing.setting.constants import ATTACKID2LABEL
from stream_processing.logging.logging_monitor import AppLogger
from stream_processing.modules.kafka_consumer import create_consumer
from stream_processing.modules.kafka_producer import KafkaProducerWrapper
from stream_processing.setting.config import kafka_config, attack_model_config

app_logger = AppLogger.get_instance()

class NetworkInferenceProcessor:
    def __init__(self, use_torch=False, processing_mode="streaming", batch_size=8, batch_timeout=0.1):
        """
        Args:
            use_torch (bool): Use PyTorch model if True, ONNX if False.
            processing_mode (str): Processing mode, either "streaming" or "micro_batch".
            batch_size (int): Maximum number of messages in a micro-batch.
            batch_timeout (float): Maximum time (in seconds) to wait for a micro-batch.
        """
        self.use_torch = use_torch
        self.processing_mode = processing_mode
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        
        # Prometheus metrics
        self.message_counter = Counter('processed_messages_total', 'Total messages processed')
        self.latency_histogram = Histogram('processing_latency_seconds', 'Latency of processing messages')
        self.attack_counter = Counter('detected_attacks_total', 'Total detected attacks')

        self.tokenizer = AutoTokenizer.from_pretrained(attack_model_config.tokenizer_path)
        self.dataloader = DataLoader()
        
        self.consumer = create_consumer(kafka_config.raw_data_topic, group_id="network_inference_group") 
        self.producer = KafkaProducerWrapper()
        self.session_id = f"session_{datetime.now().timestamp()}"
        
        if self.use_torch:
            self.model = AutoModelForSequenceClassification.from_pretrained(
                attack_model_config.pytorch_model_path,
                num_labels=len(ATTACKID2LABEL)
            )
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.model.eval()
        else:
            self.session = onnxruntime.InferenceSession(
                attack_model_config.onnx_model_path,
                providers=["CUDAExecutionProvider"] if torch.cuda.is_available() else ["CPUExecutionProvider"]
            )
            self.sess_output = [out.name for out in self.session.get_outputs()]
        
    def process_stream(self):
        """
        Process the Kafka stream in streaming or micro-batch mode.
        """
        app_logger.log(f"Starting Network Inference Processor in {self.processing_mode} mode...")

        if self.processing_mode == "micro_batch":
            self._process_micro_batch()
        elif self.processing_mode == "streaming":
            self._process_pure_streaming()
        else:
            app_logger.log(f"Invalid processing mode: {self.processing_mode}", level="error")
            return
        
        app_logger.flush()

    def _process_pure_streaming(self):
        """
        Process messages in pure streaming mode (one message at a time).
        """
        for message in self.consumer:
            try:
                data = message.value
                if not isinstance(data, dict):
                    app_logger.log(f"Invalid message data: {data} is not a dictionary", level="error")
                    continue
                input_text = self.dataloader.build_context(data, self.tokenizer.sep_token)
                self._process_query([input_text], [data])
            except Exception as e:
                app_logger.log(f"Error processing message: {str(e)}", level="error")

    def _process_micro_batch(self):
        """
        Process messages in micro-batch mode (accumulate messages into batches).
        """
        batch = []
        batch_start_time = time.time()

        for message in self.consumer:
            try:
                data = message.value
                if not isinstance(data, dict):
                    app_logger.log(f"Invalid message data: {data} is not a dictionary", level="error")
                    continue
                input_text = self.dataloader.build_context(data, self.tokenizer.sep_token)
                batch.append((input_text, data))

                # Check if batch is ready
                if len(batch) >= self.batch_size or (time.time() - batch_start_time) >= self.batch_timeout:
                    input_texts, datas = zip(*batch)
                    self._process_query(list(input_texts), list(datas))
                    batch = []
                    batch_start_time = time.time()
            except Exception as e:
                app_logger.log(f"Error processing message: {str(e)}", level="error")

        if batch:
            input_texts, datas = zip(*batch)
            self._process_query(list(input_texts), list(datas))

    def _process_query(self, input_texts: list, datas: list):
        """
        Process a batch of input texts and their corresponding data.

        Args:
            input_texts (list): List of input texts to process.
            datas (list): List of raw data dictionaries.
        """
        trace = app_logger.start_trace(f"batch_{datetime.now().timestamp()}")

        # Observation 1: Log input data
        trace.generation(
            name="input",
            input={"count": len(datas), "ids": [data.get('id', 'unknown') for data in datas]},
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        start_time = time.time()

        inputs = self.tokenizer(
            input_texts,
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        )

        if self.use_torch:
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            preds = torch.argmax(logits, dim=1).cpu().numpy().tolist()
            confidences = torch.softmax(logits, dim=1)[range(len(preds)), preds].cpu().numpy().tolist()
        else:
            sess_input = {
                "input_ids": inputs["input_ids"].cpu().numpy(),
                "attention_mask": inputs["attention_mask"].cpu().numpy()
            }
            outputs = self.session.run(self.sess_output, sess_input)
            logits = torch.from_numpy(outputs[0])
            preds = torch.argmax(logits, dim=1).cpu().numpy().tolist()
            confidences = torch.softmax(logits, dim=1)[range(len(preds)), preds].cpu().numpy().tolist()

        end_time = time.time()
        latency = end_time - start_time
        self.latency_histogram.observe(latency)
        latency_ms = latency * 1000

        self.message_counter.inc(len(datas))

        start_time_iso = datetime.fromtimestamp(start_time).isoformat()
        end_time_iso = datetime.fromtimestamp(end_time).isoformat()

        results = []
        attack_labels = ["DDoS attacks", "DoS attacks", "Bot"]

        for i, (data, input_text, pred, confidence) in enumerate(zip(datas, input_texts, preds, confidences)):
            predicted_label = ATTACKID2LABEL[pred]

            result = {
                "id": data.get("id"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "start_time": start_time_iso,
                "end_time": end_time_iso,
                "latency": latency_ms / len(datas),
                "input_text": input_text,
                "truth_labels": data.get("Label", []),
                "predicted_label": predicted_label,
                "confidence": confidence,
                "raw_data": data,
            }

            if result["predicted_label"] in attack_labels:
                self.attack_counter.inc()

            # Observation 2: Log processed result
            processed_gen = trace.generation(
                name=f"processed_network_traffic_{i}",
                input=result["input_text"],
                output=result["predicted_label"],
                metadata={
                    "id": result["id"],
                    "timestamp": result["end_time"],
                    "label": result["predicted_label"],
                    "confidence": result["confidence"],
                },
                session_id=self.session_id
            )

            trace.score(
                name="confidence_score",
                value=result["confidence"],
                generation_id=processed_gen.id
            )

            if result["predicted_label"] in attack_labels:
                app_logger.log(
                    f"Detected attack - ID: {result['id']}, Confidence: {result['confidence']}",
                    level="warning",
                    trace=trace
                )
                trace.event(
                    name="attack_alert",
                    input=result["raw_data"],
                    output=result["predicted_label"],
                    metadata={
                        "id": result["id"],
                        "timestamp": result["end_time"],
                        "attack_type": result["predicted_label"],
                        "confidence": result["confidence"],
                        "raw_data": result["raw_data"]
                    },
                    level="WARNING",
                )

            results.append(result)

        for result in results:
            self.producer.produce(kafka_config.processed_attack_data_topic, result)
        app_logger.log(f"Processed batch of {len(datas)} messages", trace=trace)