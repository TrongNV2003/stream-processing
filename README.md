# Stream Processing for Network Attack Detection

A real-time stream processing system for network traffic analysis and attack detection using Kafka, machine learning models, and microservices architecture.

## 🏗️ Architecture Overview

This system implements a complete stream processing pipeline for network security:

```
Data Ingestion → Kafka Producer → ML Processing → Attack Detection → Results Storage
     ↓              ↓                 ↓              ↓              ↓
  FastAPI      Raw Data Topic    NLP Pipeline   Processed Topic   MongoDB
```

## 🚀 Key Features

- **Real-time Stream Processing**: Kafka-based streaming with configurable processing modes
- **ML-powered Attack Detection**: Uses Hugging Face transformers for network traffic classification
- **Flexible Processing Modes**: 
  - Pure streaming (message-by-message)
  - Micro-batch processing (configurable batch size and timeout)
- **Multi-Engine Support**: PyTorch and ONNX Runtime for model inference
- **Comprehensive Monitoring**: Prometheus metrics and Langfuse observability
- **Scalable Storage**: MongoDB for processed results
- **Production Ready**: Logging, error handling, and performance optimization

## 🛠️ Tech Stack

### Core Technologies
- **Python 3.11**
- **Apache Kafka** - Stream processing platform
- **FastAPI** - Web framework for data ingestion API
- **MongoDB** - Document database for results storage

### Machine Learning
- **PyTorch** - Deep learning framework
- **Transformers** (Hugging Face) - Pre-trained models
- **ONNX Runtime** - Optimized inference engine
- **Pandas** - Data manipulation

### Monitoring & Observability
- **Prometheus** - Metrics collection
- **Langfuse** - ML observability and tracing
- **Custom Logging** - Application-level logging

## 📁 Project Structure

```
stream_processing/
├── api.py                      # FastAPI endpoints for data ingestion
├── app.py                      # Main application entry point
├── data_test_stream/          # Test datasets
├── db/                        # Database components
│   ├── connection.py          # MongoDB connection handler
│   └── storage.py             # Data storage service
├── logging/                   # Logging and monitoring
│   └── logging_monitor.py     # Application logger with tracing
├── modules/                   # Kafka components
│   ├── kafka_consumer.py      # Kafka consumer utilities
│   ├── kafka_producer.py      # Kafka producer wrapper
│   └── kafka_producer_service.py # Producer service layer
├── nlp/                       # Machine learning pipeline
│   ├── data_loader.py         # Data preprocessing
│   ├── pipeline.py            # Main inference pipeline
│   └── engine/                # Model loading engines
├── setting/                   # Configuration management
│   ├── config.py              # Environment-based settings
│   ├── common.py              # Common enums and constants
│   └── constants.py           # Application constants
└── utils/                     # Utility functions
    └── huggingface_util.py    # Model downloading utilities
```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Model Configuration
LOCAL_DIR=/path/to/local/models
HUGGINGFACE_REPO_ID=your-model-repo

# Kafka Configuration  
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
RAW_DATA_TOPIC=raw_network_data
PROCESSED_ATTACK_DATA_TOPIC=processed_attack_data

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
DB_NAME=network_security
RESULTS_ATTACK_COLLECTION=attack_results

# Langfuse Configuration (Optional)
LANGFUSE_HOST=https://your-langfuse-instance
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_PUBLIC_KEY=your-public-key
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11**
2. **Apache Kafka** running on localhost:9092
3. **MongoDB** running on localhost:27017

### Installation

1. Clone the repository:
```bash
git clone https://github.com/TrongNV2003/stream-processing.git
cd stream-processing
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the System

1. **Start the main application:**
```bash
./run.sh
# or
python -m stream_processing.app
```

2. **Ingest data via API:**
```bash
curl -X POST "http://localhost:8000/ingest"
```

## 🔧 System Components

### 1. Data Ingestion (FastAPI)
- RESTful API for data ingestion
- Chunks large files for efficient processing
- Async background task processing

### 2. Stream Processing (Kafka)
- **Producer**: Sends network traffic data to Kafka topics
- **Consumer**: Processes data in real-time or micro-batches
- **Topics**: 
  - `raw_network_data`: Incoming network traffic
  - `processed_attack_data`: ML inference results

### 3. ML Pipeline (NLP)
- **Feature Engineering**: Converts network metrics to text context
- **Model Inference**: Uses transformer models for classification
- **Attack Detection**: Identifies malicious network patterns
- **Batch Processing**: Configurable batch size and timeout

### 4. Data Storage (MongoDB)
- Stores processed results with metadata
- Includes prediction confidence and timing information
- Supports queries for analysis and reporting

## 📊 Monitoring & Metrics

### Prometheus Metrics
- `processed_messages_total`: Total messages processed
- `processing_latency_seconds`: Processing time distribution
- `detected_attacks_total`: Number of attacks detected

### Langfuse Tracing
- End-to-end request tracing
- Model performance monitoring
- Input/output logging for debugging

## 🔍 Processing Modes

### Pure Streaming
```python
processor = NetworkInference(
    processing_mode="streaming",
    # Process one message at a time
)
```

### Micro-batch Processing
```python
processor = NetworkInference(
    processing_mode="micro_batch",
    batch_size=8,           # Messages per batch
    batch_timeout=0.1       # Max wait time (seconds)
)
```

## 🛡️ Network Attack Detection

The system analyzes network traffic features including:
- **Protocol information**
- **Flow duration and packet counts**
- **Byte and packet rates**
- **Flag counts (SYN, RST, PSH, ACK)**
- **Statistical measures** (mean, max, ratios)

### Supported Attack Types
The model can detect various network attacks (configured via `id2label` in model config):
- DDoS attacks
- Port scanning
- Intrusion attempts
- Malicious traffic patterns

## 🚀 Performance Optimizations

- **GPU Acceleration**: Automatic CUDA detection for faster inference
- **ONNX Runtime**: Optimized model execution
- **Batch Processing**: Reduces per-message overhead
- **Async Operations**: Non-blocking I/O operations
- **Connection Pooling**: Efficient database connections

## 🧪 Testing

Use the provided test dataset:
```bash
# Test data is located in data_test_stream/test_dataset.csv
curl -X POST "http://localhost:8000/ingest"
```

## 📈 Scaling Considerations

- **Horizontal Scaling**: Deploy multiple consumer instances
- **Kafka Partitioning**: Distribute load across partitions  
- **Model Optimization**: Use ONNX for production deployments
- **Database Sharding**: Scale MongoDB for large datasets
- **Load Balancing**: Use multiple API instances

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the logs in `logs/app.log`
- Monitor Prometheus metrics for system health

## 🔗 Related Projects

- [Apache Kafka](https://kafka.apache.org/)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [MongoDB](https://www.mongodb.com/)