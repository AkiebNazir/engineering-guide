# pip install fastapi uvicorn aiokafka
from fastapi import FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    print("Starting aiokafka producer/consumer...")

@app.post("/messages")
async def send_message(msg: str):
    return {"status": "Message queued"}
