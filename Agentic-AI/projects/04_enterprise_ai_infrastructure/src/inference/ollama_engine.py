import os
import logging
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# Configure production-grade logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise Local Inference API (Ollama + Langchain)")

# Environment configurations (ensure you have this model pulled in Ollama: `ollama run llama3`)
MODEL_NAME = os.getenv("MODEL_NAME", "llama3") 

# Initialize Langchain Ollama Wrapper
logger.info(f"Initializing Langchain Ollama connection with model: {MODEL_NAME}")
try:
    llm = ChatOllama(model=MODEL_NAME, temperature=0.7)
except Exception as e:
    logger.error(f"Failed to initialize Ollama. Is the Ollama app running? Error: {e}")
    raise

class ChatRequest(BaseModel):
    prompt: str
    temperature: float = 0.7

@app.post("/v1/chat/completions")
async def generate_response(request: ChatRequest):
    """
    OpenAI-compatible-like endpoint for local Ollama generation using Langchain.
    """
    try:
        request_id = str(uuid.uuid4())
        logger.info(f"Received request {request_id}. Prompt length: {len(request.prompt)}")
        
        # Override temperature for this specific request if supported
        llm.temperature = request.temperature
        
        messages = [HumanMessage(content=request.prompt)]
        
        # Invoke Langchain model
        response = llm.invoke(messages)
        
        logger.info(f"Request {request_id} completed successfully.")
        
        return {
            "id": request_id,
            "choices": [{"message": {"role": "assistant", "content": response.content}}]
        }
        
    except Exception as e:
        logger.error(f"Error during inference: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error: Ensure Ollama is running.")

if __name__ == "__main__":
    import uvicorn
    # Air-gapped deployment, bind to internal network only
    logger.info("Starting Enterprise Local Inference API on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
