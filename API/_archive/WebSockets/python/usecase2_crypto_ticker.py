import asyncio
import json
import random
from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.websocket("/ticker")
async def crypto_ticker(websocket: WebSocket):
    await websocket.accept()
    price = 50000.0
    try:
        while True:
            await asyncio.sleep(1)
            price += random.uniform(-50, 50)
            payload = json.dumps({"symbol": "BTC", "price": round(price, 2)})
            await websocket.send_text(payload)
    except Exception as e:
        print("Client disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
