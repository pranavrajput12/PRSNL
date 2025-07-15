"""
OCR Image Analysis Agent - Migrated to Crew.ai

This agent extracts text from images, analyzes visual content, and generates insights.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.media_tools import (
    OCRTool,
    VisionAnalysisTool,
    ImageDescriptionTool,
    ObjectDetectionTool
)
from app.tools.ai_tools import SummaryGeneratorTool, EntityExtractorTool, TagSuggesterTool

logger = logging.getLogger(__name__)


@register_agent("ocr_image_analyst")
class OCRImageAgent(PRSNLBaseAgent):
    """
    OCR Image Analysis Agent
    
    Specializes in extracting text from images, analyzing visual content,
    and generating comprehensive insights about image content.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "OCR Image Analyst")
        goal = kwargs.pop("goal", 
            "Extract text from images, analyze visual content, and generate "
            "comprehensive insights about image content for knowledge management"
        )
        backstory = kwargs.pop("backstory",
            "You are an expert in optical character recognition and computer vision. "
            "Your ability to extract meaningful information from images and visual "
            "content is unparalleled. You can see text where others see just pixels, "
            "understand context from visual cues, and transform images into searchable, "
            "actionable knowledge. Your expertise spans multiple languages and "
            "handwriting styles, making you invaluable for digitizing any visual content."
        )
        
        # Initialize with specialized tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                OCRTool(),
                VisionAnalysisTool(),
                ImageDescriptionTool(),
                ObjectDetectionTool(),
                SummaryGeneratorTool(),
                EntityExtractorTool(),
                TagSuggesterTool()
            ]
        
        # Call parent constructor
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )
    
    def get_specialized_instructions(self) -> str:
        """Get specialized instructions for this agent"""
        return """
        When analyzing images:
        1. Extract all readable text using OCR techniques
        2. Analyze visual content and context
        3. Identify objects, people, and scenes
        4. Generate descriptive summaries
        5. Extract entities from both text and visual elements
        6. Create relevant tags for searchability
        7. Assess image quality and clarity
        8. Identify language and writing styles
        9. Note any accessibility considerations
        10. Provide structured output for knowledge indexing
        
        Focus on accuracy and comprehensiveness while maintaining
        clear organization of extracted information.
        """
    
    def assess_image_quality(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assess image quality for OCR processing"""
        quality_assessment = {
            "overall_quality": "medium",
            "text_clarity": "medium",
            "recommended_preprocessing": [],
            "confidence_factors": {}
        }
        
        # Check resolution
        width = metadata.get("width", 0)
        height = metadata.get("height", 0)
        if width > 1920 and height > 1080:
            quality_assessment["overall_quality"] = "high"
            quality_assessment["text_clarity"] = "high"
        elif width < 800 or height < 600:
            quality_assessment["overall_quality"] = "low"
            quality_assessment["recommended_preprocessing"].append("upscale")
        
        # Check file size (proxy for compression)
        file_size = metadata.get("file_size", 0)
        if file_size < 100000:  # Less than 100KB
            quality_assessment["recommended_preprocessing"].append("enhance_contrast")
        
        return quality_assessment
    
    def optimize_ocr_settings(self, image_type: str) -> Dict[str, Any]:
        """Optimize OCR settings based on image type"""
        settings = {
            "preprocessing": [],
            "ocr_mode": "auto",
            "language": "eng",
            "confidence_threshold": 0.6
        }
        
        if image_type == "document":
            settings["ocr_mode"] = "document"
            settings["preprocessing"] = ["deskew", "despeckle"]
            settings["confidence_threshold"] = 0.8
        elif image_type == "handwritten":
            settings["ocr_mode"] = "handwritten"
            settings["preprocessing"] = ["enhance_contrast", "smooth"]
            settings["confidence_threshold"] = 0.5
        elif image_type == "screenshot":
            settings["ocr_mode"] = "screenshot"
            settings["preprocessing"] = ["scale", "sharpen"]
            settings["confidence_threshold"] = 0.7
        
        return settings
    
    def categorize_image_content(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize image content for better organization"""
        categories = {
            "primary_type": "unknown",
            "content_types": [],
            "processing_priority": "medium",
            "metadata_tags": []
        }
        
        # Analyze text content
        text_content = analysis_results.get("extracted_text", "")
        if text_content:
            if len(text_content) > 500:
                categories["content_types"].append("document")
                categories["processing_priority"] = "high"
            elif any(keyword in text_content.lower() for keyword in ["code", "function", "class", "import"]):
                categories["content_types"].append("code")
                categories["metadata_tags"].append("programming")
            elif any(keyword in text_content.lower() for keyword in ["recipe", "ingredients", "cook"]):
                categories["content_types"].append("recipe")
                categories["metadata_tags"].append("cooking")
        
        # Analyze visual elements
        objects = analysis_results.get("detected_objects", [])
        if objects:
            if any("person" in obj.lower() for obj in objects):
                categories["content_types"].append("people")
            if any("chart" in obj.lower() or "graph" in obj.lower() for obj in objects):
                categories["content_types"].append("data_visualization")
                categories["metadata_tags"].append("analytics")
        
        # Determine primary type
        if categories["content_types"]:
            categories["primary_type"] = categories["content_types"][0]
        
        return categories
    
    def generate_accessibility_metadata(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate accessibility metadata for the image"""
        accessibility = {
            "alt_text": "",
            "long_description": "",
            "text_equivalent": "",
            "accessibility_score": 0.0,
            "improvements": []
        }
        
        # Generate alt text
        description = analysis_results.get("description", "")
        if description:
            accessibility["alt_text"] = description[:125]  # Keep under 125 chars
        
        # Generate long description
        extracted_text = analysis_results.get("extracted_text", "")
        if extracted_text:
            accessibility["long_description"] = extracted_text[:500]
            accessibility["text_equivalent"] = extracted_text
        
        # Calculate accessibility score
        score = 0.0
        if accessibility["alt_text"]:
            score += 0.4
        if accessibility["long_description"]:
            score += 0.3
        if accessibility["text_equivalent"]:
            score += 0.3
        
        accessibility["accessibility_score"] = score
        
        # Suggest improvements
        if score < 0.7:
            accessibility["improvements"].append("Add more descriptive alt text")
        if not accessibility["text_equivalent"] and extracted_text:
            accessibility["improvements"].append("Include text equivalent")
        
        return accessibility


@register_agent("enhanced_ocr_analyst")
class EnhancedOCRImageAgent(OCRImageAgent):
    """
    Enhanced OCR Image Agent with advanced capabilities
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add advanced tools
        from app.tools.media_tools import (
            HandwritingRecognitionTool,
            TableExtractionTool,
            FormProcessorTool
        )
        self.add_tool(HandwritingRecognitionTool())
        self.add_tool(TableExtractionTool())
        self.add_tool(FormProcessorTool())
    
    def get_specialized_instructions(self) -> str:
        """Enhanced instructions for advanced OCR processing"""
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional advanced OCR capabilities:
        11. Process handwritten text with specialized recognition
        12. Extract structured data from tables and forms
        13. Identify and preserve document layout and formatting
        14. Handle multi-column layouts and complex structures
        15. Process mathematical formulas and equations
        16. Extract data from charts and diagrams
        17. Handle multiple languages in single images
        18. Process degraded or low-quality historical documents
        """
    
    def process_structured_documents(self, image_path: str) -> Dict[str, Any]:
        """Process structured documents like forms and tables"""
        return {
            "document_type": "form",
            "fields_extracted": [],
            "tables_found": [],
            "structure_preserved": True,
            "confidence": 0.9
        }