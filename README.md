# GrowthBook Kafka Architecture

This repository contains a complete GrowthBook deployment with Kafka-based exposure tracking system.

## Architecture Overview

```
Client Apps → Exposure API → Kafka (MSK) → Consumer → Redshift
                ↑                                        ↓
         GrowthBook Dashboard ← DocumentDB        Analytics Data
```

### Components

1. **GrowthBook Dashboard**: Web UI that connects to DocumentDB for configuration and reads from Redshift for analytics
2. **Exposure API**: FastAPI service that receives exposure events from client applications and produces to Kafka
3. **Consumer**: Python service that consumes from Kafka and writes exposure data to Redshift
4. **Kafka (MSK)**: Event streaming platform for reliable message delivery
5. **DocumentDB**: MongoDB-compatible database for GrowthBook configuration
6. **Redshift**: Data warehouse for storing exposure analytics

## Prerequisites

1. AWS MSK Cluster running Kafka 3.8.x
2. AWS DocumentDB cluster
3. AWS Redshift cluster
4. Docker and Docker Compose

## Setup Instructions

### 1. Create Redshift Schema and Table

First, connect to your Redshift cluster and create the required schema and table:

```sql
-- Create the growthbook schema
CREATE SCHEMA IF NOT EXISTS growthbook;

-- Create the experiment_exposures table
CREATE TABLE IF NOT EXISTS growthbook.experiment_exposures (
    exposure_id VARCHAR(64) PRIMARY KEY,
    ds_user_id VARCHAR(128) NOT NULL,
    experiment_id VARCHAR(128) NOT NULL,
    variation_id VARCHAR(64) NOT NULL,
    ts TIMESTAMP NOT NULL,
    attributes SUPER,
    source VARCHAR(32) DEFAULT 'python_sdk',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Configure Environment Variables

Create a `.env` file with your AWS credentials and endpoints:

```env
# DocumentDB (MongoDB-compatible)
MONGODB_URI=mongodb://username:password@your-docdb-endpoint:27017/growthbook?ssl=true&retryWrites=false&authSource=admin

# GrowthBook Configuration
JWT_SECRET=your-super-secure-jwt-secret-key-that-should-be-at-least-32-characters-long-for-security
ENCRYPTION_KEY=your-super-secure-encryption-key-that-should-be-at-least-32-characters-long-for-security

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# Redshift Data Warehouse
DB_HOST=your-redshift-cluster-endpoint
DB_USER=your-redshift-username
DB_PASSWORD=your-redshift-password

# Kafka (MSK) Configuration
KAFKA_BOOTSTRAP_SERVERS=broker1:9094,broker2:9094,broker3:9094
```

### 3. Deploy Services

Deploy all services using Docker Compose:

```bash
# Start all services
docker-compose -f docker-compose.docdb.yml up -d

# Check service status
docker-compose -f docker-compose.docdb.yml ps

# View logs
docker-compose -f docker-compose.docdb.yml logs -f
```

### 4. Verify Deployment

1. **GrowthBook Dashboard**: Access at `http://localhost:80`
2. **Exposure API Health**: `curl http://localhost:80/exposure/health`
3. **Test Exposure Logging**:
   ```bash
   curl -X POST http://localhost:80/exposure \
   -H "Content-Type: application/json" \
   -d '{
     "ds_user_id": "user123",
     "experiment_id": "test-experiment",
     "variation_id": "control",
     "attributes": {"browser": "chrome"},
     "source": "web_app"
   }'
   ```

## Service Details

### Exposure API (Port 8000)

FastAPI service that receives exposure events from client applications.

**Endpoints:**
- `POST /exposure` - Log an exposure event
- `GET /health` - Health check
- `GET /exposures/{user_id}` - Get exposures for a user
- `GET /exposures/experiment/{experiment_key}` - Get exposures for an experiment

**Usage from Client Applications:**
```python
import requests

# Log exposure
response = requests.post("http://your-domain.com/exposure", json={
    "ds_user_id": "user123",
    "experiment_id": "checkout-flow-v2",
    "variation_id": "treatment",
    "attributes": {
        "platform": "mobile",
        "version": "1.2.3"
    },
    "source": "mobile_app"
})
```

### Consumer Service

Python service that:
- Consumes messages from Kafka `exposures` topic
- Batches messages for efficient processing
- Writes exposure data to Redshift
- Implements retry logic with exponential backoff
- Re-queues failed messages to the same topic with retry metadata

**Configuration:**
- `BATCH_SIZE`: Number of messages to batch (default: 100)
- `BATCH_TIMEOUT_SECONDS`: Maximum time to wait for batch (default: 30)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)

### GrowthBook Dashboard

Pre-built Docker image that connects to:
- **DocumentDB**: For storing experiments, features, and configurations
- **Redshift**: For reading exposure analytics data from `growthbook.experiment_exposures`

## Data Flow

1. **Client Application** sends exposure events to Exposure API
2. **Exposure API** validates and produces messages to Kafka
3. **Kafka** reliably stores and delivers messages
4. **Consumer** processes messages in batches and writes to Redshift
5. **GrowthBook Dashboard** reads exposure data for experiment analysis

## Error Handling

The system implements robust error handling:

- **API Level**: Returns immediate response while processing in background
- **Kafka Level**: Configurable retries and timeouts
- **Consumer Level**: Batch processing with retry logic
- **Database Level**: Transaction rollback on failures
- **Retry Mechanism**: Failed messages are re-queued with retry metadata

## Monitoring

Monitor the system using:

```bash
# View service logs
docker-compose -f docker-compose.docdb.yml logs -f exposure-api
docker-compose -f docker-compose.docdb.yml logs -f growthbook-consumer

# Check Kafka consumer group status
# (requires Kafka tools)
kafka-consumer-groups.sh --bootstrap-server $KAFKA_BOOTSTRAP_SERVERS --group growthbook-consumer --describe
```

## Scaling

- **Exposure API**: Scale horizontally by adding more containers
- **Consumer**: Scale by increasing partitions and consumer instances
- **Kafka**: Increase partition count for higher throughput
- **Redshift**: Use appropriate node types for your data volume

## Security

- All Kafka connections use SSL encryption
- Database connections are encrypted
- Secrets are managed via environment variables
- No credentials are committed to the repository

## Client Integration

Client applications should integrate with the Exposure API to track experiment exposures:

```javascript
// JavaScript example
fetch('/exposure', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ds_user_id: userId,
    experiment_id: experimentId,
    variation_id: variationId,
    attributes: userAttributes,
    source: 'web_app'
  })
});
```

This architecture ensures reliable, scalable exposure tracking while keeping the GrowthBook dashboard responsive and the data pipeline fault-tolerant.