# REAL-WORLD EXAMPLE: FastAPI (External 1)
# Demonstrates: Background Tasks (for order fulfillment without blocking the 200 OK response)
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import hmac
import hashlib
import json

app = FastAPI()
STRIPE_WEBHOOK_SECRET = b"whsec_my_super_secret"

def fulfill_order(session_id: str):
    # Simulate DB write and email sending
    print(f"Background Task: Fulfilling order for session {session_id}")

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    signature_header = request.headers.get("Stripe-Signature")

    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing signature")

    # In reality, Stripe's signature has timestamps, but this shows the HMAC concept
    expected_sig = hmac.new(STRIPE_WEBHOOK_SECRET, payload, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_sig, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = await request.json()
    
    if event.get("type") == "checkout.session.completed":
        session_id = event["data"]["object"]["id"]
        # Add to background tasks so we can return 200 OK immediately
        background_tasks.add_task(fulfill_order, session_id)
        
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
