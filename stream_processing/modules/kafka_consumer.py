import json
from kafka import KafkaConsumer

from stream_processing.setting.config import kafka_config

def create_consumer(topic: str, group_id: str) -> KafkaConsumer:
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=kafka_config.kafka_service,
        auto_offset_reset='earliest',
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )
    return consumer
