"""
Vision AI Processing Service
Handles image analysis, OCR, and visual content understanding
"""
import base64
import io
import logging
from typing import Dict, List, Optional, Any
from PIL import Image
import pytesseract
import httpx

from app.services.ai_router import ai_router, AITask, TaskType, AIProvider
from app.config import settings

logger = logging.getLogger(__name__)

class VisionProcessor:
    """Process visual content using AI"""
    
    def __init__(self):
        self.ai_router = ai_router
        self.azure_endpoint = settings.AZURE_OPENAI_ENDPOINT
        self.azure_key = settings.AZURE_OPENAI_API_KEY
        
    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process an image to extract:
        - Text content (OCR)
        - Visual description
        - Detected objects/concepts
        - Related tags
        """
        try:
            # Load image
            with Image.open(image_path) as img:
                # Convert to base64 for AI processing
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                # Get image metadata
                width, height = img.size
                format = img.format
                
            # Create vision task
            task = AITask(
                type=TaskType.VISION,
                content={
                    "image_base64": img_base64,
                    "image_path": image_path,
                    "width": width,
                    "height": height
                },
                priority=5
            )
            
            # Execute with router
            result = await self.ai_router.execute_with_fallback(
                task, 
                self._execute_vision_task
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            # Fallback to basic OCR
            return await self._fallback_ocr(image_path)
    
    async def _execute_vision_task(self, provider: AIProvider, task: AITask) -> Dict[str, Any]:
        """Execute vision task with specified provider"""
        
        if provider == AIProvider.AZURE_OPENAI:
            return await self._azure_vision_analysis(task.content)
        elif provider == AIProvider.OLLAMA:
            return await self._ollama_vision_analysis(task.content)
        else:
            return await self._fallback_ocr(task.content["image_path"])
    
    async def _azure_vision_analysis(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Use Azure OpenAI GPT-4V for vision analysis"""
        
        if not self.azure_endpoint or not self.azure_key:
            raise ValueError("Azure OpenAI not configured")
            
        headers = {
            "api-key": self.azure_key,
            "Content-Type": "application/json"
        }
        
        # Prepare vision request
        messages = [{
            "role": "system",
            "content": "You are a vision AI that analyzes images. Extract text, describe the image, identify key objects and concepts, and suggest relevant tags."
        }, {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this image and provide: 1) All text found (OCR), 2) A description of what you see, 3) Key objects/concepts, 4) 5-10 relevant tags"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{content['image_base64']}"
                    }
                }
            ]
        }]
        
        payload = {
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.azure_endpoint}/openai/deployments/gpt-4o/chat/completions?api-version=2024-01-01-preview",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
        result = response.json()
        analysis_text = result["choices"][0]["message"]["content"]
        
        # Parse structured response
        return self._parse_vision_response(analysis_text)
    
    async def _ollama_vision_analysis(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Use Ollama with vision model (if available)"""
        
        # Check if Ollama has vision model (like llava)
        try:
            # For now, fall back to OCR since most Ollama models don't support vision
            # This could be enhanced when Ollama adds vision support
            return await self._fallback_ocr(content["image_path"])
        except Exception as e:
            logger.error(f"Ollama vision failed: {e}")
            raise
    
    async def _fallback_ocr(self, image_path: str) -> Dict[str, Any]:
        """Basic OCR fallback using Tesseract"""
        
        try:
            # Extract text using OCR
            with Image.open(image_path) as img:
                ocr_text = pytesseract.image_to_string(img)
                
            return {
                "text": ocr_text.strip(),
                "description": "Image processed with OCR",
                "objects": [],
                "tags": self._extract_tags_from_text(ocr_text),
                "provider": "tesseract"
            }
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return {
                "text": "",
                "description": "Failed to process image",
                "objects": [],
                "tags": [],
                "provider": "none"
            }
    
    def _parse_vision_response(self, response_text: str) -> Dict[str, Any]:
        """Parse structured response from vision AI"""
        
        # Simple parsing - could be enhanced with better prompting
        lines = response_text.strip().split('\n')
        
        result = {
            "text": "",
            "description": "",
            "objects": [],
            "tags": [],
            "provider": "azure_openai"
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "text" in line.lower() and "ocr" in line.lower():
                current_section = "text"
            elif "description" in line.lower():
                current_section = "description"
            elif "object" in line.lower() or "concept" in line.lower():
                current_section = "objects"
            elif "tag" in line.lower():
                current_section = "tags"
            else:
                # Add content to current section
                if current_section == "text":
                    result["text"] += line + " "
                elif current_section == "description":
                    result["description"] += line + " "
                elif current_section == "objects":
                    if line.startswith("-") or line.startswith("•"):
                        result["objects"].append(line[1:].strip())
                elif current_section == "tags":
                    if line.startswith("-") or line.startswith("•"):
                        result["tags"].append(line[1:].strip())
                    elif "," in line:
                        result["tags"].extend([t.strip() for t in line.split(",")])
        
        # Clean up
        result["text"] = result["text"].strip()
        result["description"] = result["description"].strip()
        result["tags"] = [t for t in result["tags"] if t][:10]  # Max 10 tags
        
        return result
    
    def _extract_tags_from_text(self, text: str) -> List[str]:
        """Extract basic tags from OCR text"""
        
        # Simple keyword extraction
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        words = text.lower().split()
        
        # Get unique words that aren't common
        tags = []
        for word in words:
            word = word.strip(".,!?;:")
            if len(word) > 3 and word not in common_words and word not in tags:
                tags.append(word)
                
        return tags[:5]  # Return top 5
    
    async def process_screenshot(self, screenshot_data: bytes) -> Dict[str, Any]:
        """Process a screenshot from clipboard or drag-drop"""
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(screenshot_data)
            tmp_path = tmp.name
            
        try:
            result = await self.process_image(tmp_path)
            return result
        finally:
            # Clean up
            import os
            os.unlink(tmp_path)
    
    async def link_to_text_items(self, image_result: Dict[str, Any], item_id: str):
        """Link visual content analysis to related text items"""
        
        # This would search for related items based on:
        # - Extracted text
        # - Detected objects
        # - Common tags
        
        # Implementation would use the embedding service
        # to find semantically similar items
        pass


# Global vision processor instance
vision_processor = VisionProcessor()