import torch
import uvicorn
import logging
import threading
from prometheus_client import start_http_server

from stream_processing.api import app
from stream_processing.db.storage import DataStorageService
from stream_processing.logging.logging_monitor import AppLogger
from stream_processing.nlp.pipeline import NetworkInference
from stream_processing.setting.config import model_config
from stream_processing.setting.common import Engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")
app_logger = AppLogger.get_instance()


def start_network_processor():
    try:
        processor = NetworkInference(
            local_dir=model_config.local_dir,
            huggingface_repo_id=model_config.huggingface_repo_id,
            device="cuda" if torch.cuda.is_available() else "cpu",
            engine= Engine.TORCH,
            use_torch=True,
            processing_mode="micro_batch",
            batch_size=8,
            batch_timeout=0.1
        )
        
        logger.info("Starting Network Inference Processor...")
        processor.process_stream()
    except Exception as e:
        logger.error(f"Network Processor failed: {str(e)}", exc_info=True)

def main():
    start_http_server(8000)
    logger.info("Prometheus metrics server started on port 8000")
    
    data_storage_service = DataStorageService()
    t1 = threading.Thread(target=start_network_processor, daemon=True)
    t2 = threading.Thread(target=data_storage_service.storage_data_consumer, daemon=True)
    
    t1.start()
    t2.start()
    
    try:
        logger.info("Starting FastAPI server...")
        uvicorn.run(app, host="0.0.0.0", port=2206)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        app_logger.flush()
        t1.join(timeout=5)
        t2.join(timeout=5)

if __name__ == "__main__":
    main()