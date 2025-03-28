from datetime import datetime

from stream_processing.setting.config import kafka_config
from stream_processing.db.connection import DatabaseHandler
from stream_processing.logging.logging_monitor import AppLogger
from stream_processing.modules.kafka_consumer import create_consumer

app_logger = AppLogger.get_instance()

class DataStorageService:
    def __init__(self):
        self.database_handler = DatabaseHandler()

    def storage_data_consumer(self):
        """
        Consumer này sẽ đọc các message từ Kafka topic PROCESSED_DATA_TOPIC
        và lưu trữ chúng vào MongoDB sử dụng StorageService.
        """
        consumer = create_consumer(kafka_config.processed_attack_data_topic, group_id="mongodb_storage_group")
        
        for message in consumer:
            try:
                data = message.value
                data["end_time"] = datetime.now().isoformat()
                start_time = datetime.fromisoformat(data["start_time"])
                end_time = datetime.fromisoformat(data["end_time"])
                latency = (end_time - start_time).total_seconds() * 1000
                data["latency"] = latency

                self.database_handler.save_result(data)
                app_logger.log(f"Stored record ID: {data.get('id')} with latency {latency}ms")
                
            except Exception as e:
                app_logger.log(f"Error storing: {str(e)}", level="error")
        
        app_logger.flush()

