import logging
from langfuse import Langfuse

from stream_processing.setting.config import langfuse_config
from stream_processing.setting.constants import OUTPUT_LOG_FILE

class AppLogger:
    _instance = None

    @staticmethod
    def get_instance():
        if AppLogger._instance is None:
            AppLogger()
        return AppLogger._instance

    def __init__(self):
        if AppLogger._instance is not None:
            raise Exception("This class is a singleton!")
        AppLogger._instance = self

        # local logging
        self.logger = logging.getLogger("AppLogger")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(OUTPUT_LOG_FILE),
                logging.StreamHandler()
            ]
        )

        # langfuse logging
        self.langfuse = Langfuse(
            public_key=langfuse_config.public_key,
            secret_key=langfuse_config.secret_key,
            host=langfuse_config.host,
        )
        self.logger.info("Langfuse initialized with host: %s", langfuse_config.host)

    def start_trace(self, name: str):
        return self.langfuse.trace(name=name)
    
    def log(self, message: str, level: str = "info", trace=None):
        if level == "info":
            self.logger.info(message)
            if trace:
                trace.event(name="info", metadata={"message": message})
        elif level == "error":
            self.logger.error(message)
            if trace:
                trace.event(name="error", metadata={"message": message}, level="ERROR")
        elif level == "warning":
            self.logger.warning(message)
            if trace:
                trace.event(name="warning", metadata={"message": message}, level="WARNING")
        else:
            self.logger.debug(message)
            if trace:
                trace.event(name="debug", metadata={"message": message})
    
    def flush(self):
        """Đảm bảo tất cả log được gửi lên Langfuse."""
        self.langfuse.flush()