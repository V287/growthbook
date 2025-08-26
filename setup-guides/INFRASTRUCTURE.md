# GrowthBook Infrastructure Documentation

> **Comprehensive infrastructure setup for self-hosted GrowthBook deployment on AWS ECS**

## 🏗️ Current Architecture Overview

### Current Setup (POC on EC2)
Our current proof-of-concept runs on a single EC2 instance to validate the GrowthBook integration and workflow.

```
┌─────────────────────────────────────────┐
│              EC2 Instance               │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ GrowthBook  │  │  Exposure API   │   │
│  │   (Docker)  │  │   (FastAPI)     │   │
│  └─────────────┘  └─────────────────┘   │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │        DocumentDB (Local)           ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
                    ↓
        ┌─────────────────────────┐
        │    Redshift Cluster     │
        │   (Direct Connection)   │
        └─────────────────────────┘
```

## 🎯 Production Architecture (ECS Deployment)

### Target Infrastructure

```
                    ┌─────────────────────────────────────┐
                    │               VPC                   │
    ┌───────────────┼─────────────────────────────────────┼──────────────────┐
    │               │                                     │                  │
    │   Public      │              Private                │    Database      │
    │   Subnets     │              Subnets                │    Subnets       │
    │               │                                     │                  │
    │ ┌───────────┐ │  ┌──────────────────────────────┐   │ ┌──────────────┐ │
    │ │    ALB    │ │  │         ECS Cluster          │   │ │  DocumentDB  │ │
    │ │           │ │  │                              │   │ │   Cluster    │ │
    │ └───────────┘ │  │  ┌─────────────────────────┐ │   │ └──────────────┘ │
    │               │  │  │    GrowthBook Service   │ │   │                  │
    │               │  │  │  - NextJS Frontend      │ │   │ ┌──────────────┐ │
    │               │  │  │  - ExpressJS API        │ │   │ │   Redshift   │ │
    │               │  │  │  - Python Stats Engine  │ │   │ │   Cluster    │ │
    │               │  │  └─────────────────────────┘ │   │ └──────────────┘ │
    │               │  │                              │   │                  │
    │               │  │  ┌─────────────────────────┐ │   │                  │
    │               │  │  │   Exposure API Service  │ │   │                  │
    │               │  │  │  - FastAPI Application  │ │   │                  │
    │               │  │  │  - Kafka Producer       │ │   │                  │
    │               │  │  └─────────────────────────┘ │   │                  │
    │               │  └──────────────────────────────┘   │                  │
    └───────────────┼─────────────────────────────────────┼──────────────────┘
                    │                                     │
                    └─────────────────────────────────────┘
                                       ↓
                    ┌─────────────────────────────────────┐
                    │          Kafka Cluster              │
                    │  ┌─────────────────────────────────┐│
                    │  │    Exposure Events Topic        ││
                    │  └─────────────────────────────────┘│
                    └─────────────────────────────────────┘
                                       ↓
                    ┌─────────────────────────────────────┐
                    │    ECS Service (Separate Task)     │
                    │       Kafka Consumer Service       │
                    │  ┌─────────────────────────────────┐│
                    │  │  Batch Process → Redshift       ││
                    │  └─────────────────────────────────┘│
                    └─────────────────────────────────────┘
```

## 🔧 Implementation Details

### 1. Fork & Customization

#### GrowthBook Fork
```bash
# Original repository
git clone https://github.com/growthbook/growthbook.git

# Our fork with customizations
git clone https://github.com/V287/growthbook.git
```

#### Key Modifications
- **DocumentDB Integration**: Replaced MongoDB with AWS DocumentDB
- **Custom Docker Compose**: Added exposure API service
- **VPC Configuration**: Network settings for ECS deployment
- **Security Enhancements**: IAM roles, security groups, encryption

### 2. Custom Services

#### Docker Compose Enhancement
```yaml
version: '3.8'
services:
  growthbook:
    image: growthbook/growthbook:latest
    environment:
      - MONGODB_URI=mongodb://documentdb-cluster:27017/growthbook
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - JWT_SECRET=${JWT_SECRET}
    networks:
      - growthbook-network

  exposure-api:
    build: ./exposure-api
    environment:
      - KAFKA_BROKERS=${KAFKA_BROKERS}
      - REDSHIFT_HOST=${REDSHIFT_HOST}
      - REDSHIFT_USER=${REDSHIFT_USER}
      - REDSHIFT_PASSWORD=${REDSHIFT_PASSWORD}
    networks:
      - growthbook-network
    ports:
      - "8000:8000"

  documentdb:
    image: mongo:latest
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGO_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
    networks:
      - growthbook-network

networks:
  growthbook-network:
    driver: bridge
```

### 3. Exposure API Service

#### Current Implementation (Direct Redshift)
```python
# exposure_api/main.py
from fastapi import FastAPI
import psycopg2
from typing import Dict, Any

app = FastAPI()

@app.post("/exposure")
async def log_exposure(exposure_data: Dict[str, Any]):
    """
    Current: Direct write to Redshift
    Future: Kafka producer
    """
    try:
        # Direct Redshift connection (POC)
        conn = psycopg2.connect(
            host=REDSHIFT_HOST,
            port=5439,
            database=REDSHIFT_DB,
            user=REDSHIFT_USER,
            password=REDSHIFT_PASSWORD
        )
        
        # Insert exposure record
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO growthbook.experiment_exposures 
            (ds_user_id, experiment_id, variation_id, attributes, source, timestamp)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            exposure_data["ds_user_id"],
            exposure_data["experiment_id"], 
            exposure_data["variation_id"],
            json.dumps(exposure_data["attributes"]),
            exposure_data["source"]
        ))
        
        conn.commit()
        return {"status": "success", "exposure_id": generate_id()}
        
    except Exception as e:
        logger.error(f"Exposure logging failed: {e}")
        return {"status": "error", "message": str(e)}
```

#### Future Implementation (Kafka)
```python
# exposure_api/kafka_producer.py
from kafka import KafkaProducer
import json

class ExposureProducer:
    def __init__(self, bootstrap_servers):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    
    async def send_exposure(self, exposure_data: Dict[str, Any]):
        """Send exposure event to Kafka topic"""
        try:
            future = self.producer.send(
                'exposure-events',
                value=exposure_data
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            return {
                "status": "success",
                "topic": record_metadata.topic,
                "partition": record_metadata.partition,
                "offset": record_metadata.offset
            }
            
        except Exception as e:
            logger.error(f"Kafka send failed: {e}")
            raise
```

## 🔄 Data Flow Architecture

### Current Flow (POC)
```
SDK → Exposure API → Redshift
                      ↓
              GrowthBook Analytics
```

### Future Flow (Production)
```
SDK → Exposure API → Kafka → Consumer → Redshift
                                          ↓
                               GrowthBook Analytics
```

### Benefits of Kafka Integration

**🚀 Performance:**
- **Non-blocking**: API responses don't wait for database writes
- **High Throughput**: Handle thousands of exposure events per second
- **Resilience**: Kafka handles temporary database outages

**📊 Scalability:**
- **Horizontal Scaling**: Add more consumer instances
- **Batch Processing**: Efficient bulk inserts to Redshift
- **Buffer Capacity**: Handle traffic spikes gracefully

**🔧 Reliability:**
- **Durability**: Events persisted in Kafka until processed
- **Retry Logic**: Failed writes can be retried
- **Monitoring**: Kafka metrics for data pipeline health

## 🛠️ Deployment Strategy

### Phase 1: ECS Migration (Current POC → Production)

#### ECS Task Definitions
```json
{
  "family": "growthbook-task",
  "taskRoleArn": "arn:aws:iam::account:role/growthbook-task-role",
  "executionRoleArn": "arn:aws:iam::account:role/growthbook-execution-role",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "growthbook",
      "image": "your-account.dkr.ecr.region.amazonaws.com/growthbook:latest",
      "memory": 2048,
      "cpu": 1024,
      "environment": [
        {
          "name": "MONGODB_URI",
          "value": "mongodb://documentdb-cluster.cluster-xxx.docdb.amazonaws.com:27017/growthbook"
        }
      ],
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ]
    },
    {
      "name": "exposure-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/exposure-api:latest",
      "memory": 1024,
      "cpu": 512,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ]
    }
  ]
}
```

#### ECS Service Configuration
```yaml
service:
  name: growthbook-service
  cluster: growthbook-cluster
  taskDefinition: growthbook-task
  desiredCount: 2
  launchType: FARGATE
  networkConfiguration:
    awsvpcConfiguration:
      securityGroups:
        - sg-growthbook-service
      subnets:
        - subnet-private-1a
        - subnet-private-1b
  loadBalancers:
    - targetGroupArn: arn:aws:elasticloadbalancing:region:account:targetgroup/growthbook/xxx
      containerName: growthbook
      containerPort: 3000
```

### Phase 2: Kafka Integration

#### Kafka Consumer Deployment Strategy

The Kafka consumer will be deployed as a **separate ECS service** to ensure scalability and isolation:

**🏗️ Deployment Architecture:**
- **Separate ECS Task Definition**: Independent from GrowthBook main application
- **Dedicated ECS Service**: Can scale independently based on Kafka lag
- **Same ECS Cluster**: Shares networking and security configurations
- **Auto-scaling**: Scales based on Kafka consumer lag metrics

**📦 Container Configuration:**
```yaml
kafka-consumer-task:
  family: growthbook-kafka-consumer
  containers:
    - name: exposure-consumer
      image: your-account.dkr.ecr.region.amazonaws.com/exposure-consumer:latest
      memory: 1024
      cpu: 512
      environment:
        - KAFKA_BROKERS: $MSK_BOOTSTRAP_SERVERS
        - REDSHIFT_HOST: $REDSHIFT_ENDPOINT
        - BATCH_SIZE: 1000
        - CONSUMER_GROUP: exposure-consumer-group
```

**⚙️ ECS Service Configuration:**
```yaml
consumer-service:
  name: growthbook-consumer-service
  cluster: growthbook-cluster
  taskDefinition: kafka-consumer-task
  desiredCount: 2  # Start with 2 instances
  launchType: FARGATE
  networkConfiguration:
    securityGroups: [sg-kafka-consumer]
    subnets: [subnet-private-1a, subnet-private-1b]
```

**📊 Auto-scaling Configuration:**
```yaml
auto-scaling:
  target: ECS Service
  metric: Kafka Consumer Lag
  thresholds:
    - lag > 5000 messages → Scale up
    - lag < 1000 messages → Scale down
  min_capacity: 1
  max_capacity: 10
```

#### MSK (Managed Streaming for Kafka) Setup
```yaml
kafka:
  cluster_name: growthbook-kafka
  kafka_version: 2.8.0
  broker_node_group:
    instance_type: kafka.m5.large
    client_subnets:
      - subnet-private-1a
      - subnet-private-1b
      - subnet-private-1c
    storage_info:
      ebs_volume_size: 100
  encryption:
    encryption_in_transit:
      client_broker: TLS
      in_cluster: true
```

#### Complete Kafka Consumer Implementation

**📁 Project Structure:**
```
consumer/
├── Dockerfile
├── requirements.txt
├── main.py
├── consumer.py
├── redshift_client.py
└── config.py
```

**🐳 Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run the consumer
CMD ["python", "main.py"]
```

**📦 Requirements.txt:**
```txt
kafka-python==2.0.2
psycopg2-binary==2.9.5
boto3==1.26.137
python-json-logger==2.0.7
prometheus-client==0.16.0
fastapi==0.95.2
uvicorn==0.22.0
requests==2.31.0
```

**⚙️ Configuration (config.py):**
```python
import os
from typing import List

class Config:
    # Kafka Configuration
    KAFKA_BROKERS: List[str] = os.getenv('KAFKA_BROKERS', 'localhost:9092').split(',')
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC', 'exposure-events')
    CONSUMER_GROUP: str = os.getenv('CONSUMER_GROUP', 'exposure-consumer-group')
    
    # Redshift Configuration
    REDSHIFT_HOST: str = os.getenv('REDSHIFT_HOST')
    REDSHIFT_PORT: int = int(os.getenv('REDSHIFT_PORT', '5439'))
    REDSHIFT_DB: str = os.getenv('REDSHIFT_DB', 'analytics')
    REDSHIFT_USER: str = os.getenv('REDSHIFT_USER')
    REDSHIFT_PASSWORD: str = os.getenv('REDSHIFT_PASSWORD')
    REDSHIFT_SCHEMA: str = os.getenv('REDSHIFT_SCHEMA', 'growthbook')
    
    # Processing Configuration
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '1000'))
    BATCH_TIMEOUT: int = int(os.getenv('BATCH_TIMEOUT', '30'))  # seconds
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    
    # Monitoring
    METRICS_PORT: int = int(os.getenv('METRICS_PORT', '8080'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
```

**🔧 Redshift Client (redshift_client.py):**
```python
import psycopg2
import psycopg2.extras
import json
import logging
from typing import List, Dict, Optional
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)

class RedshiftClient:
    def __init__(self, config: Config):
        self.config = config
        self.connection_params = {
            'host': config.REDSHIFT_HOST,
            'port': config.REDSHIFT_PORT,
            'database': config.REDSHIFT_DB,
            'user': config.REDSHIFT_USER,
            'password': config.REDSHIFT_PASSWORD,
        }
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            conn.set_session(autocommit=False)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def create_table_if_not_exists(self):
        """Ensure the exposures table exists with proper schema"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.config.REDSHIFT_SCHEMA}.experiment_exposures (
            id BIGINT IDENTITY(1,1) PRIMARY KEY,
            ds_user_id VARCHAR(255) NOT NULL,
            experiment_id VARCHAR(255) NOT NULL,
            variation_id VARCHAR(255) NOT NULL,
            attributes TEXT,
            source VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP DEFAULT GETDATE(),
            created_at TIMESTAMP DEFAULT GETDATE()
        );
        
        -- Create indexes for better query performance
        CREATE INDEX IF NOT EXISTS idx_exposures_user_id 
            ON {self.config.REDSHIFT_SCHEMA}.experiment_exposures(ds_user_id);
        CREATE INDEX IF NOT EXISTS idx_exposures_experiment_id 
            ON {self.config.REDSHIFT_SCHEMA}.experiment_exposures(experiment_id);
        CREATE INDEX IF NOT EXISTS idx_exposures_timestamp 
            ON {self.config.REDSHIFT_SCHEMA}.experiment_exposures(timestamp);
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Ensured exposures table exists")
    
    def batch_insert_exposures(self, exposures: List[Dict]) -> bool:
        """
        Efficiently batch insert exposures using COPY command for better performance
        """
        if not exposures:
            return True
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare data for bulk insert
                values = []
                for exp in exposures:
                    values.append((
                        exp.get("ds_user_id"),
                        exp.get("experiment_id"),
                        exp.get("variation_id"),
                        json.dumps(exp.get("attributes", {})),
                        exp.get("source", "sdk"),
                        exp.get("timestamp")
                    ))
                
                # Use executemany for batch insert
                insert_sql = f"""
                    INSERT INTO {self.config.REDSHIFT_SCHEMA}.experiment_exposures 
                    (ds_user_id, experiment_id, variation_id, attributes, source, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                psycopg2.extras.execute_batch(
                    cursor, 
                    insert_sql, 
                    values, 
                    page_size=1000
                )
                
                conn.commit()
                logger.info(f"Successfully inserted {len(exposures)} exposures")
                return True
                
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return False
    
    def get_connection_health(self) -> bool:
        """Check if Redshift connection is healthy"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
```

**🎯 Main Consumer Logic (consumer.py):**
```python
import json
import logging
import time
import threading
from kafka import KafkaConsumer, TopicPartition
from typing import List, Dict, Optional
from datetime import datetime, timezone
from collections import defaultdict
from redshift_client import RedshiftClient
from config import Config

logger = logging.getLogger(__name__)

class ExposureConsumer:
    def __init__(self, config: Config):
        self.config = config
        self.redshift_client = RedshiftClient(config)
        self.consumer = None
        self.running = False
        self.metrics = {
            'messages_processed': 0,
            'messages_failed': 0,
            'batches_processed': 0,
            'last_processed_time': None
        }
        
    def setup_consumer(self):
        """Initialize Kafka consumer with proper configuration"""
        consumer_config = {
            'bootstrap_servers': self.config.KAFKA_BROKERS,
            'group_id': self.config.CONSUMER_GROUP,
            'value_deserializer': lambda m: json.loads(m.decode('utf-8')) if m else None,
            'key_deserializer': lambda m: m.decode('utf-8') if m else None,
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
            'auto_commit_interval_ms': 5000,
            'max_poll_records': self.config.BATCH_SIZE,
            'max_poll_interval_ms': 300000,  # 5 minutes
            'session_timeout_ms': 30000,
            'heartbeat_interval_ms': 10000,
            'fetch_min_bytes': 1,
            'fetch_max_wait_ms': 500
        }
        
        self.consumer = KafkaConsumer(
            self.config.KAFKA_TOPIC,
            **consumer_config
        )
        
        logger.info(f"Kafka consumer initialized for topic: {self.config.KAFKA_TOPIC}")
        logger.info(f"Consumer group: {self.config.CONSUMER_GROUP}")
        
    def start_consuming(self):
        """Main consumer loop with batch processing and error handling"""
        self.running = True
        batch = []
        last_batch_time = time.time()
        
        logger.info("Starting exposure consumer...")
        
        # Ensure table exists
        self.redshift_client.create_table_if_not_exists()
        
        try:
            while self.running:
                try:
                    # Poll for messages with timeout
                    message_batch = self.consumer.poll(timeout_ms=1000)
                    
                    if not message_batch and not batch:
                        continue
                    
                    # Process messages from all partitions
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            if self.validate_message(message.value):
                                batch.append(self.enrich_message(message.value))
                            else:
                                logger.warning(f"Invalid message format: {message.value}")
                                self.metrics['messages_failed'] += 1
                    
                    # Process batch if size or timeout reached
                    current_time = time.time()
                    should_process = (
                        len(batch) >= self.config.BATCH_SIZE or 
                        (batch and current_time - last_batch_time >= self.config.BATCH_TIMEOUT)
                    )
                    
                    if should_process:
                        if self.process_batch(batch):
                            self.metrics['batches_processed'] += 1
                            self.metrics['messages_processed'] += len(batch)
                            logger.info(f"Processed batch of {len(batch)} exposures")
                        else:
                            self.metrics['messages_failed'] += len(batch)
                            logger.error(f"Failed to process batch of {len(batch)} exposures")
                        
                        batch = []
                        last_batch_time = current_time
                        self.metrics['last_processed_time'] = datetime.now(timezone.utc)
                
                except Exception as e:
                    logger.error(f"Error in consumer loop: {e}")
                    time.sleep(5)  # Back off on errors
                    
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            # Process any remaining messages in batch
            if batch:
                self.process_batch(batch)
            self.cleanup()
    
    def validate_message(self, message: Dict) -> bool:
        """Validate message structure before processing"""
        required_fields = ['ds_user_id', 'experiment_id', 'variation_id']
        return all(field in message and message[field] for field in required_fields)
    
    def enrich_message(self, message: Dict) -> Dict:
        """Add processing metadata to message"""
        if 'timestamp' not in message or not message['timestamp']:
            message['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Ensure source is set
        if 'source' not in message:
            message['source'] = 'sdk'
            
        return message
    
    def process_batch(self, batch: List[Dict]) -> bool:
        """Process a batch of exposure events with retry logic"""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if self.redshift_client.batch_insert_exposures(batch):
                    return True
                    
            except Exception as e:
                logger.error(f"Batch processing attempt {attempt + 1} failed: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        logger.error(f"Failed to process batch after {self.config.MAX_RETRIES} attempts")
        return False
    
    def get_metrics(self) -> Dict:
        """Return consumer metrics for monitoring"""
        return {
            **self.metrics,
            'consumer_group': self.config.CONSUMER_GROUP,
            'topic': self.config.KAFKA_TOPIC,
            'batch_size': self.config.BATCH_SIZE,
            'redshift_healthy': self.redshift_client.get_connection_health()
        }
    
    def stop_consuming(self):
        """Gracefully stop the consumer"""
        logger.info("Stopping exposure consumer...")
        self.running = False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.consumer:
            self.consumer.close()
        logger.info("Consumer cleanup completed")
```

**🚀 Application Entry Point (main.py):**
```python
import logging
import signal
import sys
import threading
from fastapi import FastAPI
from uvicorn import run
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from consumer import ExposureConsumer
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
MESSAGES_PROCESSED = Counter('kafka_messages_processed_total', 'Total processed messages')
BATCHES_PROCESSED = Counter('kafka_batches_processed_total', 'Total processed batches')
PROCESSING_TIME = Histogram('batch_processing_seconds', 'Time spent processing batches')

class ConsumerApp:
    def __init__(self):
        self.config = Config()
        self.consumer = ExposureConsumer(self.config)
        self.app = FastAPI(title="GrowthBook Exposure Consumer")
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for ECS health checks"""
            return {
                "status": "healthy",
                "consumer_running": self.consumer.running,
                "redshift_connection": self.consumer.redshift_client.get_connection_health()
            }
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            consumer_metrics = self.consumer.get_metrics()
            
            # Update Prometheus counters
            MESSAGES_PROCESSED._value._value = consumer_metrics['messages_processed']
            BATCHES_PROCESSED._value._value = consumer_metrics['batches_processed']
            
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        
        @self.app.get("/status")
        async def status():
            """Detailed status endpoint"""
            return self.consumer.get_metrics()
    
    def start_consumer_thread(self):
        """Start consumer in separate thread"""
        def run_consumer():
            try:
                self.consumer.setup_consumer()
                self.consumer.start_consuming()
            except Exception as e:
                logger.error(f"Consumer thread failed: {e}")
                
        consumer_thread = threading.Thread(target=run_consumer, daemon=True)
        consumer_thread.start()
        return consumer_thread
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.consumer.stop_consuming()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

def main():
    app_instance = ConsumerApp()
    
    # Setup signal handlers for graceful shutdown
    app_instance.setup_signal_handlers()
    
    # Start consumer in background thread
    consumer_thread = app_instance.start_consumer_thread()
    
    # Start health check/metrics server
    logger.info(f"Starting health check server on port {app_instance.config.METRICS_PORT}")
    run(
        app_instance.app,
        host="0.0.0.0",
        port=app_instance.config.METRICS_PORT,
        log_level="info"
    )

if __name__ == "__main__":
    main()
```

**📊 ECS Task Definition for Consumer:**
```json
{
  "family": "growthbook-kafka-consumer",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/growthbook-consumer-role",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/growthbook-execution-role",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "exposure-consumer",
      "image": "ACCOUNT.dkr.ecr.REGION.amazonaws.com/growthbook-consumer:latest",
      "essential": true,
      "environment": [
        {"name": "KAFKA_BROKERS", "value": "kafka-broker-1:9092,kafka-broker-2:9092"},
        {"name": "KAFKA_TOPIC", "value": "exposure-events"},
        {"name": "CONSUMER_GROUP", "value": "exposure-consumer-group"},
        {"name": "REDSHIFT_HOST", "value": "redshift-cluster.amazonaws.com"},
        {"name": "REDSHIFT_DB", "value": "analytics"},
        {"name": "REDSHIFT_USER", "value": "growthbook_user"},
        {"name": "BATCH_SIZE", "value": "1000"},
        {"name": "BATCH_TIMEOUT", "value": "30"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {"name": "REDSHIFT_PASSWORD", "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT:secret:redshift-password"}
      ],
      "portMappings": [
        {"containerPort": 8080, "protocol": "tcp"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/growthbook-consumer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 🔐 Security & Compliance

### Network Security
```yaml
Security Groups:
  growthbook-alb-sg:
    ingress:
      - port: 443
        protocol: tcp
        cidr: 0.0.0.0/0  # Public access via HTTPS
        
  growthbook-service-sg:
    ingress:
      - port: 3000
        protocol: tcp
        source_security_group: growthbook-alb-sg
      - port: 8000
        protocol: tcp
        source_security_group: growthbook-alb-sg
        
  documentdb-sg:
    ingress:
      - port: 27017
        protocol: tcp
        source_security_group: growthbook-service-sg
        
  redshift-sg:
    ingress:
      - port: 5439
        protocol: tcp
        source_security_group: growthbook-service-sg
```

### IAM Roles & Policies
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kafka:DescribeCluster",
        "kafka:GetBootstrapBrokers",
        "kafka-cluster:Connect"
      ],
      "Resource": "arn:aws:kafka:region:account:cluster/growthbook-kafka/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBClusters",
        "rds-db:connect"
      ],
      "Resource": "arn:aws:rds-db:region:account:dbuser:redshift-cluster/*"
    },
    {
      "Effect": "Allow", 
      "Action": [
        "docdb:ListCollections",
        "docdb:ReadPreference"
      ],
      "Resource": "arn:aws:rds:region:account:cluster:documentdb-cluster/*"
    }
  ]
}
```


## 🎯 Kafka Consumer Deployment Details

### Why Separate ECS Service?

**Benefits of Dedicated Consumer Service:**
- **Independent Scaling**: Consumer can scale based on Kafka lag without affecting main app
- **Isolation**: Issues in consumer don't impact GrowthBook UI/API
- **Resource Optimization**: Different CPU/memory requirements than web application
- **Deployment Independence**: Can deploy consumer updates without touching main service

### Consumer Service Architecture
```
ECS Cluster: growthbook-cluster
├─ Service: growthbook-service (Main application)
│  ├─ Task: GrowthBook Web UI + API
│  └─ Task: Exposure API (Kafka Producer)
└─ Service: growthbook-consumer-service (Consumer)
   ├─ Task: Kafka Consumer #1
   └─ Task: Kafka Consumer #2 (auto-scaled)
```

### Resource Requirements
```yaml
Consumer Service Sizing:
  Initial: 1 vCPU, 2GB RAM × 2 tasks
  Max Scale: 1 vCPU, 2GB RAM × 10 tasks
  
Network:
  - Same VPC as main services
  - Access to MSK cluster
  - Access to Redshift cluster
  - No public internet required
```

### Consumer Group Strategy
```python
# Consumer configuration
CONSUMER_CONFIG = {
    'group_id': 'exposure-consumer-group',
    'auto_offset_reset': 'earliest',
    'enable_auto_commit': True,
    'max_poll_records': 1000,
    'session_timeout_ms': 30000
}

# Partition strategy: Multiple consumers can process different partitions
# Topic: exposure-events (3 partitions)
# Consumer instances: 2-3 (one per partition for optimal throughput)
```

## 💰 Cost Optimization

### Resource Sizing Estimates
```yaml
Production Monthly Costs:
  ECS Fargate:
    - GrowthBook Service: 2 vCPU, 4GB × 2 tasks = ~$120
    - Exposure API: 1 vCPU, 2GB × 2 tasks = ~$60  
    - Kafka Consumer: 1 vCPU, 2GB × 2 tasks = ~$60
    
  MSK (Managed Kafka): 
    - kafka.m5.large × 3 brokers = ~$400
    
  DocumentDB:
    - r6g.large × 2 instances = ~$300
    
  Supporting Services:
    - ALB, CloudWatch, Data Transfer = ~$100
    
Total Estimated: ~$1,040/month
```
```