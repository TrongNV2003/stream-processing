import os
from abc import ABC, abstractmethod

import torch
from loguru import logger
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoConfig, AutoModelForSequenceClassification

from stream_processing.setting.common import Engine
from stream_processing.nlp.engine.onnx_optimizer import convert_to_onnx
from stream_processing.utils.huggingface_util import load_model_from_huggingface
from stream_processing.setting.config import model_config

class ModelLoader(ABC):
    @abstractmethod
    def load_model(self, local_model_path: str, config: AutoConfig, device: torch.device):
        pass

class OnnxClsModelLoader(ModelLoader):
    def load_model(self, local_model_path: str, config: AutoConfig, device: torch.device):
        onnx_model_path = os.path.join(local_model_path, "onnx_o4")
        provider = "CUDAExecutionProvider" if torch.cuda.is_available() else "CPUExecutionProvider"
        
        local_model_path = load_model_from_huggingface(
            local_dir=model_config.local_dir,
            huggingface_repo_id=model_config.huggingface_repo_id
        )
        
        if os.path.exists(onnx_model_path):
            logger.info(f"Loading ONNX model from {onnx_model_path}")
            return ORTModelForSequenceClassification.from_pretrained(
                onnx_model_path, use_io_binding=True, provider=provider
            ).to(device)

        logger.info(f"Converting PyTorch model to ONNX at {onnx_model_path}")
        convert_to_onnx(ORTModelForSequenceClassification, local_model_path, onnx_model_path)
        return ORTModelForSequenceClassification.from_pretrained(
            onnx_model_path, use_io_binding=True, provider=provider
        ).to(device)

class TorchClsModelLoader(ModelLoader):
    def load_model(self, local_model_path: str, config: AutoConfig, device: torch.device):
        local_model_path = load_model_from_huggingface(
            local_dir=os.path.dirname(local_model_path),
            huggingface_repo_id=model_config.huggingface_repo_id
        )
        
        logger.info(f"Loading PyTorch model from {local_model_path}")
        model = AutoModelForSequenceClassification.from_pretrained(
            local_model_path, config=config, torch_dtype=torch.float16
            )
        model.to(device)
        model.eval()
        return model
    
class ModelLoaderFactory:
    @staticmethod
    def get_model_loader(engine: Engine) -> ModelLoader:
        if engine == Engine.ONNX:
            return OnnxClsModelLoader()
        elif engine == Engine.TORCH:
            return TorchClsModelLoader()
        else:
            raise ValueError(f"Unsupported engine type: {engine}")