from fastapi import Request, Response, FastAPI
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("x-signature")
    
    # Verify signature here...
    print(f"Received webhook payload size: {len(payload)}")
    
    return Response(content="Webhook received", status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
