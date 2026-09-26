import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Real-Time Dashboard Backend")

# Configuration
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "dashboard_metrics"

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket connection established")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket connection closed")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")

manager = ConnectionManager()

def get_kafka_consumer():
    """Initialize and return a Kafka consumer."""
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id='dashboard-backend-group',
            value_deserializer=lambda x: x.decode('utf-8')
        )
        return consumer
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return None

async def consume_kafka_messages():
    """Background task to consume messages from Kafka and broadcast them to WS clients."""
    loop = asyncio.get_event_loop()
    consumer = await loop.run_in_executor(None, get_kafka_consumer)
    
    if not consumer:
        logger.warning("Kafka consumer not initialized. Skipping message consumption.")
        return

    logger.info("Started Kafka consumer background task")
    try:
        # We use a non-blocking loop pattern for demonstration
        for message in consumer:
            data = message.value
            logger.debug(f"Received message from Kafka: {data}")
            await manager.broadcast(data)
            # Yield control back to event loop
            await asyncio.sleep(0.01)
    except Exception as e:
        logger.error(f"Kafka consumption error: {e}")
    finally:
        consumer.close()

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    asyncio.create_task(consume_kafka_messages())

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for the real-time dashboard clients."""
    await manager.connect(websocket)
    try:
        while True:
            # We just wait for disconnects, communication is strictly server -> client
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
