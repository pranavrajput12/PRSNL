"""
OpenCLIP REST API Endpoints for PRSNL
Advanced image understanding and visual-semantic search
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import base64
import io
from PIL import Image
import numpy as np

from app.services.openclip_service import openclip_service
# Rate limiting temporarily disabled for testing
# from app.middleware.rate_limit import openclip_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/openclip", tags=["openclip"])

# Pydantic models
class TextEncodeRequest(BaseModel):
    text: str = Field(..., description="Text to encode")

class ImageTextSimilarityRequest(BaseModel):
    text: str = Field(..., description="Text to compare")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")

class TextMatchRequest(BaseModel):
    text_candidates: List[str] = Field(..., description="List of text candidates")
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")

class ImageSearchRequest(BaseModel):
    text_query: str = Field(..., description="Search query text")
    top_k: int = Field(5, description="Number of results to return")

class BatchTextEncodeRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to encode")

class DescriptionRequest(BaseModel):
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
    description_templates: Optional[List[str]] = Field(None, description="Custom description templates")

# Response models
class EncodingResponse(BaseModel):
    success: bool
    encoding: Optional[List[float]] = None
    shape: Optional[List[int]] = None
    error: Optional[str] = None

class SimilarityResponse(BaseModel):
    success: bool
    similarity: Optional[float] = None
    error: Optional[str] = None

class DescriptionResponse(BaseModel):
    success: bool
    description: Optional[str] = None
    confidence: Optional[float] = None
    confidence_level: Optional[str] = None
    alternatives: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class ModelInfoResponse(BaseModel):
    enabled: bool
    model_name: str
    pretrained: str
    device: str
    available: bool

def decode_base64_image(base64_str: str) -> Image.Image:
    """Decode base64 string to PIL Image"""
    try:
        # Remove data:image/jpeg;base64, prefix if present
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image: {e}")

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

@router.post("/encode/text", response_model=EncodingResponse)
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
            return EncodingResponse(
                success=False,
                error="Failed to encode text"
            )
        
        return EncodingResponse(
            success=True,
            encoding=encoding.tolist(),
            shape=list(encoding.shape)
        )
        
    except Exception as e:
        logger.error(f"Error in encode_text endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/encode/image", response_model=EncodingResponse)
async def encode_image_file(file: UploadFile = File(...)):
    """
    Encode uploaded image to feature vector using OpenCLIP
    
    Args:
        file: Uploaded image file
        
    Returns:
        Feature vector encoding
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    try:
        # Read image file
        image_data = await file.read()
        
        encoding = await openclip_service.encode_image(image_data)
        
        if encoding is None:
            return EncodingResponse(
                success=False,
                error="Failed to encode image"
            )
        
        return EncodingResponse(
            success=True,
            encoding=encoding.tolist(),
            shape=list(encoding.shape)
        )
        
    except Exception as e:
        logger.error(f"Error in encode_image endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/encode/image-base64", response_model=EncodingResponse)
async def encode_image_base64(image_base64: str = Form(...)):
    """
    Encode base64 image to feature vector using OpenCLIP
    
    Args:
        image_base64: Base64 encoded image
        
    Returns:
        Feature vector encoding
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    try:
        image = decode_base64_image(image_base64)
        
        encoding = await openclip_service.encode_image(image)
        
        if encoding is None:
            return EncodingResponse(
                success=False,
                error="Failed to encode image"
            )
        
        return EncodingResponse(
            success=True,
            encoding=encoding.tolist(),
            shape=list(encoding.shape)
        )
        
    except Exception as e:
        logger.error(f"Error in encode_image_base64 endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similarity", response_model=SimilarityResponse)
async def compute_similarity_file(
    text: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Compute similarity between uploaded image and text
    
    Args:
        text: Text to compare
        file: Uploaded image file
        
    Returns:
        Similarity score (0-1)
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    try:
        # Read image file
        image_data = await file.read()
        
        similarity = await openclip_service.compute_similarity(image_data, text)
        
        if similarity is None:
            return SimilarityResponse(
                success=False,
                error="Failed to compute similarity"
            )
        
        return SimilarityResponse(
            success=True,
            similarity=similarity
        )
        
    except Exception as e:
        logger.error(f"Error in compute_similarity endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/similarity-base64", response_model=SimilarityResponse)
async def compute_similarity_base64(request: ImageTextSimilarityRequest):
    """
    Compute similarity between base64 image and text
    
    Args:
        request: Image-text similarity request
        
    Returns:
        Similarity score (0-1)
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    
    try:
        image = decode_base64_image(request.image_base64)
        
        similarity = await openclip_service.compute_similarity(image, request.text)
        
        if similarity is None:
            return SimilarityResponse(
                success=False,
                error="Failed to compute similarity"
            )
        
        return SimilarityResponse(
            success=True,
            similarity=similarity
        )
        
    except Exception as e:
        logger.error(f"Error in compute_similarity_base64 endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/find-best-match")
async def find_best_text_match_file(
    text_candidates: str = Form(..., description="JSON array of text candidates"),
    file: UploadFile = File(...)
):
    """
    Find the best matching text for an uploaded image
    
    Args:
        text_candidates: JSON string of text candidates
        file: Uploaded image file
        
    Returns:
        Best match information
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    try:
        import json
        candidates = json.loads(text_candidates)
        
        if not isinstance(candidates, list):
            raise HTTPException(status_code=400, detail="text_candidates must be a JSON array")
        
        # Read image file
        image_data = await file.read()
        
        result = await openclip_service.find_best_text_match(image_data, candidates)
        
        return JSONResponse(content=result)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for text_candidates")
    except Exception as e:
        logger.error(f"Error in find_best_text_match endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/find-best-match-base64")
async def find_best_text_match_base64(request: TextMatchRequest):
    """
    Find the best matching text for a base64 image
    
    Args:
        request: Text match request
        
    Returns:
        Best match information
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    
    try:
        image = decode_base64_image(request.image_base64)
        
        result = await openclip_service.find_best_text_match(image, request.text_candidates)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error in find_best_text_match_base64 endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/describe-image", response_model=DescriptionResponse)
async def describe_image_file(file: UploadFile = File(...)):
    """
    Generate description for an uploaded image
    
    Args:
        file: Uploaded image file
        
    Returns:
        Generated description and confidence
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    try:
        # Read image file
        image_data = await file.read()
        
        result = await openclip_service.generate_image_description(image_data)
        
        if "error" in result:
            return DescriptionResponse(
                success=False,
                error=result["error"]
            )
        
        return DescriptionResponse(
            success=True,
            description=result.get("description"),
            confidence=result.get("confidence"),
            confidence_level=result.get("confidence_level"),
            alternatives=result.get("alternatives")
        )
        
    except Exception as e:
        logger.error(f"Error in describe_image endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/describe-image-base64", response_model=DescriptionResponse)
async def describe_image_base64(request: DescriptionRequest):
    """
    Generate description for a base64 image
    
    Args:
        request: Description request
        
    Returns:
        Generated description and confidence
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    if not request.image_base64:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    
    try:
        image = decode_base64_image(request.image_base64)
        
        result = await openclip_service.generate_image_description(
            image, 
            request.description_templates
        )
        
        if "error" in result:
            return DescriptionResponse(
                success=False,
                error=result["error"]
            )
        
        return DescriptionResponse(
            success=True,
            description=result.get("description"),
            confidence=result.get("confidence"),
            confidence_level=result.get("confidence_level"),
            alternatives=result.get("alternatives")
        )
        
    except Exception as e:
        logger.error(f"Error in describe_image_base64 endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/encode-text")
async def batch_encode_text(request: BatchTextEncodeRequest):
    """
    Encode multiple texts in batch
    
    Args:
        request: Batch text encoding request
        
    Returns:
        List of encodings
    """
    if not openclip_service.enabled:
        raise HTTPException(status_code=503, detail="OpenCLIP service not available")
    
    try:
        encodings = await openclip_service.batch_encode_texts(request.texts)
        
        # Convert numpy arrays to lists
        result = []
        for encoding in encodings:
            if encoding is not None:
                result.append({
                    "success": True,
                    "encoding": encoding.tolist(),
                    "shape": list(encoding.shape)
                })
            else:
                result.append({
                    "success": False,
                    "encoding": None,
                    "error": "Failed to encode text"
                })
        
        return {
            "success": True,
            "results": result,
            "total": len(request.texts)
        }
        
    except Exception as e:
        logger.error(f"Error in batch_encode_text endpoint: {e}")
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
            "encode_image": {
                "endpoint": "/openclip/encode/image",
                "method": "POST",
                "payload": "multipart/form-data with image file",
                "description": "Encode image to feature vector"
            },
            "similarity": {
                "endpoint": "/openclip/similarity",
                "method": "POST",
                "payload": "multipart/form-data with text and image",
                "description": "Compute image-text similarity"
            },
            "describe_image": {
                "endpoint": "/openclip/describe-image",
                "method": "POST",
                "payload": "multipart/form-data with image file",
                "description": "Generate image description"
            }
        },
        "rate_limits": {
            "requests_per_minute": 30,
            "concurrent_requests": 5
        }
    }