import asyncio
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile

from stream_processing.setting.config import kafka_config
from stream_processing.db.connection import DatabaseHandler
from stream_processing.logging.logging_monitor import AppLogger
from stream_processing.modules.kafka_producer_service import KafkaProducerService

app = FastAPI()
app_logger = AppLogger.get_instance()

# MongoDB
def get_storage_service():
    return DatabaseHandler()

async def ingest_in_background(content: bytes):
    producer_service = KafkaProducerService()
    await producer_service.ingest_data(kafka_config.raw_data_topic, content)

@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    with open("stream_processing/data_test_stream/dataset.csv", "rb") as file:
        content = file.read()
        
    background_tasks.add_task(ingest_in_background, content) # Chạy trong background
    return {"status": "success", "message": "Record network traffic to Kafka"}

@app.post("/ingest/upload")
async def ingest_upload(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only csv files are supported")
    
    content = await file.read()
    background_tasks.add_task(ingest_in_background, content)
    return {"status": "success", "message": "Record network traffic to Kafka"}

@app.get("/results")
def get_results(limit: int = 10, service: DatabaseHandler = Depends(get_storage_service)):
    try:
        results = service.get_latest_results(limit=limit)
        for result in results:
            result["_id"] = str(result["_id"])
        return results
    except Exception as e:
        app_logger.log(f"Results error: {str(e)}", level="error")
        raise HTTPException(status_code=500, detail=str(e))
