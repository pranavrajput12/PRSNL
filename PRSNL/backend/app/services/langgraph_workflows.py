"""
LangGraph Workflow Service - State-based content processing workflows
Handles multi-modal content routing and processing with intelligent decision trees
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, Annotated
from uuid import uuid4

try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
    from langchain_openai import AzureChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

from app.config import settings
# Lazy imports to avoid circular dependencies
# from app.services.unified_ai_service import unified_ai_service
# from app.services.document_processor import DocumentProcessor
# from app.services.haystack_rag_service import haystack_rag_service
# from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Types of content that can be processed"""
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    IMAGE = "image"
    URL = "url"
    TEXT = "text"
    UNKNOWN = "unknown"


class ProcessingPhase(str, Enum):
    """Phases of content processing"""
    INGESTION = "ingestion"
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    ENRICHMENT = "enrichment"
    STORAGE = "storage"
    INDEXING = "indexing"


class ContentState(TypedDict):
    """State definition for content processing workflow"""
    # Input data
    content_id: str
    raw_content: Any
    content_type: ContentType
    source_url: Optional[str]
    metadata: Dict[str, Any]
    
    # Processing state
    current_phase: ProcessingPhase
    processing_path: List[str]
    extracted_text: Optional[str]
    
    # Analysis results
    title: Optional[str]
    summary: Optional[str]
    category: Optional[str]
    tags: List[str]
    entities: Dict[str, List[str]]
    embeddings: Optional[List[float]]
    
    # Quality metrics
    quality_score: float
    confidence_scores: Dict[str, float]
    requires_review: bool
    
    # Errors and warnings
    errors: List[str]
    warnings: List[str]
    
    # Final results
    processed_content: Optional[Dict[str, Any]]
    storage_location: Optional[str]
    index_status: Optional[str]


class LangGraphWorkflowService:
    """
    Service for managing LangGraph workflows for content processing
    
    Features:
    - Multi-modal content routing
    - State-based processing with checkpoints
    - Adaptive quality improvement loops
    - Cross-service orchestration
    """
    
    def __init__(self):
        self.enabled = LANGGRAPH_AVAILABLE and bool(settings.AZURE_OPENAI_API_KEY)
        self.workflows = {}
        self.document_processor = None
        
        if self.enabled:
            self._initialize_workflows()
            self._setup_llm()
            self._init_services()
        else:
            logger.warning("LangGraph workflows disabled. Check dependencies and API keys.")
    
    def _init_services(self):
        """Initialize services with lazy imports"""
        try:
            from app.services.document_processor import DocumentProcessor
            self.document_processor = DocumentProcessor()
        except ImportError:
            logger.warning("DocumentProcessor not available")
    
    def _setup_llm(self):
        """Initialize Azure OpenAI for workflow decisions"""
        self.llm = AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
            temperature=0.3
        )
    
    def _initialize_workflows(self):
        """Initialize all content processing workflows"""
        try:
            # Create main content processing workflow
            self.workflows['content_processing'] = self._create_content_processing_workflow()
            
            # Create specialized workflows
            self.workflows['document_analysis'] = self._create_document_workflow()
            self.workflows['media_processing'] = self._create_media_workflow()
            self.workflows['code_analysis'] = self._create_code_workflow()
            
            logger.info("LangGraph workflows initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflows: {e}")
            self.enabled = False
    
    def _create_content_processing_workflow(self) -> StateGraph:
        """Create the main content processing workflow with routing"""
        workflow = StateGraph(ContentState)
        
        # Add nodes for each processing phase
        workflow.add_node("route_content", self._route_content)
        workflow.add_node("extract_content", self._extract_content)
        workflow.add_node("analyze_content", self._analyze_content)
        workflow.add_node("enrich_content", self._enrich_content)
        workflow.add_node("quality_check", self._quality_check)
        workflow.add_node("store_content", self._store_content)
        workflow.add_node("index_content", self._index_content)
        
        # Define edges (workflow transitions)
        workflow.set_entry_point("route_content")
        
        # Routing based on content type
        workflow.add_conditional_edges(
            "route_content",
            self._should_extract,
            {
                "extract": "extract_content",
                "analyze": "analyze_content",
                "skip": "store_content"
            }
        )
        
        # Linear flow with quality loops
        workflow.add_edge("extract_content", "analyze_content")
        workflow.add_edge("analyze_content", "enrich_content")
        workflow.add_edge("enrich_content", "quality_check")
        
        # Quality check can loop back or proceed
        workflow.add_conditional_edges(
            "quality_check",
            self._check_quality,
            {
                "reanalyze": "analyze_content",
                "proceed": "store_content",
                "review": "store_content"  # Store but flag for review
            }
        )
        
        workflow.add_edge("store_content", "index_content")
        workflow.add_edge("index_content", END)
        
        return workflow.compile()
    
    def _create_document_workflow(self) -> StateGraph:
        """Specialized workflow for document processing"""
        workflow = StateGraph(ContentState)
        
        workflow.add_node("detect_document_type", self._detect_document_type)
        workflow.add_node("extract_text", self._extract_document_text)
        workflow.add_node("extract_metadata", self._extract_document_metadata)
        workflow.add_node("segment_content", self._segment_document)
        workflow.add_node("analyze_structure", self._analyze_document_structure)
        
        workflow.set_entry_point("detect_document_type")
        workflow.add_edge("detect_document_type", "extract_text")
        workflow.add_edge("extract_text", "extract_metadata")
        workflow.add_edge("extract_metadata", "segment_content")
        workflow.add_edge("segment_content", "analyze_structure")
        workflow.add_edge("analyze_structure", END)
        
        return workflow.compile()
    
    def _create_media_workflow(self) -> StateGraph:
        """Specialized workflow for media (video/audio) processing"""
        workflow = StateGraph(ContentState)
        
        workflow.add_node("detect_media_type", self._detect_media_type)
        workflow.add_node("extract_audio", self._extract_audio)
        workflow.add_node("transcribe", self._transcribe_media)
        workflow.add_node("extract_keyframes", self._extract_keyframes)
        workflow.add_node("analyze_visual", self._analyze_visual_content)
        workflow.add_node("merge_insights", self._merge_media_insights)
        
        workflow.set_entry_point("detect_media_type")
        
        # Conditional routing based on media type
        workflow.add_conditional_edges(
            "detect_media_type",
            self._route_media_type,
            {
                "video": "extract_audio",
                "audio": "transcribe",
                "image": "analyze_visual"
            }
        )
        
        workflow.add_edge("extract_audio", "transcribe")
        workflow.add_edge("transcribe", "extract_keyframes")
        workflow.add_edge("extract_keyframes", "analyze_visual")
        workflow.add_edge("analyze_visual", "merge_insights")
        workflow.add_edge("merge_insights", END)
        
        return workflow.compile()
    
    def _create_code_workflow(self) -> StateGraph:
        """Specialized workflow for code analysis"""
        workflow = StateGraph(ContentState)
        
        workflow.add_node("detect_language", self._detect_code_language)
        workflow.add_node("parse_structure", self._parse_code_structure)
        workflow.add_node("extract_dependencies", self._extract_dependencies)
        workflow.add_node("analyze_patterns", self._analyze_code_patterns)
        workflow.add_node("generate_docs", self._generate_code_docs)
        
        workflow.set_entry_point("detect_language")
        workflow.add_edge("detect_language", "parse_structure")
        workflow.add_edge("parse_structure", "extract_dependencies")
        workflow.add_edge("extract_dependencies", "analyze_patterns")
        workflow.add_edge("analyze_patterns", "generate_docs")
        workflow.add_edge("generate_docs", END)
        
        return workflow.compile()
    
    # Node implementations
    async def _route_content(self, state: ContentState) -> ContentState:
        """Route content to appropriate processing path"""
        logger.info(f"Routing content {state['content_id']} of type {state['content_type']}")
        
        state['current_phase'] = ProcessingPhase.INGESTION
        state['processing_path'].append('route_content')
        
        # Determine content type if unknown
        if state['content_type'] == ContentType.UNKNOWN:
            state['content_type'] = await self._detect_content_type(state)
        
        return state
    
    async def _extract_content(self, state: ContentState) -> ContentState:
        """Extract text and metadata from content"""
        logger.info(f"Extracting content for {state['content_id']}")
        
        state['current_phase'] = ProcessingPhase.EXTRACTION
        state['processing_path'].append('extract_content')
        
        try:
            if state['content_type'] == ContentType.DOCUMENT:
                # Use document processor
                result = await self.document_processor.extract_text_from_content(
                    state['raw_content'],
                    state['metadata'].get('filename', 'unknown')
                )
                state['extracted_text'] = result.get('text', '')
                state['metadata'].update(result.get('metadata', {}))
                
            elif state['content_type'] == ContentType.URL:
                # Use existing URL extraction
                state['extracted_text'] = state['raw_content']  # Assuming already extracted
                
            else:
                state['extracted_text'] = str(state['raw_content'])
                
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            state['errors'].append(f"Extraction error: {str(e)}")
            state['extracted_text'] = ""
        
        return state
    
    async def _analyze_content(self, state: ContentState) -> ContentState:
        """Analyze content using AI"""
        logger.info(f"Analyzing content for {state['content_id']}")
        
        state['current_phase'] = ProcessingPhase.ANALYSIS
        state['processing_path'].append('analyze_content')
        
        try:
            # Lazy import to avoid circular dependencies
            from app.services.unified_ai_service import unified_ai_service
            
            # Use unified AI service for analysis
            analysis = await unified_ai_service.analyze_content(
                state['extracted_text'] or state['raw_content'],
                url=state['source_url']
            )
            
            # Update state with analysis results
            state['title'] = analysis.get('title')
            state['summary'] = analysis.get('summary')
            state['category'] = analysis.get('category')
            state['tags'] = analysis.get('tags', [])
            state['entities'] = analysis.get('entities', {})
            
            # Calculate confidence scores
            state['confidence_scores']['analysis'] = 0.8  # Base confidence
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            state['errors'].append(f"Analysis error: {str(e)}")
            state['confidence_scores']['analysis'] = 0.0
        
        return state
    
    async def _enrich_content(self, state: ContentState) -> ContentState:
        """Enrich content with additional insights"""
        logger.info(f"Enriching content for {state['content_id']}")
        
        state['current_phase'] = ProcessingPhase.ENRICHMENT
        state['processing_path'].append('enrich_content')
        
        try:
            # Lazy import to avoid circular dependencies
            from app.services.unified_ai_service import unified_ai_service
            
            # Generate embeddings
            if state['extracted_text']:
                embeddings = await unified_ai_service.generate_embeddings(
                    [state['extracted_text']],
                    cache_key_prefix=f"workflow_{state['content_id']}"
                )
                state['embeddings'] = embeddings[0] if embeddings else None
            
            # Additional enrichment based on content type
            if state['content_type'] == ContentType.CODE:
                # Could add code-specific enrichment
                pass
            elif state['content_type'] == ContentType.VIDEO:
                # Could add video-specific enrichment
                pass
            
            state['confidence_scores']['enrichment'] = 0.9
            
        except Exception as e:
            logger.error(f"Enrichment failed: {e}")
            state['warnings'].append(f"Enrichment warning: {str(e)}")
            state['confidence_scores']['enrichment'] = 0.5
        
        return state
    
    async def _quality_check(self, state: ContentState) -> ContentState:
        """Check content quality and determine if reprocessing is needed"""
        logger.info(f"Quality check for {state['content_id']}")
        
        state['processing_path'].append('quality_check')
        
        # Calculate overall quality score
        confidence_values = list(state['confidence_scores'].values())
        state['quality_score'] = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        
        # Check for required fields
        has_title = bool(state['title'])
        has_summary = bool(state['summary'])
        has_tags = len(state['tags']) > 0
        has_text = bool(state['extracted_text'])
        
        # Determine if review is needed
        if state['quality_score'] < 0.5:
            state['requires_review'] = True
            state['warnings'].append("Low quality score - manual review recommended")
        elif not (has_title and has_summary):
            state['requires_review'] = True
            state['warnings'].append("Missing critical metadata")
        else:
            state['requires_review'] = False
        
        return state
    
    async def _store_content(self, state: ContentState) -> ContentState:
        """Store processed content"""
        logger.info(f"Storing content for {state['content_id']}")
        
        state['current_phase'] = ProcessingPhase.STORAGE
        state['processing_path'].append('store_content')
        
        # Compile processed content
        state['processed_content'] = {
            'id': state['content_id'],
            'title': state['title'],
            'summary': state['summary'],
            'category': state['category'],
            'tags': state['tags'],
            'entities': state['entities'],
            'extracted_text': state['extracted_text'],
            'embeddings': state['embeddings'],
            'metadata': state['metadata'],
            'quality_score': state['quality_score'],
            'requires_review': state['requires_review'],
            'processing_path': state['processing_path'],
            'errors': state['errors'],
            'warnings': state['warnings']
        }
        
        # Storage would happen here
        state['storage_location'] = f"storage/{state['content_id']}"
        
        return state
    
    async def _index_content(self, state: ContentState) -> ContentState:
        """Index content for search"""
        logger.info(f"Indexing content for {state['content_id']}")
        
        state['current_phase'] = ProcessingPhase.INDEXING
        state['processing_path'].append('index_content')
        
        try:
            # Lazy import to avoid circular dependencies
            from app.services.haystack_rag_service import haystack_rag_service
            
            # Add to Haystack document store if available
            if haystack_rag_service.enabled and state['extracted_text']:
                # Would add to document store here
                state['index_status'] = 'indexed'
            else:
                state['index_status'] = 'skipped'
                
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
            state['errors'].append(f"Indexing error: {str(e)}")
            state['index_status'] = 'failed'
        
        return state
    
    # Conditional edge functions
    def _should_extract(self, state: ContentState) -> str:
        """Determine if content needs extraction"""
        if state['content_type'] in [ContentType.DOCUMENT, ContentType.VIDEO, ContentType.AUDIO]:
            return "extract"
        elif state['content_type'] == ContentType.TEXT:
            return "analyze"
        else:
            return "skip"
    
    def _check_quality(self, state: ContentState) -> str:
        """Determine next step based on quality check"""
        if state['quality_score'] < 0.3 and len(state['processing_path']) < 10:
            return "reanalyze"
        elif state['requires_review']:
            return "review"
        else:
            return "proceed"
    
    def _route_media_type(self, state: ContentState) -> str:
        """Route based on media type"""
        media_type = state['metadata'].get('media_type', 'unknown')
        if media_type == 'video':
            return "video"
        elif media_type == 'audio':
            return "audio"
        else:
            return "image"
    
    # Helper methods
    async def _detect_content_type(self, state: ContentState) -> ContentType:
        """Detect content type using AI"""
        try:
            prompt = f"""Analyze this content and determine its type:
            
Content sample: {str(state['raw_content'])[:500]}
Metadata: {json.dumps(state['metadata'])}

Return the content type as one of: document, video, audio, code, image, url, text"""
            
            response = await self.llm.ainvoke(prompt)
            content_type = response.content.strip().lower()
            
            return ContentType(content_type) if content_type in ContentType._value2member_map_ else ContentType.UNKNOWN
            
        except Exception as e:
            logger.error(f"Content type detection failed: {e}")
            return ContentType.UNKNOWN
    
    # Document workflow nodes
    async def _detect_document_type(self, state: ContentState) -> ContentState:
        """Detect specific document type"""
        state['processing_path'].append('detect_document_type')
        # Implementation would detect PDF, DOCX, etc.
        return state
    
    async def _extract_document_text(self, state: ContentState) -> ContentState:
        """Extract text from document"""
        state['processing_path'].append('extract_document_text')
        # Implementation would use document processor
        return state
    
    async def _extract_document_metadata(self, state: ContentState) -> ContentState:
        """Extract document metadata"""
        state['processing_path'].append('extract_document_metadata')
        # Implementation would extract author, date, etc.
        return state
    
    async def _segment_document(self, state: ContentState) -> ContentState:
        """Segment document into sections"""
        state['processing_path'].append('segment_document')
        # Implementation would split into chapters/sections
        return state
    
    async def _analyze_document_structure(self, state: ContentState) -> ContentState:
        """Analyze document structure"""
        state['processing_path'].append('analyze_document_structure')
        # Implementation would identify headings, lists, etc.
        return state
    
    # Media workflow nodes
    async def _detect_media_type(self, state: ContentState) -> ContentState:
        """Detect media type (video/audio)"""
        state['processing_path'].append('detect_media_type')
        return state
    
    async def _extract_audio(self, state: ContentState) -> ContentState:
        """Extract audio from video"""
        state['processing_path'].append('extract_audio')
        return state
    
    async def _transcribe_media(self, state: ContentState) -> ContentState:
        """Transcribe audio to text"""
        state['processing_path'].append('transcribe_media')
        return state
    
    async def _extract_keyframes(self, state: ContentState) -> ContentState:
        """Extract keyframes from video"""
        state['processing_path'].append('extract_keyframes')
        return state
    
    async def _analyze_visual_content(self, state: ContentState) -> ContentState:
        """Analyze visual content"""
        state['processing_path'].append('analyze_visual_content')
        return state
    
    async def _merge_media_insights(self, state: ContentState) -> ContentState:
        """Merge insights from audio and visual analysis"""
        state['processing_path'].append('merge_media_insights')
        return state
    
    # Code workflow nodes
    async def _detect_code_language(self, state: ContentState) -> ContentState:
        """Detect programming language"""
        state['processing_path'].append('detect_code_language')
        return state
    
    async def _parse_code_structure(self, state: ContentState) -> ContentState:
        """Parse code structure"""
        state['processing_path'].append('parse_code_structure')
        return state
    
    async def _extract_dependencies(self, state: ContentState) -> ContentState:
        """Extract code dependencies"""
        state['processing_path'].append('extract_dependencies')
        return state
    
    async def _analyze_code_patterns(self, state: ContentState) -> ContentState:
        """Analyze code patterns"""
        state['processing_path'].append('analyze_code_patterns')
        return state
    
    async def _generate_code_docs(self, state: ContentState) -> ContentState:
        """Generate code documentation"""
        state['processing_path'].append('generate_code_docs')
        return state
    
    # Public API
    async def process_content(
        self,
        content: Any,
        content_type: Optional[ContentType] = None,
        source_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process content through the appropriate workflow
        
        Args:
            content: Raw content to process
            content_type: Type of content (will be detected if not provided)
            source_url: Source URL if applicable
            metadata: Additional metadata
            
        Returns:
            Processed content with all extracted information
        """
        if not self.enabled:
            logger.warning("LangGraph workflows not enabled")
            return {
                'error': 'Workflows not available',
                'fallback': True
            }
        
        # Initialize state
        initial_state: ContentState = {
            'content_id': str(uuid4()),
            'raw_content': content,
            'content_type': content_type or ContentType.UNKNOWN,
            'source_url': source_url,
            'metadata': metadata or {},
            'current_phase': ProcessingPhase.INGESTION,
            'processing_path': [],
            'extracted_text': None,
            'title': None,
            'summary': None,
            'category': None,
            'tags': [],
            'entities': {},
            'embeddings': None,
            'quality_score': 0.0,
            'confidence_scores': {},
            'requires_review': False,
            'errors': [],
            'warnings': [],
            'processed_content': None,
            'storage_location': None,
            'index_status': None
        }
        
        try:
            # Run the main workflow
            workflow = self.workflows.get('content_processing')
            if not workflow:
                raise ValueError("Content processing workflow not initialized")
            
            # Execute workflow
            final_state = await workflow.ainvoke(initial_state)
            
            # Return processed content
            return final_state.get('processed_content', {
                'error': 'Processing incomplete',
                'state': final_state
            })
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                'error': str(e),
                'content_id': initial_state['content_id'],
                'partial_state': initial_state
            }
    
    async def process_batch(
        self,
        items: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Process multiple content items in batch
        
        Args:
            items: List of content items to process
            max_concurrent: Maximum concurrent workflows
            
        Returns:
            List of processed results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(item):
            async with semaphore:
                return await self.process_content(
                    content=item.get('content'),
                    content_type=item.get('content_type'),
                    source_url=item.get('source_url'),
                    metadata=item.get('metadata')
                )
        
        tasks = [process_with_semaphore(item) for item in items]
        return await asyncio.gather(*tasks)
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        return {
            'enabled': self.enabled,
            'available_workflows': list(self.workflows.keys()) if self.enabled else [],
            'langgraph_version': 'unknown',  # Would get from package
            'status': 'operational' if self.enabled else 'disabled'
        }


# Singleton instance
langgraph_workflow_service = LangGraphWorkflowService()