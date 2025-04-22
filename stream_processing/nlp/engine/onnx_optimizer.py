from optimum.onnxruntime import AutoOptimizationConfig, ORTOptimizer


def convert_to_onnx(ort_class, model_name: str, save_dir: str) -> str:
    model = ort_class.from_pretrained(model_name, export=True)
    
    # Create the optimizer
    optimizer = ORTOptimizer.from_pretrained(model)
    
    # Define the optimization configuration
    optimization_config = AutoOptimizationConfig.O4(use_raw_attention_mask=True)
    
    # Optimize the model
    optimizer.optimize(save_dir=save_dir, optimization_config=optimization_config)
    
    return save_dir