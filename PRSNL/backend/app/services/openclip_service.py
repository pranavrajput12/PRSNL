"""
OpenCLIP Vision Service for PRSNL
Advanced image understanding and visual-semantic search
"""

import asyncio
import base64
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import OpenCLIP
try:
    import open_clip
    OPENCLIP_AVAILABLE = True
    logger.info("OpenCLIP successfully imported")
except ImportError as e:
    logger.warning(f"OpenCLIP not available: {e}")
    OPENCLIP_AVAILABLE = False


class OpenCLIPService:
    """Advanced image understanding service using OpenCLIP"""
    
    def __init__(self):
        self.enabled = OPENCLIP_AVAILABLE
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Model configuration
        self.model_name = settings.OPENCLIP_MODEL
        self.pretrained = settings.OPENCLIP_PRETRAINED
        
        if self.enabled:
            self._initialize_model()
        else:
            logger.warning("OpenCLIP service disabled. Install open-clip-torch to enable.")
    
    def _initialize_model(self):
        """Initialize OpenCLIP model and components"""
        try:
            logger.info(f"Loading OpenCLIP model: {self.model_name} ({self.pretrained})")
            
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                self.model_name,
                pretrained=self.pretrained,
                device=self.device
            )
            
            self.tokenizer = open_clip.get_tokenizer(self.model_name)
            
            # Set to evaluation mode
            self.model.eval()
            
            logger.info(f"OpenCLIP model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenCLIP model: {e}")
            self.enabled = False
    
    async def encode_image(self, image: Union[str, bytes, Image.Image]) -> Optional[np.ndarray]:
        """
        Encode image to feature vector
        
        Args:
            image: Image path, bytes, or PIL Image
            
        Returns:
            Feature vector or None if failed
        """
        if not self.enabled:
            logger.warning("OpenCLIP service not enabled")
            return None
        
        try:
            # Load and preprocess image
            if isinstance(image, str):
                # File path
                pil_image = Image.open(image).convert('RGB')
            elif isinstance(image, bytes):
                # Image bytes
                pil_image = Image.open(io.BytesIO(image)).convert('RGB')
            elif isinstance(image, Image.Image):
                # PIL Image
                pil_image = image.convert('RGB')
            else:
                logger.error(f"Unsupported image type: {type(image)}")
                return None
            
            # Preprocess and encode
            image_tensor = self.preprocess(pil_image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()
            
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            return None
    
    async def encode_text(self, text: str) -> Optional[np.ndarray]:
        """
        Encode text to feature vector
        
        Args:
            text: Text to encode
            
        Returns:
            Feature vector or None if failed
        """
        if not self.enabled:
            logger.warning("OpenCLIP service not enabled")
            return None
        
        try:
            # Tokenize and encode
            text_tokens = self.tokenizer([text]).to(self.device)
            
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.cpu().numpy().flatten()
            
        except Exception as e:
            logger.error(f"Error encoding text: {e}")
            return None
    
    async def compute_similarity(self, 
                               image: Union[str, bytes, Image.Image], 
                               text: str) -> Optional[float]:
        """
        Compute similarity between image and text
        
        Args:
            image: Image to compare
            text: Text to compare
            
        Returns:
            Similarity score (0-1) or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            # Encode both
            image_features = await self.encode_image(image)
            text_features = await self.encode_text(text)
            
            if image_features is None or text_features is None:
                return None
            
            # Compute cosine similarity
            similarity = np.dot(image_features, text_features)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return None
    
    async def find_best_text_match(self, 
                                  image: Union[str, bytes, Image.Image], 
                                  text_candidates: List[str]) -> Dict[str, Any]:
        """
        Find the best matching text for an image
        
        Args:
            image: Image to match
            text_candidates: List of text descriptions
            
        Returns:
            Best match information
        """
        if not self.enabled:
            return {"error": "OpenCLIP service not enabled"}
        
        try:
            # Encode image once
            image_features = await self.encode_image(image)
            if image_features is None:
                return {"error": "Failed to encode image"}
            
            # Encode all text candidates
            similarities = []
            for text in text_candidates:
                text_features = await self.encode_text(text)
                if text_features is not None:
                    similarity = np.dot(image_features, text_features)
                    similarities.append({
                        "text": text,
                        "similarity": float(similarity)
                    })
            
            if not similarities:
                return {"error": "No valid text encodings"}
            
            # Sort by similarity
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return {
                "best_match": similarities[0],
                "all_matches": similarities,
                "total_candidates": len(text_candidates)
            }
            
        except Exception as e:
            logger.error(f"Error finding best text match: {e}")
            return {"error": str(e)}
    
    async def generate_image_description(self, 
                                       image: Union[str, bytes, Image.Image],
                                       description_templates: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate description for an image using predefined templates
        
        Args:
            image: Image to describe
            description_templates: Custom templates or use defaults
            
        Returns:
            Generated description and alternatives
        """
        if not self.enabled:
            return {"error": "OpenCLIP service not enabled"}
        
        # Default description templates
        if description_templates is None:
            description_templates = [
                "a photo of {}",
                "a picture of {}",
                "an image of {}",
                "a drawing of {}",
                "a painting of {}",
                "a sketch of {}",
                "a screenshot of {}",
                "a digital art of {}",
                "a close-up of {}",
                "a view of {}",
                "a person",
                "a man",
                "a woman",
                "a child",
                "an animal",
                "a cat",
                "a dog",
                "a bird",
                "a car",
                "a building",
                "a tree",
                "a flower",
                "a landscape",
                "a cityscape",
                "food",
                "a document",
                "text",
                "a chart",
                "a graph",
                "a diagram",
                "a map",
                "a computer screen",
                "a phone",
                "a book",
                "a table",
                "a chair",
                "indoor scene",
                "outdoor scene",
                "nature",
                "technology",
                "art",
                "business",
                "education",
                "entertainment",
                "sports",
                "travel"
            ]
        
        try:
            result = await self.find_best_text_match(image, description_templates)
            
            if "error" in result:
                return result
            
            # Format response
            best_match = result["best_match"]
            confidence = best_match["similarity"]
            
            # Determine confidence level
            if confidence > 0.3:
                confidence_level = "high"
            elif confidence > 0.2:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            return {
                "description": best_match["text"],
                "confidence": confidence,
                "confidence_level": confidence_level,
                "alternatives": result["all_matches"][:5],  # Top 5 alternatives
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating image description: {e}")
            return {"error": str(e)}
    
    async def batch_encode_images(self, images: List[Union[str, bytes, Image.Image]]) -> List[Optional[np.ndarray]]:
        """
        Encode multiple images in batch
        
        Args:
            images: List of images to encode
            
        Returns:
            List of feature vectors
        """
        if not self.enabled:
            return [None] * len(images)
        
        results = []
        for image in images:
            features = await self.encode_image(image)
            results.append(features)
        
        return results
    
    async def batch_encode_texts(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Encode multiple texts in batch
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of feature vectors
        """
        if not self.enabled:
            return [None] * len(texts)
        
        results = []
        for text in texts:
            features = await self.encode_text(text)
            results.append(features)
        
        return results
    
    async def search_images_by_text(self, 
                                   text_query: str,
                                   image_embeddings: List[Dict[str, Any]],
                                   top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search images by text query using precomputed embeddings
        
        Args:
            text_query: Search query
            image_embeddings: List of {"id": str, "embedding": np.ndarray, "metadata": dict}
            top_k: Number of results to return
            
        Returns:
            Ranked search results
        """
        if not self.enabled:
            return []
        
        try:
            # Encode query
            query_features = await self.encode_text(text_query)
            if query_features is None:
                return []
            
            # Compute similarities
            results = []
            for item in image_embeddings:
                if "embedding" in item and item["embedding"] is not None:
                    similarity = np.dot(query_features, item["embedding"])
                    results.append({
                        "id": item.get("id"),
                        "similarity": float(similarity),
                        "metadata": item.get("metadata", {})
                    })
            
            # Sort and return top_k
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching images by text: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "enabled": self.enabled,
            "model_name": self.model_name,
            "pretrained": self.pretrained,
            "device": self.device,
            "available": OPENCLIP_AVAILABLE
        }
    
    def is_image_file(self, filename: str) -> bool:
        """Check if file is a supported image format"""
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        return Path(filename).suffix.lower() in supported_formats


# Singleton instance
openclip_service = OpenCLIPService()