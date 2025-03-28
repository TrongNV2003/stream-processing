# import json
# from kafka import KafkaConsumer

# consumer = KafkaConsumer(
#     'raw_data',
#     bootstrap_servers='localhost:9092',
#     auto_offset_reset='earliest',
#     value_deserializer=lambda v: json.loads(v.decode('utf-8'))
# )

# for msg in consumer:
#     data = msg.value
#     print(f"ID: {data['id']}")
#     print(f"History: {data['history']}")
#     print(f"Current Message: {data['current_message']}")
#     print(f"Intent: {data['label_intent']}")
#     print("-" * 50)
from stream_processing.nlp.network_processing import NetworkInferenceProcessor

if __name__ == "__main__":
    processor = NetworkInferenceProcessor()
    processor.process_stream()