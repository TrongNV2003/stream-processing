import os
from loguru import logger
from transformers import AutoModelForSequenceClassification
from huggingface_hub import snapshot_download

def load_model_from_huggingface(local_dir: str, huggingface_repo_id: str) -> str:
    os.makedirs(local_dir, exist_ok=True)
    
    model_name = huggingface_repo_id.split("/")[-1]
    local_model_path = os.path.join(local_dir, model_name)
    
    if os.path.exists(local_model_path) and os.listdir(local_model_path):
        logger.info(f"Found local model at {local_model_path}")
        return local_model_path
    
    logger.info(f"No local model found at {local_model_path}. Downloading from Hugging Face: {huggingface_repo_id}")
    snapshot_download(
        repo_id=huggingface_repo_id,
        local_dir=local_model_path,
        local_dir_use_symlinks=False,
        cache_dir=local_dir
    )
    
    logger.info(f"Model downloaded and saved to {local_model_path}")
    return local_model_path
