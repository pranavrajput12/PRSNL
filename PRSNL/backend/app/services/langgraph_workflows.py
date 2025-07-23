"""
LangGraph 0.5.3 Persistent Workflows with Checkpointing
Enables crash recovery and workflow state persistence
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict
from uuid import uuid4

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI

from app.config import settings
from app.services.performance_monitoring import profile_ai, profile_critical_section
from app.db.database import get_db_connection

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State schema for document processing workflows"""
    document_id: str
    document_text: str
    current_step: str
    metadata: Dict[str, Any]
    entities: List[str]
    summary: str
    insights: List[str]
    errors: List[str]
    messages: List[Dict[str, str]]
    completed_steps: List[str]
    timestamp: str


class PersistentWorkflowManager:
    """
    Manages persistent workflows with LangGraph 0.5.3 checkpointing
    Supports crash recovery and state persistence
    """
    
    def __init__(self, checkpoint_dir: str = None):
        """Initialize with checkpoint storage"""
        if checkpoint_dir is None:
            import tempfile
            import os
            # Use secure temporary directory instead of hardcoded /tmp
            checkpoint_dir = os.path.join(tempfile.gettempdir(), 'prsnl_checkpoints')
        self.checkpoint_dir = checkpoint_dir
        self.checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{checkpoint_dir}/workflows.db")
        
        # Initialize Azure OpenAI
        self.llm = AzureChatOpenAI(
            deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=0.1
        )
        
        # Build the workflow graph
        self.workflow = self._build_workflow_graph()
        
    def _build_workflow_graph(self) -> StateGraph:
        """Build the document processing workflow with checkpointing"""
        workflow = StateGraph(WorkflowState)
        
        # Define workflow nodes
        workflow.add_node("extract_metadata", self._extract_metadata)
        workflow.add_node("extract_entities", self._extract_entities)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("extract_insights", self._extract_insights)
        workflow.add_node("quality_check", self._quality_check)
        workflow.add_node("finalize", self._finalize_processing)
        
        # Set entry point
        workflow.set_entry_point("extract_metadata")
        
        # Define edges (workflow flow)
        workflow.add_edge("extract_metadata", "extract_entities")
        workflow.add_edge("extract_entities", "generate_summary")
        workflow.add_edge("generate_summary", "extract_insights")
        workflow.add_edge("extract_insights", "quality_check")
        
        # Conditional edge from quality check
        workflow.add_conditional_edges(
            "quality_check",
            self._should_retry,
            {
                "retry": "extract_metadata",  # Retry from beginning if quality is low
                "continue": "finalize"  # Continue to finalization if quality is good
            }
        )
        
        workflow.add_edge("finalize", END)
        
        # Compile with checkpointing
        return workflow.compile(checkpointer=self.checkpointer)
    
    @profile_ai(model="gpt-4", operation="metadata_extraction")
    async def _extract_metadata(self, state: WorkflowState) -> WorkflowState:
        """Extract metadata from document"""
        try:
            with profile_critical_section("metadata_extraction"):
                prompt = f"""Extract metadata from this document:
                
{state['document_text'][:2000]}...

Extract: title, author, date, type, language"""
                
                response = await self.llm.ainvoke([HumanMessage(content=prompt)])
                
                state['metadata'] = {
                    "extracted_at": datetime.utcnow().isoformat(),
                    "content": response.content
                }
                state['completed_steps'].append("extract_metadata")
                state['current_step'] = "extract_entities"
                
                logger.info(f"Metadata extracted for document {state['document_id']}")
                
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            state['errors'].append(f"Metadata extraction error: {str(e)}")
            
        return state
    
    @profile_ai(model="gpt-4", operation="entity_extraction")
    async def _extract_entities(self, state: WorkflowState) -> WorkflowState:
        """Extract entities from document"""
        try:
            prompt = f"""Extract all named entities from this document:
            
{state['document_text'][:3000]}...

Categories: people, organizations, locations, dates, technologies"""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            # Parse entities from response
            state['entities'] = response.content.split('\n')
            state['completed_steps'].append("extract_entities")
            state['current_step'] = "generate_summary"
            
            logger.info(f"Extracted {len(state['entities'])} entities")
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            state['errors'].append(f"Entity extraction error: {str(e)}")
            
        return state
    
    @profile_ai(model="gpt-4", operation="summarization")
    async def _generate_summary(self, state: WorkflowState) -> WorkflowState:
        """Generate document summary"""
        try:
            prompt = f"""Generate a comprehensive summary of this document:
            
{state['document_text'][:4000]}...

Create a 3-5 paragraph summary covering main points."""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            state['summary'] = response.content
            state['completed_steps'].append("generate_summary")
            state['current_step'] = "extract_insights"
            
            logger.info("Summary generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            state['errors'].append(f"Summary generation error: {str(e)}")
            
        return state
    
    @profile_ai(model="gpt-4", operation="insight_extraction")
    async def _extract_insights(self, state: WorkflowState) -> WorkflowState:
        """Extract key insights and actionable items"""
        try:
            prompt = f"""Based on this document and summary, extract key insights:

Document Summary:
{state.get('summary', 'No summary available')}

Extract:
1. Key insights (3-5 points)
2. Actionable recommendations
3. Important connections or patterns"""
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            state['insights'] = response.content.split('\n')
            state['completed_steps'].append("extract_insights")
            state['current_step'] = "quality_check"
            
            logger.info(f"Extracted {len(state['insights'])} insights")
            
        except Exception as e:
            logger.error(f"Error extracting insights: {e}")
            state['errors'].append(f"Insight extraction error: {str(e)}")
            
        return state
    
    def _quality_check(self, state: WorkflowState) -> WorkflowState:
        """Check quality of extraction and decide if retry is needed"""
        # Check if we have minimum required data
        has_metadata = bool(state.get('metadata'))
        has_entities = len(state.get('entities', [])) > 0
        has_summary = len(state.get('summary', '')) > 50
        has_insights = len(state.get('insights', [])) > 0
        
        # Calculate quality score
        quality_score = sum([has_metadata, has_entities, has_summary, has_insights]) / 4
        
        state['metadata']['quality_score'] = quality_score
        state['completed_steps'].append("quality_check")
        
        # Retry if quality is too low and we haven't retried too many times
        retry_count = state['metadata'].get('retry_count', 0)
        if quality_score < 0.6 and retry_count < 2:
            state['metadata']['retry_count'] = retry_count + 1
            state['current_step'] = "retry"
            logger.warning(f"Quality check failed (score: {quality_score}), retrying...")
        else:
            state['current_step'] = "continue"
            logger.info(f"Quality check passed (score: {quality_score})")
            
        return state
    
    def _should_retry(self, state: WorkflowState) -> str:
        """Determine if workflow should retry or continue"""
        return state['current_step']
    
    def _finalize_processing(self, state: WorkflowState) -> WorkflowState:
        """Finalize document processing"""
        state['completed_steps'].append("finalize")
        state['current_step'] = "completed"
        state['metadata']['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Document {state['document_id']} processing completed")
        return state
    
    async def process_document(
        self, 
        document_id: str, 
        document_text: str,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document with persistent workflow
        
        Args:
            document_id: Unique document identifier
            document_text: Document content to process
            thread_id: Optional thread ID for resuming workflows
            
        Returns:
            Processing results with workflow state
        """
        # Initialize workflow state
        initial_state = WorkflowState(
            document_id=document_id,
            document_text=document_text,
            current_step="extract_metadata",
            metadata={
                "started_at": datetime.utcnow().isoformat(),
                "thread_id": thread_id or str(uuid4())
            },
            entities=[],
            summary="",
            insights=[],
            errors=[],
            messages=[],
            completed_steps=[],
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Use existing thread or create new one
        config = {
            "configurable": {
                "thread_id": initial_state['metadata']['thread_id']
            }
        }
        
        try:
            # Run workflow with checkpointing
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            return {
                "success": True,
                "document_id": document_id,
                "thread_id": final_state['metadata']['thread_id'],
                "metadata": final_state['metadata'],
                "entities": final_state['entities'],
                "summary": final_state['summary'],
                "insights": final_state['insights'],
                "completed_steps": final_state['completed_steps'],
                "errors": final_state['errors'],
                "quality_score": final_state['metadata'].get('quality_score', 0)
            }
            
        except Exception as e:
            logger.error(f"Workflow processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id,
                "thread_id": initial_state['metadata']['thread_id']
            }
    
    async def resume_workflow(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume a previously interrupted workflow
        
        Args:
            thread_id: Thread ID of the workflow to resume
            
        Returns:
            Workflow state if found, None otherwise
        """
        try:
            # Get checkpoint state
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = self.checkpointer.get(config)
            
            if checkpoint and checkpoint.get('state'):
                state = checkpoint['state']
                logger.info(f"Resuming workflow {thread_id} from step: {state['current_step']}")
                
                # Continue workflow from checkpoint
                final_state = await self.workflow.ainvoke(state, config)
                
                return {
                    "success": True,
                    "resumed": True,
                    "thread_id": thread_id,
                    "state": final_state
                }
            else:
                logger.warning(f"No checkpoint found for thread {thread_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error resuming workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "thread_id": thread_id
            }
    
    async def list_active_workflows(self) -> List[Dict[str, Any]]:
        """List all active workflows with checkpoints"""
        try:
            # This would query the checkpoint database
            # Implementation depends on checkpoint storage backend
            return []
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []


# Convenience function for creating workflow manager
def create_workflow_manager() -> PersistentWorkflowManager:
    """Create a configured workflow manager instance"""
    return PersistentWorkflowManager()