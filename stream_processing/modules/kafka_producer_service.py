import asyncio
import pandas as pd
from datetime import datetime

from stream_processing.logging.logging_monitor import AppLogger
from stream_processing.modules.kafka_producer import KafkaProducerWrapper

app_logger = AppLogger.get_instance()

class KafkaProducerService:
    def __init__(self, producer: KafkaProducerWrapper = None):
        self.producer = producer or KafkaProducerWrapper()

    async def ingest_data(self, topic: str, file_content: bytes):
        """Gửi dữ liệu lên Kafka"""
        from io import StringIO
        queries = pd.read_csv(StringIO(file_content.decode('utf-8')))
        for _, row in queries.iterrows():
            data = row.to_dict()
            await self._send_query(topic, data)
        app_logger.log(f"Finished sending {len(queries)} records to {topic}")
    
    async def _send_query(self, topic: str, data: dict, throttle_delay: int = 0.01):
        if "id" not in data:
            data["id"] = f"{datetime.now().timestamp()}_{hash(str(data))}"

        self.producer.produce(topic, data)
        app_logger.log(f"Sent record to {topic}: ID {data['id']}")
        await asyncio.sleep(throttle_delay)