#!/usr/bin/env python3

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import List, Dict
import psycopg2
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import boto3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GrowthBookConsumer:
    def __init__(self):
        # Kafka configuration
        self.kafka_config = {
            'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', '').split(','),
            'security_protocol': 'SSL',
            'group_id': os.getenv('KAFKA_CONSUMER_GROUP', 'growthbook-consumer'),
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False,  # Manual commit after successful DB write
            'value_deserializer': lambda v: json.loads(v.decode('utf-8')),
            'api_version': (2, 8, 1)
        }
        
        # Topics (auto-created when first used)
        self.exposure_topic = os.getenv('KAFKA_EXPOSURE_TOPIC', 'exposures')
        
        # Redshift configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', ''),
            'port': int(os.getenv('DB_PORT', 5439)),
            'database': os.getenv('DB_NAME', 'events'),
            'user': os.getenv('DB_USER', ''),
            'password': os.getenv('DB_PASSWORD', '')
        }
        
        # Processing configuration
        self.batch_size = int(os.getenv('BATCH_SIZE', 100))
        self.batch_timeout = int(os.getenv('BATCH_TIMEOUT_SECONDS', 30))
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        
        # Initialize components
        self.consumer = None
        self.retry_producer = None
        self.db_connection = None
        self.running = True
        
        # Batch processing
        self.message_batch = []
        self.last_batch_time = time.time()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)
        
    def shutdown_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def initialize_kafka(self):
        """Initialize Kafka consumer and retry producer"""
        try:
            self.consumer = KafkaConsumer(
                self.exposure_topic,
                **self.kafka_config
            )
            
            # Initialize retry producer (for re-queuing failed messages)
            producer_config = self.kafka_config.copy()
            del producer_config['group_id']
            del producer_config['auto_offset_reset']
            del producer_config['enable_auto_commit']
            del producer_config['value_deserializer']
            producer_config['value_serializer'] = lambda v: json.dumps(v).encode('utf-8')
            
            self.retry_producer = KafkaProducer(**producer_config)
            
            logger.info(f"✅ Kafka consumer initialized for topic: {self.exposure_topic}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka: {e}")
            raise
            
    def get_db_connection(self):
        """Get database connection with connection pooling logic"""
        if self.db_connection is None or self.db_connection.closed:
            try:
                self.db_connection = psycopg2.connect(**self.db_config)
                self.db_connection.autocommit = False
                logger.info("✅ Database connection established")
            except Exception as e:
                logger.error(f"❌ Failed to connect to database: {e}")
                raise
        return self.db_connection
        
    def create_table_if_not_exists(self):
        """Ensure the exposures table exists"""
        create_table_sql = """
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
        """
        
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                conn.commit()
                logger.info("✅ Ensured experiment_exposures table exists")
        except Exception as e:
            logger.error(f"❌ Failed to create table: {e}")
            raise
            
    def batch_insert_exposures(self, exposures: List[Dict]) -> bool:
        """Batch insert exposures to Redshift"""
        if not exposures:
            return True
            
        try:
            conn = self.get_db_connection()
            
            # Prepare batch insert SQL (Redshift compatible)
            sql = """
            INSERT INTO growthbook.experiment_exposures 
            (exposure_id, ds_user_id, experiment_id, variation_id, ts, attributes, source)
            VALUES %s
            """
            
            # Prepare values
            values = []
            for exp in exposures:
                attributes_json = json.dumps(exp.get('attributes')) if exp.get('attributes') else None
                values.append((
                    exp['exposure_id'],
                    exp['ds_user_id'],
                    exp['experiment_id'],
                    exp['variation_id'],
                    exp['ts'],
                    attributes_json,
                    exp.get('source', 'python_sdk')
                ))
            
            # Execute batch insert using psycopg2 extras
            from psycopg2.extras import execute_values
            with conn.cursor() as cur:
                execute_values(cur, sql, values, template=None, page_size=100)
                conn.commit()
                
            logger.info(f"✅ Successfully inserted {len(exposures)} exposures to Redshift")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to batch insert exposures: {e}")
            if conn:
                conn.rollback()
            return False
            
    def retry_messages_to_topic(self, messages: List[Dict], error_reason: str):
        """Re-publish failed messages back to same topic with retry metadata"""
        try:
            for message in messages:
                retry_count = message.get('retry_count', 0) + 1
                
                # Add retry metadata
                retry_message = {
                    **message,  # Original message data
                    'retry_count': retry_count,
                    'last_error': error_reason,
                    'last_failed_at': datetime.now().isoformat(),
                    'retry_delay_applied': True
                }
                
                # Only retry if under max retry limit
                if retry_count <= 3:
                    self.retry_producer.send(self.exposure_topic, value=retry_message)
                    logger.info(f"🔄 Retry {retry_count}/3: Re-queued exposure {message.get('exposure_id')} to {self.exposure_topic}")
                else:
                    # Final failure - log permanently
                    logger.error(f"💀 PERMANENT FAILURE: exposure {message.get('exposure_id')} failed {retry_count} times")
                    logger.error(f"💀 Final error: {error_reason}")
                    # Could write to a separate failure log file here
                
            self.retry_producer.flush()
            logger.warning(f"🔄 Re-queued {len([m for m in messages if m.get('retry_count', 0) < 3])} messages for retry")
            
        except Exception as e:
            logger.error(f"❌ Failed to retry messages: {e}")
            
    def process_batch(self, messages: List[Dict]) -> bool:
        """Process a batch of messages with retry logic"""
        for attempt in range(self.max_retries):
            try:
                success = self.batch_insert_exposures(messages)
                if success:
                    return True
                    
            except Exception as e:
                logger.warning(f"⚠️ Batch processing attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        # If all retries failed, re-queue to same topic with retry metadata
        self.retry_messages_to_topic(messages, f"Failed after {self.max_retries} retry attempts")
        return False
        
    def should_process_batch(self) -> bool:
        """Check if we should process the current batch"""
        batch_full = len(self.message_batch) >= self.batch_size
        batch_timeout = (time.time() - self.last_batch_time) >= self.batch_timeout
        return batch_full or (self.message_batch and batch_timeout)
        
    def process_messages(self):
        """Main message processing loop"""
        logger.info("🚀 Starting message processing...")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    # Parse message
                    exposure_data = message.value
                    self.message_batch.append(exposure_data)
                    
                    # Process batch if conditions are met
                    if self.should_process_batch():
                        success = self.process_batch(self.message_batch.copy())
                        
                        if success:
                            # Commit Kafka offsets only after successful DB write
                            self.consumer.commit()
                            logger.info(f"✅ Processed batch of {len(self.message_batch)} exposures")
                        else:
                            logger.error(f"❌ Failed to process batch of {len(self.message_batch)} exposures")
                            # Failed messages re-queued to same topic with new offsets
                            # Safe to commit offsets now
                            self.consumer.commit()
                            logger.info("✅ Committed offsets - failed messages re-queued for retry")
                            
                        # Reset batch
                        self.message_batch.clear()
                        self.last_batch_time = time.time()
                        
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    # Send problematic message to DLQ
                    self.send_to_dlq([message.value], str(e))
                    
            # Process any remaining messages in batch
            if self.message_batch:
                self.process_batch(self.message_batch)
                self.consumer.commit()
                
        except Exception as e:
            logger.error(f"❌ Fatal error in message processing: {e}")
            raise
            
    def run(self):
        """Main entry point"""
        logger.info("🏁 Starting GrowthBook Consumer...")
        
        try:
            # Initialize components
            self.initialize_kafka()
            self.create_table_if_not_exists()
            
            # Start processing
            self.process_messages()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Interrupted by user")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            return 1
        finally:
            self.cleanup()
            
        logger.info("👋 GrowthBook Consumer stopped")
        return 0
        
    def cleanup(self):
        """Cleanup resources"""
        if self.consumer:
            self.consumer.close()
            
        if self.retry_producer:
            self.retry_producer.close()
            
        if self.db_connection:
            self.db_connection.close()

if __name__ == "__main__":
    consumer = GrowthBookConsumer()
    exit_code = consumer.run()
    sys.exit(exit_code)