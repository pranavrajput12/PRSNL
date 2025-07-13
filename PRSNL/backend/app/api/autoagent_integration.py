"""
AutoAgent Integration API for PRSNL Second Brain

This module provides FastAPI endpoints that expose AutoAgent's
multi-agent capabilities to the PRSNL frontend.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

# CRITICAL: Set environment variables BEFORE any autoagent imports
os.environ["DEFAULT_LOG"] = "False"  # Disable default logging to avoid directory issue
os.environ["DEBUG"] = "False"
# Enable function calling for Azure OpenAI
os.environ["FN_CALL"] = "True"  # Enable function calling
# Azure OpenAI supports function calling with API version 2023-07-01-preview or later
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-12-01-preview"  # Enable function calling

# Add AutoAgent to path
autoagent_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'autoagent')
sys.path.insert(0, autoagent_path)

from app.config import settings
from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from autoagent import Agent, MetaChain, Response
from autoagent.agents.prsnl_agents import PRSNLMultiAgentOrchestrator
from autoagent.logger import MetaChainLogger
from autoagent.memory.prsnl_memory import PRSNLMemory

router = APIRouter(prefix="/api/autoagent", tags=["autoagent"])

# Request/Response models
class ContentProcessingRequest(BaseModel):
    content: str
    title: Optional[str] = None
    tags: Optional[List[str]] = []
    url: Optional[str] = None
    type: Optional[str] = "general"

class TopicExplorationRequest(BaseModel):
    topic: str
    user_interests: List[str] = []
    depth: int = Field(default=2, ge=1, le=5)

class LearningPathRequest(BaseModel):
    goal: str
    current_knowledge: List[str] = []
    time_commitment: Optional[str] = "moderate"

class AgentResponse(BaseModel):
    status: str
    agent: str
    results: Dict[str, Any]
    timestamp: str

class MultiAgentResponse(BaseModel):
    request_id: str
    status: str
    results: Dict[str, Any]
    agents_involved: List[str]
    execution_time: float
    timestamp: str

# Initialize shared resources
# Set environment variables for AutoAgent to use Azure OpenAI
import litellm

litellm.azure_key = settings.AZURE_OPENAI_API_KEY
litellm.api_base = settings.AZURE_OPENAI_ENDPOINT

# Also set as env var for AutoAgent with function calling support
os.environ["AZURE_OPENAI_API_KEY"] = settings.AZURE_OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = settings.AZURE_OPENAI_ENDPOINT
os.environ["AZURE_OPENAI_API_VERSION"] = "2023-12-01-preview"  # Function calling support
os.environ["AZURE_OPENAI_DEPLOYMENT"] = settings.AZURE_OPENAI_DEPLOYMENT  # gpt-4.1 deployment
os.environ["OPENAI_API_KEY"] = settings.AZURE_OPENAI_API_KEY  # Fallback for libraries expecting this

memory = PRSNLMemory(
    db_url=settings.DATABASE_URL
)

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Environment variables already set above before imports

logger = MetaChainLogger(
    log_path=os.path.join(log_dir, 'autoagent.log')
)

orchestrator = PRSNLMultiAgentOrchestrator(memory, logger)

@router.on_event("startup")
async def startup():
    """Initialize AutoAgent resources on startup."""
    try:
        await memory.initialize()
        logger.info("AutoAgent integration initialized", title="Startup", color="green")
    except Exception as e:
        logger.info(f"Failed to initialize AutoAgent: {e}", color="red", title="ERROR")
        # Don't raise - allow service to start even if AutoAgent init fails

@router.on_event("shutdown")
async def shutdown():
    """Cleanup AutoAgent resources on shutdown."""
    await memory.close()

@router.post("/process-content", response_model=MultiAgentResponse)
async def process_new_content(request: ContentProcessingRequest):
    """
    Process new content through the multi-agent workflow.
    
    This endpoint triggers the Knowledge Curator, Research Synthesizer,
    and other agents to analyze and enhance new content.
    """
    start_time = datetime.utcnow()
    request_id = f"content-{start_time.timestamp()}"
    
    try:
        # Prepare content for processing
        content_data = {
            "content": request.content,
            "title": request.title,
            "tags": request.tags,
            "url": request.url,
            "type": request.type
        }
        
        # Process through multi-agent orchestrator
        results = await orchestrator.process_new_content(content_data)
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return MultiAgentResponse(
            request_id=request_id,
            status="completed",
            results=results,
            agents_involved=["knowledge_curator", "research_synthesizer"],
            execution_time=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.info(f"Error processing content: {e}", color="red", title="ERROR")
        raise HTTPException(status_code=500, detail=f"Content processing failed: {str(e)}")

@router.post("/explore-topic", response_model=MultiAgentResponse)
async def explore_topic(request: TopicExplorationRequest):
    """
    Explore a topic using the Content Explorer and Learning Pathfinder agents.
    
    This creates exploration paths, finds connections, and suggests learning sequences.
    """
    start_time = datetime.utcnow()
    request_id = f"explore-{start_time.timestamp()}"
    
    try:
        # Explore topic through orchestrator
        results = await orchestrator.explore_topic(
            topic=request.topic,
            user_interests=request.user_interests
        )
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return MultiAgentResponse(
            request_id=request_id,
            status="completed",
            results=results,
            agents_involved=["content_explorer", "learning_pathfinder"],
            execution_time=execution_time,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.info(f"Error exploring topic: {e}", color="red", title="ERROR")
        raise HTTPException(status_code=500, detail=f"Topic exploration failed: {str(e)}")

@router.post("/create-learning-path", response_model=AgentResponse)
async def create_learning_path(request: LearningPathRequest):
    """
    Create a personalized learning path for a specific goal.
    """
    try:
        # Use the learning pathfinder agent through MetaChain
        agent = orchestrator.learning_pathfinder
        
        messages = [
            {"role": "system", "content": "You are the Learning Pathfinder Agent. Create personalized learning sequences."},
            {"role": "user", "content": f"Create a comprehensive learning path for the goal: '{request.goal}'. Consider the user's current knowledge in: {', '.join(request.current_knowledge)}. Time commitment: {request.time_commitment}. Include milestones, resources, and practical exercises."}
        ]
        
        # Run agent through MetaChain
        response = await orchestrator.metachain.run_async(
            agent=agent,
            messages=messages,
            context_variables={"goal": request.goal, "current_knowledge": request.current_knowledge}
        )
        
        # Extract the result from the response
        result_content = response.messages[-1]["content"] if response.messages else "No learning path generated."
        
        return AgentResponse(
            status="completed",
            agent="learning_pathfinder",
            results={"learning_path": result_content},
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.info(f"Error creating learning path: {e}", color="red", title="ERROR")
        raise HTTPException(status_code=500, detail=f"Learning path creation failed: {str(e)}")

@router.get("/insights-report")
async def generate_insights_report(time_period: str = "week"):
    """
    Generate a comprehensive insights report from the knowledge base.
    """
    try:
        report = await orchestrator.generate_insights_report(time_period)
        
        return {
            "status": "completed",
            "report": report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.info(f"Error generating insights report: {e}", color="red", title="ERROR")
        raise HTTPException(status_code=500, detail=f"Insights report generation failed: {str(e)}")

@router.post("/find-connections/{item_id}")
async def find_connections(item_id: str, limit: int = 5):
    """
    Find connections for a specific item in the knowledge base.
    """
    try:
        connections = await memory.get_related_items(item_id, limit)
        
        # Enhance with agent analysis
        if connections:
            agent = orchestrator.knowledge_curator
            enhanced_connections = []
            
            for conn in connections:
                # Add explanation for why items are connected
                enhanced_conn = conn.copy()
                enhanced_conn["connection_explanation"] = (
                    f"Connected through shared concepts with {conn['similarity']:.2%} similarity"
                )
                enhanced_connections.append(enhanced_conn)
            
            return {
                "item_id": item_id,
                "connections": enhanced_connections,
                "total_found": len(enhanced_connections)
            }
        
        return {
            "item_id": item_id,
            "connections": [],
            "total_found": 0
        }
        
    except Exception as e:
        logger.info(f"Error finding connections: {e}", color="red", title="ERROR")
        raise HTTPException(status_code=500, detail=f"Connection finding failed: {str(e)}")

@router.post("/synthesize")
async def synthesize_items(item_ids: List[str], focus: Optional[str] = None):
    """
    Synthesize information from multiple items.
    """
    try:
        agent = orchestrator.research_synthesizer
        
        # Fetch items from database
        items_content = []
        async for conn in get_db_connection():
            for item_id in item_ids:
                row = await conn.fetchrow(
                    "SELECT title, content, summary FROM items WHERE id = $1::uuid",
                    item_id
                )
                if row:
                    items_content.append(f"Title: {row['title']}\nSummary: {row['summary']}\nContent: {row['content'][:500]}...")
        
        if not items_content:
            raise HTTPException(status_code=404, detail="No items found with provided IDs")
        
        # Create synthesis request
        messages = [
            {"role": "system", "content": "You are the Research Synthesis Agent. Synthesize information from multiple sources."},
            {"role": "user", "content": f"Synthesize the following items{' with focus on: ' + focus if focus else ''}:\n\n" + "\n\n---\n\n".join(items_content) + "\n\nProvide a comprehensive synthesis with key findings, patterns, contradictions, gaps, and insights."}
        ]
        
        # Run agent through MetaChain
        response = await orchestrator.metachain.run_async(
            agent=agent,
            messages=messages,
            context_variables={"item_ids": item_ids, "focus": focus}
        )
        
        # Extract the synthesis
        synthesis_content = response.messages[-1]["content"] if response.messages else "No synthesis generated."
        
        return {
            "status": "completed",
            "synthesis": synthesis_content,
            "items_processed": len(item_ids),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.info(f"Error synthesizing items: {e}", color="red", title="ERROR")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")

@router.get("/agent-status")
async def get_agent_status():
    """
    Get the status of all AutoAgent agents.
    """
    agents_status = []
    
    for agent_name, agent in orchestrator.agents.items():
        agents_status.append({
            "name": agent_name,
            "status": "active",
            "capabilities": [func.__name__ for func in agent.functions] if hasattr(agent, 'functions') else []
        })
    
    return {
        "total_agents": len(agents_status),
        "agents": agents_status,
        "memory_status": "connected" if memory.pool else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/custom-agent-query")
async def custom_agent_query(agent_name: str, query: str, context: Optional[Dict[str, Any]] = None):
    """
    Send a custom query to a specific agent.
    """
    if agent_name not in orchestrator.agents:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    try:
        agent = orchestrator.agents[agent_name]
        
        # Create a MetaChain client for this query
        client = MetaChain(log_path=logger)
        
        messages = [{"role": "user", "content": query}]
        context_variables = context or {}
        
        # Add knowledge base context
        kb_context = await memory.get_context_for_query(query)
        if kb_context:
            context_variables["knowledge_base_context"] = kb_context
        
        # Run the agent
        response: Response = await client.run_async(
            agent=agent,
            messages=messages,
            context_variables=context_variables,
            debug=True
        )
        
        return {
            "agent": agent_name,
            "query": query,
            "response": response.messages[-1]["content"] if response.messages else "No response",
            "context_used": bool(kb_context),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.info(f"Error in custom agent query: {e}", color="red", title="ERROR")
        raise HTTPException(status_code=500, detail=f"Agent query failed: {str(e)}")

@router.get("/health")
async def autoagent_health():
    """Health check endpoint for AutoAgent integration."""
    try:
        # Check memory connection
        memory_ok = memory.pool is not None
        
        # Check agents
        agents_ok = len(orchestrator.agents) == 4
        
        return {
            "status": "healthy" if memory_ok and agents_ok else "degraded",
            "service": "prsnl-autoagent",
            "memory_connected": memory_ok,
            "agents_loaded": agents_ok,
            "agent_count": len(orchestrator.agents),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "prsnl-autoagent",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }