from pydantic import Field
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class AttackModelConfig(BaseSettings):
    onnx_model_path: str = Field(..., alias="ATTACK_MODEL_PATH")
    tokenizer_path: str = Field(..., alias="ATTACK_TOKENIZER_PATH")
    pytorch_model_path: str = Field(..., alias="PYTORCH_MODEL_PATH")

class KafkaConfig(BaseSettings):
    kafka_service: str = Field(..., alias="KAFKA_BOOTSTRAP_SERVERS")
    raw_data_topic: str = Field(..., alias="RAW_DATA_TOPIC")
    processed_attack_data_topic: str = Field(..., alias="PROCESSED_ATTACK_DATA_TOPIC")

class MongoConfig(BaseSettings):
    mongo_uri: str = Field(..., alias="MONGO_URI")
    db_name: str = Field(..., alias="DB_NAME")
    results_attack_collection: str = Field(..., alias="RESULTS_ATTACK_COLLECTION")

class LangfuseConfig(BaseSettings):
    host: str = Field(..., alias="LANGFUSE_HOST")
    secret_key: str = Field(..., alias="LANGFUSE_SECRET_KEY")
    public_key: str = Field(..., alias="LANGFUSE_PUBLIC_KEY")


attack_model_config = AttackModelConfig()
kafka_config = KafkaConfig()
mongo_config = MongoConfig()
langfuse_config = LangfuseConfig()
