from enum import Enum

class Engine(str, Enum):
    TORCH = "torch"
    ONNX = "onnx"
    TRANSFORMERS = "transformers"
    
class Device(str, Enum):
    CPU = "cpu"
    GPU = "gpu"