import uvicorn
import logging
import argparse
import threading
from prometheus_client import start_http_server

from stream_processing.api import app
from stream_processing.db.storage import DataStorageService
from stream_processing.logging.logging_monitor import AppLogger
from stream_processing.nlp.network_processing import NetworkInferenceProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("App")
app_logger = AppLogger.get_instance()


parser = argparse.ArgumentParser()
parser.add_argument("--processing_mode", type=str, default="streaming", choices=["streaming", "micro_batch"], required=True)
parser.add_argument("--batch_size", type=int, default=8, help="batch size for micro batch", required=True)
parser.add_argument("--batch_timeout", type=float, default=0.1, help="set process timeout", required=True)
parser.add_argument("--use_torch", action="store_true", default=False)
args = parser.parse_args()


def start_network_processor():
    try:
        processor = NetworkInferenceProcessor(
            use_torch=args.use_torch,
            processing_mode=args.processing_mode,
            batch_size=args.batch_size,
            batch_timeout=args.batch_timeout
        )
        
        logger.info("Starting Network Inference Processor...")
        processor.process_stream()
    except Exception as e:
        logger.error(f"Network Processor failed: {str(e)}")

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