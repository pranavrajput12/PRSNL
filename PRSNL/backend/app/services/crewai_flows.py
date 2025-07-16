"""
CrewAI 0.141.0 Flows Implementation with Multimodal Support
Revolutionary event-driven workflows with image processing capabilities
"""

import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import base64
from pathlib import Path

from crewai import Agent, Crew, Task, Process
from crewai.flow.flow import Flow, listen, start
from crewai.tools import tool
from langchain_openai import AzureChatOpenAI
from PIL import Image
import io

from app.config import settings
from app.services.performance_monitoring import profile_ai, track_custom_metric
from app.services.document_extraction_enhanced import EnhancedDocumentExtractor
from app.db.database import get_db_connection

logger = logging.getLogger(__name__)


class DocumentProcessingFlow(Flow):
    """
    Event-driven document processing flow with persistence
    Supports multimodal content (text + images)
    """
    
    def __init__(self):
        super().__init__()
        self.llm = AzureChatOpenAI(
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=0.1
        )
        
        # Initialize agents with multimodal capabilities
        self._initialize_agents()
        
        # Track flow metrics
        self.metrics = {
            "documents_processed": 0,
            "images_analyzed": 0,
            "errors": 0
        }
    
    def _initialize_agents(self):
        """Initialize specialized agents for the flow"""
        
        # Document Analysis Agent
        self.document_analyst = Agent(
            role="Document Analyst",
            goal="Extract comprehensive insights from documents",
            backstory="Expert in analyzing documents and extracting structured information",
            llm=self.llm,
            verbose=True
        )
        
        # Vision Analysis Agent (Multimodal)
        self.vision_analyst = Agent(
            role="Vision Analyst",
            goal="Analyze images and extract visual information",
            backstory="Specialist in computer vision and image analysis",
            llm=self.llm,
            multimodal=True,  # Enable multimodal capabilities
            verbose=True
        )
        
        # Quality Assurance Agent
        self.qa_agent = Agent(
            role="Quality Assurance",
            goal="Ensure extraction quality and completeness",
            backstory="Expert in data quality and validation",
            llm=self.llm,
            verbose=True
        )
        
        # Knowledge Synthesis Agent
        self.synthesizer = Agent(
            role="Knowledge Synthesizer",
            goal="Combine insights from multiple sources",
            backstory="Expert in knowledge integration and synthesis",
            llm=self.llm,
            verbose=True
        )
    
    @start()
    async def receive_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entry point for document processing
        Handles both text and image inputs
        """
        logger.info(f"Starting document processing flow for: {data.get('document_id')}")
        
        # Initialize flow state
        state = {
            "document_id": data.get("document_id"),
            "document_text": data.get("text", ""),
            "images": data.get("images", []),
            "metadata": {
                "started_at": datetime.utcnow().isoformat(),
                "source": data.get("source", "unknown")
            },
            "results": {},
            "errors": []
        }
        
        # Track metrics
        self.metrics["documents_processed"] += 1
        track_custom_metric("crewai.documents.started", 1)
        
        return state
    
    @listen(receive_document)
    @profile_ai(model="gpt-4", operation="text_analysis")
    async def analyze_text(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text content of the document"""
        if not state["document_text"]:
            logger.info("No text content to analyze")
            return state
        
        try:
            # Create text analysis task
            task = Task(
                description=f"""Analyze this document text and extract:
                1. Key topics and themes
                2. Named entities (people, organizations, locations)
                3. Important dates and events
                4. Technical concepts mentioned
                5. Overall sentiment and tone
                
                Document: {state['document_text'][:3000]}...""",
                agent=self.document_analyst,
                expected_output="Structured analysis with all requested information"
            )
            
            # Execute task
            result = await task.execute_async()
            
            state["results"]["text_analysis"] = {
                "status": "completed",
                "data": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Text analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Text analysis error: {e}")
            state["errors"].append(f"Text analysis failed: {str(e)}")
            self.metrics["errors"] += 1
        
        return state
    
    @listen(receive_document)
    @profile_ai(model="gpt-4-vision", operation="image_analysis")
    async def analyze_images(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze images using multimodal capabilities"""
        if not state["images"]:
            logger.info("No images to analyze")
            return state
        
        try:
            image_results = []
            
            for idx, image_data in enumerate(state["images"]):
                logger.info(f"Analyzing image {idx + 1}/{len(state['images'])}")
                
                # Create vision analysis task
                task = Task(
                    description=f"""Analyze this image and extract:
                    1. What is shown in the image
                    2. Any text visible in the image (OCR)
                    3. Charts, graphs, or diagrams present
                    4. Key visual elements and their relationships
                    5. Any data or metrics shown
                    
                    Provide detailed analysis for knowledge extraction.""",
                    agent=self.vision_analyst,
                    expected_output="Detailed visual analysis with extracted information",
                    context={"image": image_data}  # Pass image data to agent
                )
                
                # Execute vision task
                result = await task.execute_async()
                
                image_results.append({
                    "image_index": idx,
                    "analysis": result,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                self.metrics["images_analyzed"] += 1
                track_custom_metric("crewai.images.analyzed", 1)
            
            state["results"]["image_analysis"] = {
                "status": "completed",
                "images_analyzed": len(image_results),
                "data": image_results
            }
            
            logger.info(f"Image analysis completed for {len(image_results)} images")
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            state["errors"].append(f"Image analysis failed: {str(e)}")
            self.metrics["errors"] += 1
        
        return state
    
    @listen(analyze_text)
    @listen(analyze_images)
    async def quality_check(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform quality check on extracted data"""
        try:
            # Compile all results for QA
            qa_input = {
                "text_analysis": state["results"].get("text_analysis", {}),
                "image_analysis": state["results"].get("image_analysis", {})
            }
            
            task = Task(
                description=f"""Review the analysis results and:
                1. Check for completeness
                2. Identify any missing information
                3. Validate consistency across text and image analysis
                4. Rate overall quality (1-10)
                5. Suggest improvements if needed
                
                Analysis Results: {qa_input}""",
                agent=self.qa_agent,
                expected_output="Quality assessment with score and recommendations"
            )
            
            result = await task.execute_async()
            
            state["results"]["quality_check"] = {
                "status": "completed",
                "assessment": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Quality check completed")
            
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            state["errors"].append(f"Quality check failed: {str(e)}")
        
        return state
    
    @listen(quality_check)
    @profile_ai(model="gpt-4", operation="knowledge_synthesis")
    async def synthesize_knowledge(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all extracted information into unified knowledge"""
        try:
            # Prepare synthesis input
            synthesis_data = {
                "text_insights": state["results"].get("text_analysis", {}).get("data"),
                "visual_insights": state["results"].get("image_analysis", {}).get("data"),
                "quality_score": state["results"].get("quality_check", {}).get("assessment")
            }
            
            task = Task(
                description=f"""Synthesize all extracted information into a comprehensive knowledge summary:
                1. Combine insights from text and images
                2. Identify key findings and patterns
                3. Create actionable recommendations
                4. Highlight important connections
                5. Generate a executive summary
                
                All Data: {synthesis_data}""",
                agent=self.synthesizer,
                expected_output="Comprehensive knowledge synthesis with key insights"
            )
            
            result = await task.execute_async()
            
            state["results"]["synthesis"] = {
                "status": "completed",
                "knowledge": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Mark flow as completed
            state["metadata"]["completed_at"] = datetime.utcnow().isoformat()
            state["metadata"]["status"] = "success"
            
            logger.info("Knowledge synthesis completed successfully")
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            state["errors"].append(f"Synthesis failed: {str(e)}")
            state["metadata"]["status"] = "failed"
        
        return state


class MultimodalDocumentProcessor:
    """
    High-level interface for processing documents with CrewAI Flows
    Supports text, images, and mixed media documents
    """
    
    def __init__(self):
        self.flow = DocumentProcessingFlow()
        self.extractor = EnhancedDocumentExtractor()
    
    async def process_document(
        self, 
        document_id: str,
        content: Union[str, bytes],
        content_type: str = "text/plain",
        images: Optional[List[bytes]] = None
    ) -> Dict[str, Any]:
        """
        Process a document with multimodal capabilities
        
        Args:
            document_id: Unique document identifier
            content: Document content (text or binary)
            content_type: MIME type of content
            images: Optional list of image bytes
            
        Returns:
            Processing results with all extracted information
        """
        try:
            # Prepare document data
            doc_data = {
                "document_id": document_id,
                "source": content_type
            }
            
            # Handle text content
            if content_type.startswith("text/"):
                doc_data["text"] = content if isinstance(content, str) else content.decode('utf-8')
            
            # Handle images
            if images:
                # Convert images to base64 for processing
                doc_data["images"] = []
                for img_bytes in images:
                    base64_img = base64.b64encode(img_bytes).decode('utf-8')
                    doc_data["images"].append(base64_img)
            
            # Run the flow
            logger.info(f"Starting CrewAI Flow for document {document_id}")
            result = await self.flow.kickoff_async(doc_data)
            
            # Track success metrics
            track_custom_metric("crewai.flow.completed", 1)
            
            return {
                "success": True,
                "document_id": document_id,
                "results": result.get("results", {}),
                "metadata": result.get("metadata", {}),
                "errors": result.get("errors", [])
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            track_custom_metric("crewai.flow.failed", 1)
            
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e)
            }
    
    async def process_mixed_media_document(
        self,
        document_id: str,
        pdf_bytes: bytes
    ) -> Dict[str, Any]:
        """
        Process a PDF document that may contain both text and images
        
        Args:
            document_id: Unique document identifier
            pdf_bytes: PDF file bytes
            
        Returns:
            Processing results with multimodal analysis
        """
        try:
            # Extract text and images from PDF
            # This would use a PDF processing library
            text_content = "Extracted PDF text content..."  # Placeholder
            images = []  # Placeholder for extracted images
            
            # Process with multimodal flow
            return await self.process_document(
                document_id=document_id,
                content=text_content,
                content_type="text/plain",
                images=images
            )
            
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {
                "success": False,
                "document_id": document_id,
                "error": str(e)
            }
    
    def get_flow_metrics(self) -> Dict[str, Any]:
        """Get metrics from the processing flow"""
        return {
            "documents_processed": self.flow.metrics["documents_processed"],
            "images_analyzed": self.flow.metrics["images_analyzed"],
            "errors": self.flow.metrics["errors"],
            "success_rate": (
                self.flow.metrics["documents_processed"] - self.flow.metrics["errors"]
            ) / max(self.flow.metrics["documents_processed"], 1)
        }


# Tools for CrewAI agents
@tool("extract_table_data")
def extract_table_from_image(image_base64: str) -> str:
    """
    Extract tabular data from an image
    Useful for processing charts and tables in documents
    """
    try:
        # Decode image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Here you would use OCR or specialized table extraction
        # For now, return placeholder
        return "Table data extraction would happen here"
        
    except Exception as e:
        return f"Error extracting table: {str(e)}"


@tool("analyze_chart")
def analyze_chart_data(image_base64: str) -> str:
    """
    Analyze charts and graphs in images
    Extract data points and trends
    """
    try:
        # Decode image
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Here you would use chart analysis logic
        # For now, return placeholder
        return "Chart analysis would happen here"
        
    except Exception as e:
        return f"Error analyzing chart: {str(e)}"


# Convenience function
def create_multimodal_processor() -> MultimodalDocumentProcessor:
    """Create a configured multimodal document processor"""
    return MultimodalDocumentProcessor()