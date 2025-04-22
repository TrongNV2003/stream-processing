from pydantic import Field
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class AttackModelConfig(BaseSettings):
    local_dir: str = Field(..., alias="LOCAL_DIR")
    huggingface_repo_id: str = Field(..., alias="HUGGINGFACE_REPO_ID")
    

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


model_config = AttackModelConfig()
kafka_config = KafkaConfig()
mongo_config = MongoConfig()
langfuse_config = LangfuseConfig()
