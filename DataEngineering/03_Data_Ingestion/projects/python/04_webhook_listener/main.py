import os
import json
import uuid
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
import uvicorn
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="Webhook Listener API")

S3_BUCKET = os.getenv("S3_BUCKET", "my-webhook-payloads")
s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION", "us-east-1"))

@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Endpoint to receive webhook payloads and upload them directly to AWS S3.
    """
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Generate a unique object key based on timestamp and uuid
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    file_id = str(uuid.uuid4())
    object_key = f"webhooks/{timestamp}_{file_id}.json"
    
    try:
        # Upload the payload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=object_key,
            Body=json.dumps(payload),
            ContentType="application/json"
        )
        logging.info(f"Successfully uploaded payload to s3://{S3_BUCKET}/{object_key}")
    except (BotoCoreError, ClientError) as e:
        logging.error(f"Failed to upload to S3: {e}")
        # In a real scenario, you might write to a local fallback or Kafka dead-letter queue
        raise HTTPException(status_code=500, detail="Failed to persist webhook payload")

    return {"status": "success", "key": object_key}

def main():
    logging.info('Starting Data Engineering Project: 04_webhook_listener (FastAPI + Boto3)')
    port = int(os.getenv("PORT", 8080))
    # Uvicorn is a standard ASGI server for FastAPI
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == '__main__':
    main()
