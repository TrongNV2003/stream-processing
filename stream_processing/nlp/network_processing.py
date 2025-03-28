import time
import torch
import onnxruntime
import pandas as pd
from typing import List
from transformers import AutoTokenizer
from datetime import datetime, timezone
from prometheus_client import Counter, Histogram

from stream_processing.setting.constants import ATTACKID2LABEL
from stream_processing.logging.logging_monitor import AppLogger
from stream_processing.modules.kafka_consumer import create_consumer
from stream_processing.modules.kafka_producer import KafkaProducerWrapper
from stream_processing.setting.config import kafka_config, attack_model_config

app_logger = AppLogger.get_instance()

def build_context(data: dict, sep_token: str) -> str:
    selected_columns = [
        'Protocol', 'Flow Duration', 'Tot Fwd Pkts', 'Tot Bwd Pkts', 
        'TotLen Fwd Pkts', 'TotLen Bwd Pkts', 'Fwd Pkt Len Max', 
        'Fwd Pkt Len Mean', 'Bwd Pkt Len Max', 'Flow Byts/s', 
        'Flow Pkts/s', 'Flow IAT Mean', 'Flow IAT Max', 'SYN Flag Cnt', 
        'RST Flag Cnt', 'PSH Flag Cnt', 'ACK Flag Cnt', 'Down/Up Ratio', 
        'Pkt Size Avg', 'Active Mean'
    ]
    context_parts = []
    for col in selected_columns:
        value = data.get(col, 0)
        if isinstance(value, float) and (pd.isna(value) or value in [float('inf'), float('-inf')]):
            value = 0
        context_parts.append(f"{col.replace(' ', '_')}_is_{value}")
    return sep_token.join(context_parts)

class NetworkInferenceProcessor:
    def __init__(self):
        # Prometheus scrape tại port 8000
        self.message_counter = Counter('processed_messages_total', 'Total messages processed')
        self.latency_histogram = Histogram('processing_latency_seconds', 'Latency of processing messages')
        self.attack_counter = Counter('detected_attacks_total', 'Total detected attacks')

        self.tokenizer = AutoTokenizer.from_pretrained(attack_model_config.tokenizer_path)
        self.session = onnxruntime.InferenceSession(
            attack_model_config.onnx_model_path,
            providers=["CUDAExecutionProvider"] if torch.cuda.is_available() else ["CPUExecutionProvider"]
        )
        self.sess_output = [out.name for out in self.session.get_outputs()]
        
        self.consumer = create_consumer(kafka_config.raw_data_topic, group_id="network_inference_group") 
        self.producer = KafkaProducerWrapper()
        self.session_id = f"session_{datetime.now().timestamp()}"


    def process_stream(self):
        app_logger.log("Starting Network Inference Processor stream...")
        for message in self.consumer:
            try:
                data = message.value
                input_text = build_context(data, self.tokenizer.sep_token)
                self._process_query(input_text, data)
                
            except Exception as e:
                app_logger.log(f"Error processing message: {str(e)}", level="error")
        
        app_logger.flush()
        
    def _process_query(self, input_text: List[tuple], data: dict):
        trace = app_logger.start_trace(f"{data.get('id', 'unknown')}")
            
        # Observation 1: Ghi dữ liệu đầu vào
        trace.generation(
            name="input",
            input=data,
            metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
        )

        start_time = time.time()

        inputs = self.tokenizer(
            [input_text],
            truncation=True,
            padding=True,
            max_length=512,
            return_tensors="pt"
        )
        sess_input = {
            "input_ids": inputs["input_ids"].cpu().numpy(),
            "attention_mask": inputs["attention_mask"].cpu().numpy()
        }

        outputs = self.session.run(self.sess_output, sess_input)
        logits = torch.from_numpy(outputs[0])
        preds = torch.argmax(logits, dim=1).cpu().numpy().tolist()
        predicted_label = ATTACKID2LABEL[preds[0]]
        confidence = torch.softmax(logits, dim=1)[0, preds[0]].item()
        
        end_time = time.time()
        latency = end_time - start_time

        self.latency_histogram.observe(latency)
        self.message_counter.inc()

        latency_ms = latency * 1000
        start_time_iso = datetime.fromtimestamp(start_time).isoformat()
        end_time_iso = datetime.fromtimestamp(end_time).isoformat()

        result = {
            "id": data.get("id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "start_time": start_time_iso,
            "end_time": end_time_iso,
            "latency": latency_ms,
            "input_text": input_text,
            "truth_labels": data.get("Label", []),
            "predicted_label": predicted_label,
            "confidence": confidence,
            "raw_data": data,
        }

        # Count detected attacks
        attack_labels = ["DDoS attacks", "DoS attacks", "Bot"]
        if result["predicted_label"] in attack_labels:
            self.attack_counter.inc()


        # Observation 2: Ghi kết quả sau xử lý
        processed_gen = trace.generation(
            name=f"processed_network_traffic",
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

        attack_labels = ["DDoS attacks", "DoS attacks", "Bot"]
        
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
        self.producer.produce(kafka_config.processed_attack_data_topic, result)
        app_logger.log(f"Processed ID: {result['id']}", trace=trace)
