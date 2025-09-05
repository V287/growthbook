#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from datetime import datetime
import uuid
import os
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic model for exposure data
class ExposureData(BaseModel):
    ds_user_id: str
    experiment_id: str
    variation_id: str
    attributes: Optional[Dict[str, Any]] = None
    source: str = "python_sdk"

class KafkaExposureProducer:
    """Kafka producer for GrowthBook exposures"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', '')
        self.exposure_topic = os.getenv('KAFKA_EXPOSURE_TOPIC', 'exposures')
        self.producer = None
        
    def get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer with AWS MSK IAM authentication"""
        if self.producer is None:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    security_protocol='SSL',
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    retries=3,
                    retry_backoff_ms=100,
                    request_timeout_ms=30000,
                    api_version=(2, 8, 1)
                )
                logger.info("✅ Kafka producer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Kafka producer: {e}")
                raise
        return self.producer
    
    def produce_exposure(self, exposure_data: dict, exposure_id: str) -> None:
        """Produce exposure message to Kafka"""
        try:
            producer = self.get_producer()
            
            # Create the message
            message = {
                'exposure_id': exposure_id,
                'ds_user_id': exposure_data['ds_user_id'],
                'experiment_id': exposure_data['experiment_id'],
                'variation_id': exposure_data['variation_id'],
                'ts': datetime.now().isoformat(),
                'attributes': exposure_data.get('attributes'),
                'source': exposure_data['source']
            }
            
            # Produce to Kafka
            future = producer.send(self.exposure_topic, value=message)
            
            # Wait for the message to be sent (with timeout)
            record_metadata = future.get(timeout=10)
            
            logger.info(f"✅ Exposure {exposure_id} sent to Kafka topic {record_metadata.topic} partition {record_metadata.partition} offset {record_metadata.offset}")
            
        except KafkaError as e:
            logger.error(f"❌ Kafka error for exposure {exposure_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to produce exposure {exposure_id} to Kafka: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check Kafka producer health"""
        try:
            producer = self.get_producer()
            # Simple health check by checking if producer is initialized
            return producer is not None
        except Exception:
            return False
    
    def close(self):
        """Close the producer connection"""
        if self.producer:
            self.producer.close()

# Initialize the exposure producer
exposure_producer = KafkaExposureProducer()

# FastAPI app
app = FastAPI(title="GrowthBook Kafka Exposure Producer", version="3.0.0")

@app.on_event("startup")
async def startup_event():
    """Initialize Kafka producer on startup"""
    try:
        exposure_producer.get_producer()
        logger.info("🚀 GrowthBook Exposure Producer started")
    except Exception as e:
        logger.error(f"❌ Failed to start exposure producer: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    exposure_producer.close()
    logger.info("👋 GrowthBook Exposure Producer stopped")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "GrowthBook Async Exposure API", "status": "healthy", "mode": "async_background_tasks"}

@app.get("/health")
async def health_check():
    """Kafka producer health check"""
    try:
        kafka_healthy = exposure_producer.health_check()
        if kafka_healthy:
            return {"status": "healthy", "kafka": "connected"}
        else:
            raise HTTPException(status_code=500, detail="Kafka producer not healthy")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

def produce_exposure_to_kafka(exposure_data: dict, exposure_id: str):
    """Background task to produce exposure to Kafka"""
    exposure_producer.produce_exposure(exposure_data, exposure_id)

@app.post("/exposure")
async def log_exposure(exposure: ExposureData, background_tasks: BackgroundTasks):
    """Queue an exposure for Kafka processing"""
    try:
        exposure_id = str(uuid.uuid4())
        
        # Add background task to produce to Kafka
        background_tasks.add_task(
            produce_exposure_to_kafka, 
            exposure.dict(), 
            exposure_id
        )
        
        # Return immediate response
        return {
            "success": True,
            "exposure_id": exposure_id,
            "message": "Exposure queued for Kafka",
            "status": "queued",
            "topic": exposure_producer.exposure_topic
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to queue exposure for Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue exposure for Kafka: {str(e)}")

@app.get("/exposures/{user_id}")
async def get_user_exposures(user_id: str, limit: int = 100):
    """Get exposures for a specific user"""
    try:
        sql = """
        SELECT exposure_id, experiment_id, variation_id, ts, attributes, source
        FROM growthbook.experiment_exposures 
        WHERE ds_user_id = %s 
        ORDER BY ts DESC 
        LIMIT %s
        """
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit))
                rows = cur.fetchall()
                
                exposures = []
                for row in rows:
                    exposures.append({
                        "exposure_id": row[0],
                        "experiment_id": row[1],
                        "variation_id": row[2],
                        "ts": row[3].isoformat() if row[3] else None,
                        "attributes": row[4],
                        "source": row[5]
                    })
                
                return {
                    "user_id": user_id,
                    "exposures": exposures,
                    "count": len(exposures)
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exposures: {str(e)}")

@app.get("/exposures/experiment/{experiment_key}")
async def get_experiment_exposures(experiment_key: str, limit: int = 100):
    """Get all exposures for a specific experiment"""
    try:
        sql = """
        SELECT exposure_id, ds_user_id, experiment_id, variation_id, ts, attributes, source
        FROM growthbook.experiment_exposures 
        WHERE experiment_id = %s 
        ORDER BY ts DESC 
        LIMIT %s
        """
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (experiment_key, limit))
                rows = cur.fetchall()
                
                exposures = []
                for row in rows:
                    exposures.append({
                        "exposure_id": row[0],
                        "ds_user_id": row[1],
                        "experiment_id": row[2],
                        "variation_id": row[3],
                        "ts": row[4].isoformat() if row[4] else None,
                        "attributes": row[5],
                        "source": row[6]
                    })
                
                return {
                    "experiment_key": experiment_key,
                    "exposures": exposures,
                    "count": len(exposures)
                }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch experiment exposures: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
