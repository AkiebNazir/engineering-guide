import json
import logging
from kafka import KafkaConsumer
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "user_activity"
DB_CONNECTION_STRING = "postgresql://user:password@localhost:5432/analytics_db"

Base = declarative_base()

class UserActivity(Base):
    __tablename__ = 'user_activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True)
    activity_type = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

def get_db_session():
    engine = create_engine(DB_CONNECTION_STRING)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def consume_and_store():
    logger.info("Starting Kafka to DB Consumer...")
    
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='db_consumer_group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return

    session = get_db_session()
    
    logger.info(f"Listening for messages on '{KAFKA_TOPIC}'...")
    
    # Process messages in batches to optimize DB inserts
    batch_size = 100
    batch = []
    
    try:
        for message in consumer:
            data = message.value
            
            try:
                activity = UserActivity(
                    user_id=data.get('user_id'),
                    activity_type=data.get('activity_type'),
                    value=float(data.get('value', 0.0)),
                    timestamp=datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
                )
                batch.append(activity)
            except Exception as e:
                logger.error(f"Error parsing message data: {e}")
                continue
            
            # Commit batch when size is reached
            if len(batch) >= batch_size:
                try:
                    session.bulk_save_objects(batch)
                    session.commit()
                    logger.info(f"Committed {len(batch)} records to database.")
                    batch.clear()
                except Exception as e:
                    session.rollback()
                    logger.error(f"Database commit failed: {e}")
                    
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
    finally:
        # Commit remaining
        if batch:
            try:
                session.bulk_save_objects(batch)
                session.commit()
                logger.info(f"Committed final {len(batch)} records to database.")
            except Exception as e:
                logger.error(f"Final DB commit failed: {e}")
        
        consumer.close()
        session.close()

if __name__ == "__main__":
    consume_and_store()
