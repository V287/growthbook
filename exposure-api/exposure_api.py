#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import psycopg2
import json
from datetime import datetime
import uuid
import os
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GrowthBook Async Exposure API", version="2.0.0")

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'event-warehouse.c42h0lx7fues.ap-southeast-1.redshift.amazonaws.com'),
    'port': int(os.getenv('DB_PORT', 5439)),
    'database': os.getenv('DB_NAME', 'events'),
    'user': os.getenv('DB_USER', 'datascience'),
    'password': os.getenv('DB_PASSWORD', 'eyEnaG26eoTQahEsj6d66KafkDxs4TRv')
}

# Pydantic model for exposure data
class ExposureData(BaseModel):
    ds_user_id: str
    experiment_id: str
    variation_id: str
    attributes: Optional[Dict[str, Any]] = None
    source: str = "python_sdk"

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def create_exposure_table():
    """Create the experiment_exposures table if it doesn't exist"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS growthbook.experiment_exposures (
        exposure_id VARCHAR(64) PRIMARY KEY,
        ds_user_id VARCHAR(128) NOT NULL,
        experiment_id VARCHAR(128) NOT NULL,
        variation_id VARCHAR(64) NOT NULL,
        ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        attributes SUPER,
        source VARCHAR(32) DEFAULT 'python_sdk'
    );
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                conn.commit()
                print("✅ Experiment exposures table ready")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize database table on startup"""
    create_exposure_table()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "GrowthBook Async Exposure API", "status": "healthy", "mode": "async_background_tasks"}

@app.get("/health")
async def health_check():
    """Database health check"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def write_exposure_to_db(exposure_data: dict, exposure_id: str):
    """Background task to write exposure to database"""
    try:
        # Prepare the SQL insert
        sql = """
        INSERT INTO growthbook.experiment_exposures 
        (exposure_id, ds_user_id, experiment_id, variation_id, ts, attributes, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        # Convert attributes to JSON string
        attributes_json = json.dumps(exposure_data.get('attributes')) if exposure_data.get('attributes') else None
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    exposure_id,
                    exposure_data['ds_user_id'],
                    exposure_data['experiment_id'],
                    exposure_data['variation_id'],
                    datetime.now(),
                    attributes_json,
                    exposure_data['source']
                ))
                conn.commit()
        
        logger.info(f"✅ Exposure {exposure_id} written to database for user {exposure_data['ds_user_id']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to write exposure {exposure_id} to database: {e}")

@app.post("/exposure")
async def log_exposure(exposure: ExposureData, background_tasks: BackgroundTasks):
    """Queue an exposure for background processing"""
    try:
        exposure_id = str(uuid.uuid4())
        
        # Add background task to write to database
        background_tasks.add_task(
            write_exposure_to_db, 
            exposure.dict(), 
            exposure_id
        )
        
        # Return immediate response
        return {
            "success": True,
            "exposure_id": exposure_id,
            "message": "Exposure job submitted successfully",
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to queue exposure job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue exposure job: {str(e)}")

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
