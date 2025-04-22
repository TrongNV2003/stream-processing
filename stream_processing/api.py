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

async def ingest_in_background(chunks: list[bytes]):
    producer_service = KafkaProducerService()
    for chunk in chunks:
        await producer_service.ingest_data(kafka_config.raw_data_topic, chunk)

@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    chunk_size = 1024 * 1024
    chunks = []
    try:
        with open("stream_processing/data_test_stream/dataset.csv", "rb") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
            
        background_tasks.add_task(ingest_in_background, chunks) # Chạy trong background
        return {"status": "success", "message": "Record network traffic to Kafka"}
    except Exception as e:
        app_logger.log(f"Ingest error: {str(e)}", level="error")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/upload")
async def ingest_upload(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only csv files are supported")
    
    chunk_size = 1024 * 1024
    chunks = []
    
    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
        
        background_tasks.add_task(ingest_in_background, chunks)
        return {"status": "success", "message": "Record network traffic to Kafka"}
    
    except Exception as e:
        app_logger.log(f"Ingest upload error: {str(e)}", level="error")
        raise HTTPException(status_code=500, detail=str(e))

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
