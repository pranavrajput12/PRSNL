#!/usr/bin/env python3
"""
Cipher Azure OpenAI Proxy
Uses the official OpenAI SDK to properly handle Azure OpenAI authentication
Provides OpenAI-compatible API that Cipher can use
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from openai import AzureOpenAI
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/pronav/Personal Knowledge Base/PRSNL/backend/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cipher Azure Proxy")

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1')
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2023-12-01-preview')

if not all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT]):
    raise ValueError("Azure OpenAI credentials not found in environment")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

@app.get("/")
async def health():
    return {
        "status": "healthy",
        "service": "cipher-azure-proxy",
        "azure_endpoint": AZURE_OPENAI_ENDPOINT,
        "note": "OpenAI SDK handles Azure authentication automatically"
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Proxy OpenAI chat completions to Azure OpenAI using SDK"""
    try:
        # Log incoming request for debugging
        logger.info(f"Received chat completion request")
        body = await request.json()
        
        # Remove model from body, use deployment
        messages = body.get('messages', [])
        temperature = body.get('temperature', 0.7)
        max_tokens = body.get('max_tokens', 2000)
        stream = body.get('stream', False)
        
        # Use Azure OpenAI SDK
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,  # This is the deployment name
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            async def generate():
                for chunk in response:
                    yield f"data: {json.dumps(chunk.model_dump())}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            # Convert response to match OpenAI format
            return JSONResponse(content=response.model_dump())
            
    except Exception as e:
        logger.error(f"Error in chat completions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings")
async def embeddings(request: Request):
    """Proxy OpenAI embeddings to Azure OpenAI using SDK"""
    try:
        # Log incoming request for debugging
        logger.info(f"Received embeddings request")
        body = await request.json()
        input_text = body.get('input', '')
        
        # Handle both string and list inputs
        if isinstance(input_text, str):
            input_text = [input_text]
        
        # Use Azure OpenAI SDK for embeddings
        response = client.embeddings.create(
            model=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input=input_text
        )
        
        # Return in OpenAI format
        return JSONResponse(content=response.model_dump())
            
    except Exception as e:
        logger.error(f"Error in embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatible)"""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1677649963,
                "owned_by": "azure-openai",
                "permission": [],
                "root": "gpt-4",
                "parent": None,
            },
            {
                "id": "text-embedding-ada-002",
                "object": "model",
                "created": 1671217299,
                "owned_by": "azure-openai",
                "permission": [],
                "root": "text-embedding-ada-002",
                "parent": None,
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Cipher Azure Proxy on http://localhost:8002")
    print(f"📍 Using Azure endpoint: {AZURE_OPENAI_ENDPOINT}")
    print(f"🤖 Chat model: {AZURE_OPENAI_DEPLOYMENT}")
    print(f"🧮 Embedding model: {AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
    print("✅ OpenAI SDK handles Azure auth automatically")
    uvicorn.run(app, host="0.0.0.0", port=8002)