"""
OpenCLIP REST API Endpoints for PRSNL (Simplified Version)
Advanced image understanding and visual-semantic search
"""

import base64
import io
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, Field

from app.services.openclip_service import openclip_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openclip", tags=["openclip"])

# Pydantic models
class TextEncodeRequest(BaseModel):
    text: str = Field(..., description="Text to encode")

class ModelInfoResponse(BaseModel):
    enabled: bool
    model_name: str
    pretrained: str
    device: str
    available: bool

@router.get("/health")
async def health_check():
    """Health check for OpenCLIP service"""
    model_info = openclip_service.get_model_info()
    return {
        "status": "healthy" if model_info["enabled"] else "disabled",
        "service": "openclip",
        "model_info": model_info
    }

@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """Get information about the loaded OpenCLIP model"""
    return openclip_service.get_model_info()

@router.post("/encode/text")
async def encode_text(request: TextEncodeRequest):
    """
    Encode text to feature vector using OpenCLIP
    
    Args:
        request: Text encoding request
        
    Returns:
        Feature vector encoding
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    try:
        encoding = await openclip_service.encode_text(request.text)
        
        if encoding is None:
            return {
                "success": False,
                "error": "Failed to encode text"
            }
        
        return {
            "success": True,
            "encoding": encoding.tolist(),
            "shape": list(encoding.shape)
        }
        
    except Exception as e:
        logger.error(f"Error in encode_text endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported image formats"""
    return {
        "supported_formats": [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"],
        "max_file_size": "10MB",
        "recommendations": {
            "format": "JPEG or PNG",
            "resolution": "224x224 to 2048x2048",
            "color_space": "RGB"
        }
    }

@router.get("/examples")
async def get_api_examples():
    """Get API usage examples"""
    return {
        "examples": {
            "encode_text": {
                "endpoint": "/openclip/encode/text",
                "method": "POST",
                "payload": {"text": "a photo of a cat"},
                "description": "Encode text to feature vector"
            },
            "health_check": {
                "endpoint": "/openclip/health",
                "method": "GET",
                "description": "Check service status"
            }
        },
        "note": "This is a simplified version for testing. Full API with image processing requires open-clip-torch installation."
    }