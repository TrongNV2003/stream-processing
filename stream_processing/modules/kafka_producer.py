import json
from kafka import KafkaProducer
from tenacity import retry, wait_exponential, stop_after_attempt

from stream_processing.setting.config import kafka_config
from stream_processing.logging.logging_monitor import AppLogger

app_logger = AppLogger.get_instance()

class KafkaProducerWrapper:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_config.kafka_service,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    @retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
    def produce(self, topic: str, message: dict | list):
        try:
            if isinstance(message, list):
                for item in message:
                    message_key = str(item.get("id", "unknown")).encode('utf-8')
                    self.producer.send(topic, key=message_key, value=item)
                    app_logger.log(f"Delivered to {topic} with key {message_key}")
            else:
                message_key = str(message.get("id", "unknown")).encode('utf-8')
                self.producer.send(topic, key=message_key, value=message)
                app_logger.log(f"Delivered to {topic} with key {message_key}")
            self.producer.flush()

        except Exception as e:
            app_logger.log(f"Failed to deliver: {str(e)}", level="error")
            raise
