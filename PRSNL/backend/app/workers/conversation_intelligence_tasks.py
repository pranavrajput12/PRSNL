"""
Conversation Intelligence Celery Tasks

Phase 2: Enhanced multi-agent coordination using Celery Groups and Chords
for parallel execution and intelligent result aggregation.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
from celery import group, chord
from app.workers.celery_app import celery_app
from app.workers.retry_strategies import IntelligentRetryTask, apply_retry_strategy
from app.db.database import get_db_connection
from app.services.unified_ai_service import UnifiedAIService
from app.services.conversation_intelligence import ConversationIntelligenceAgent
from app.services.realtime_progress_service import send_task_progress

logger = logging.getLogger(__name__)


@celery_app.task(name="conversation.process_distributed", base=IntelligentRetryTask, bind=True, agent_type="conversation_intelligence")
def process_conversation_distributed(self, conversation_id: str, user_id: str, options: Dict[str, Any] = None):
    """
    Orchestrate distributed conversation intelligence processing using Celery coordination.
    
    Uses Group -> Chord pattern for parallel agent execution with intelligent aggregation.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _process_conversation_distributed_async(self.request.id, conversation_id, user_id, options or {})
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Distributed conversation processing failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_process_conversation_distributed")
async def _process_conversation_distributed_async(task_id: str, conversation_id: str, user_id: str, options: Dict[str, Any]):
    """Async implementation of distributed conversation processing"""
    
    try:
        await _send_progress_update(task_id, conversation_id, "conversation_intelligence", 0, 3, "Starting distributed processing")
        
        # Load conversation data
        async with get_db_connection() as db:
            conversation = await db.fetchrow("""
                SELECT * FROM conversations WHERE id = $1 AND user_id = $2
            """, UUID(conversation_id), UUID(user_id))
            
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            messages = await db.fetch("""
                SELECT * FROM conversation_messages 
                WHERE conversation_id = $1 
                ORDER BY created_at ASC
            """, UUID(conversation_id))
        
        if not messages:
            return {"status": "skipped", "message": "No messages to process"}
        
        await _send_progress_update(task_id, conversation_id, "conversation_intelligence", 1, 3, "Creating agent group")
        
        # Create parallel agent group using Celery Groups
        agent_group = group([
            technical_content_extraction_task.s(conversation_id, [dict(msg) for msg in messages]),
            learning_journey_analysis_task.s(conversation_id, [dict(msg) for msg in messages]),
            actionable_insights_extraction_task.s(conversation_id, [dict(msg) for msg in messages]),
            knowledge_gap_identification_task.s(conversation_id, [dict(msg) for msg in messages]),
            contextual_analysis_task.s(conversation_id, dict(conversation), [dict(msg) for msg in messages]),
            pattern_recognition_task.s(conversation_id, [dict(msg) for msg in messages]),
            sentiment_progression_task.s(conversation_id, [dict(msg) for msg in messages]),
            topic_evolution_task.s(conversation_id, [dict(msg) for msg in messages])
        ])
        
        # Execute agents in parallel and aggregate with Chord
        await _send_progress_update(task_id, conversation_id, "conversation_intelligence", 2, 3, "Executing parallel agents")
        
        # Use Chord for intelligent aggregation
        workflow = chord(agent_group)(
            conversation_synthesis_task.s(conversation_id, user_id, options)
        )
        
        # Start workflow
        workflow_result = workflow.apply_async()
        
        await _send_progress_update(task_id, conversation_id, "conversation_intelligence", 3, 3, "Workflow initiated")
        
        return {
            "status": "workflow_initiated",
            "conversation_id": conversation_id,
            "workflow_id": workflow_result.id,
            "parallel_agents": 8,
            "initiated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Distributed conversation processing async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.technical_extraction", base=IntelligentRetryTask, bind=True, agent_type="content_analysis", queue="ai_analysis")
def technical_content_extraction_task(self, conversation_id: str, messages: List[Dict[str, Any]]):
    """Extract technical content and concepts from conversation"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _technical_extraction_async(self.request.id, conversation_id, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Technical extraction failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "technical_extraction", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_technical_extraction")
async def _technical_extraction_async(task_id: str, conversation_id: str, messages: List[Dict[str, Any]]):
    """Technical content extraction implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Extract technical concepts and code examples
        combined_content = "\n".join([msg.get("content", "") for msg in messages])
        
        technical_analysis = await ai_service.extract_technical_concepts(
            content=combined_content,
            extract_code=True,
            identify_technologies=True,
            find_patterns=True
        )
        
        return {
            "agent": "technical_extraction",
            "status": "completed",
            "result": technical_analysis,
            "confidence": technical_analysis.get("confidence", 0.8),
            "concepts_count": len(technical_analysis.get("concepts", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Technical extraction async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.learning_analysis", bind=True, max_retries=2, queue="ai_analysis")
def learning_journey_analysis_task(self, conversation_id: str, messages: List[Dict[str, Any]]):
    """Analyze learning progression and educational value"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _learning_analysis_async(self.request.id, conversation_id, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Learning analysis failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "learning_analysis", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_learning_analysis")
async def _learning_analysis_async(task_id: str, conversation_id: str, messages: List[Dict[str, Any]]):
    """Learning progression analysis implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Analyze learning progression through conversation
        learning_analysis = await ai_service.analyze_learning_progression(
            messages=messages,
            identify_knowledge_building=True,
            track_skill_development=True,
            find_learning_moments=True
        )
        
        return {
            "agent": "learning_analysis",
            "status": "completed", 
            "result": learning_analysis,
            "confidence": learning_analysis.get("confidence", 0.75),
            "learning_moments": len(learning_analysis.get("key_moments", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Learning analysis async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.insights_extraction", bind=True, max_retries=2, queue="ai_analysis")
def actionable_insights_extraction_task(self, conversation_id: str, messages: List[Dict[str, Any]]):
    """Extract actionable insights and recommendations"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _insights_extraction_async(self.request.id, conversation_id, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Insights extraction failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "insights_extraction", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_insights_extraction")
async def _insights_extraction_async(task_id: str, conversation_id: str, messages: List[Dict[str, Any]]):
    """Actionable insights extraction implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Extract actionable insights and next steps
        insights = await ai_service.extract_actionable_insights(
            messages=messages,
            generate_recommendations=True,
            identify_next_steps=True,
            find_improvement_areas=True
        )
        
        return {
            "agent": "insights_extraction",
            "status": "completed",
            "result": insights,
            "confidence": insights.get("confidence", 0.8),
            "insights_count": len(insights.get("insights", [])),
            "recommendations_count": len(insights.get("recommendations", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Insights extraction async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.gap_identification", bind=True, max_retries=2, queue="ai_analysis")
def knowledge_gap_identification_task(self, conversation_id: str, messages: List[Dict[str, Any]]):
    """Identify knowledge gaps and learning opportunities"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _gap_identification_async(self.request.id, conversation_id, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Gap identification failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "gap_identification", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_gap_identification")
async def _gap_identification_async(task_id: str, conversation_id: str, messages: List[Dict[str, Any]]):
    """Knowledge gap identification implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Identify knowledge gaps and missing information
        gap_analysis = await ai_service.identify_knowledge_gaps(
            messages=messages,
            find_missing_concepts=True,
            suggest_learning_paths=True,
            identify_prerequisites=True
        )
        
        return {
            "agent": "gap_identification",
            "status": "completed",
            "result": gap_analysis,
            "confidence": gap_analysis.get("confidence", 0.7),
            "gaps_count": len(gap_analysis.get("gaps", [])),
            "suggestions_count": len(gap_analysis.get("suggestions", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Gap identification async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.contextual_analysis", bind=True, max_retries=2, queue="ai_analysis")
def contextual_analysis_task(self, conversation_id: str, conversation: Dict[str, Any], messages: List[Dict[str, Any]]):
    """Analyze conversation context and metadata"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _contextual_analysis_async(self.request.id, conversation_id, conversation, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Contextual analysis failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "contextual_analysis", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_contextual_analysis")
async def _contextual_analysis_async(task_id: str, conversation_id: str, conversation: Dict[str, Any], messages: List[Dict[str, Any]]):
    """Contextual analysis implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Analyze conversation context and flow
        context_analysis = await ai_service.analyze_conversation_context(
            conversation_metadata=conversation,
            messages=messages,
            analyze_flow=True,
            identify_topics=True,
            track_sentiment=True
        )
        
        return {
            "agent": "contextual_analysis",
            "status": "completed",
            "result": context_analysis,
            "confidence": context_analysis.get("confidence", 0.8),
            "topics_count": len(context_analysis.get("topics", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Contextual analysis async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.pattern_recognition", bind=True, max_retries=2, queue="ai_analysis")
def pattern_recognition_task(self, conversation_id: str, messages: List[Dict[str, Any]]):
    """Recognize patterns in conversation flow and content"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _pattern_recognition_async(self.request.id, conversation_id, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Pattern recognition failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "pattern_recognition", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_pattern_recognition")
async def _pattern_recognition_async(task_id: str, conversation_id: str, messages: List[Dict[str, Any]]):
    """Pattern recognition implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Recognize conversation patterns
        pattern_analysis = await ai_service.recognize_conversation_patterns(
            messages=messages,
            identify_structures=True,
            find_recurring_themes=True,
            analyze_question_types=True
        )
        
        return {
            "agent": "pattern_recognition",
            "status": "completed",
            "result": pattern_analysis,
            "confidence": pattern_analysis.get("confidence", 0.75),
            "patterns_count": len(pattern_analysis.get("patterns", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pattern recognition async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.sentiment_progression", bind=True, max_retries=2, queue="ai_analysis")
def sentiment_progression_task(self, conversation_id: str, messages: List[Dict[str, Any]]):
    """Analyze sentiment progression throughout conversation"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _sentiment_progression_async(self.request.id, conversation_id, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Sentiment progression failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "sentiment_progression", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_sentiment_progression")
async def _sentiment_progression_async(task_id: str, conversation_id: str, messages: List[Dict[str, Any]]):
    """Sentiment progression analysis implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Track sentiment changes over conversation
        sentiment_analysis = await ai_service.analyze_sentiment_progression(
            messages=messages,
            track_emotional_journey=True,
            identify_turning_points=True,
            measure_engagement=True
        )
        
        return {
            "agent": "sentiment_progression",
            "status": "completed",
            "result": sentiment_analysis,
            "confidence": sentiment_analysis.get("confidence", 0.7),
            "sentiment_points": len(sentiment_analysis.get("progression", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sentiment progression async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.topic_evolution", bind=True, max_retries=2, queue="ai_analysis")
def topic_evolution_task(self, conversation_id: str, messages: List[Dict[str, Any]]):
    """Track topic evolution and transitions"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _topic_evolution_async(self.request.id, conversation_id, messages)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Topic evolution failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        return {"agent": "topic_evolution", "error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_topic_evolution")
async def _topic_evolution_async(task_id: str, conversation_id: str, messages: List[Dict[str, Any]]):
    """Topic evolution analysis implementation"""
    
    try:
        ai_service = UnifiedAIService()
        
        # Track how topics evolve and change
        topic_analysis = await ai_service.analyze_topic_evolution(
            messages=messages,
            track_transitions=True,
            identify_branches=True,
            measure_depth=True
        )
        
        return {
            "agent": "topic_evolution",
            "status": "completed",
            "result": topic_analysis,
            "confidence": topic_analysis.get("confidence", 0.8),
            "topics_count": len(topic_analysis.get("topics", [])),
            "transitions_count": len(topic_analysis.get("transitions", [])),
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Topic evolution async failed: {e}", exc_info=True)
        raise


@celery_app.task(name="conversation.synthesis", base=IntelligentRetryTask, bind=True, agent_type="conversation_intelligence", queue="ai_analysis")
def conversation_synthesis_task(self, agent_results: List[Dict[str, Any]], conversation_id: str, user_id: str, options: Dict[str, Any]):
    """
    Intelligent synthesis of all agent results using Celery Chord callback.
    
    This task receives results from all parallel agents and creates a comprehensive
    conversation intelligence summary.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _conversation_synthesis_async(self.request.id, agent_results, conversation_id, user_id, options)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Conversation synthesis failed: {e}", exc_info=True)
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


@observe(name="worker_conversation_synthesis")
async def _conversation_synthesis_async(task_id: str, agent_results: List[Dict[str, Any]], conversation_id: str, user_id: str, options: Dict[str, Any]):
    """Intelligent conversation synthesis implementation"""
    
    try:
        await _send_progress_update(task_id, conversation_id, "conversation_synthesis", 0, 4, "Starting intelligent synthesis")
        
        # Filter successful agent results
        successful_results = [result for result in agent_results if result.get("status") == "completed"]
        failed_agents = [result.get("agent", "unknown") for result in agent_results if result.get("status") == "failed"]
        
        logger.info(f"Synthesis: {len(successful_results)} successful, {len(failed_agents)} failed agents")
        
        await _send_progress_update(task_id, conversation_id, "conversation_synthesis", 1, 4, "Aggregating agent insights")
        
        # Aggregate insights by agent type
        aggregated_insights = {}
        confidence_scores = {}
        
        for result in successful_results:
            agent_name = result.get("agent", "unknown")
            aggregated_insights[agent_name] = result.get("result", {})
            confidence_scores[agent_name] = result.get("confidence", 0.5)
        
        await _send_progress_update(task_id, conversation_id, "conversation_synthesis", 2, 4, "Creating comprehensive summary")
        
        # Create comprehensive conversation intelligence
        ai_service = UnifiedAIService()
        
        comprehensive_summary = await ai_service.synthesize_conversation_intelligence(
            agent_insights=aggregated_insights,
            confidence_scores=confidence_scores,
            failed_agents=failed_agents,
            synthesis_options=options.get("synthesis", {})
        )
        
        await _send_progress_update(task_id, conversation_id, "conversation_synthesis", 3, 4, "Storing results")
        
        # Store comprehensive results
        async with get_db_connection() as db:
            await db.execute("""
                UPDATE conversations 
                SET 
                    intelligence_analysis = $2,
                    analysis_status = 'completed',
                    analyzed_at = CURRENT_TIMESTAMP,
                    agent_insights = $3,
                    synthesis_metadata = $4
                WHERE id = $1
            """, 
                UUID(conversation_id),
                comprehensive_summary,
                aggregated_insights,
                {
                    "successful_agents": len(successful_results),
                    "failed_agents": failed_agents,
                    "overall_confidence": sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0,
                    "synthesis_options": options
                }
            )
        
        await _send_progress_update(task_id, conversation_id, "conversation_synthesis", 4, 4, "Synthesis completed")
        
        return {
            "status": "completed",
            "conversation_id": conversation_id,
            "comprehensive_summary": comprehensive_summary,
            "agent_results_count": len(successful_results),
            "failed_agents": failed_agents,
            "overall_confidence": sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Conversation synthesis async failed: {e}", exc_info=True)
        raise


async def _send_progress_update(
    task_id: str,
    entity_id: str,
    progress_type: str,
    current_value: int,
    total_value: Optional[int] = None,
    message: Optional[str] = None
):
    """Send progress update to database and WebSocket"""
    try:
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO task_progress (
                    task_id, entity_id, progress_type, current_value,
                    total_value, message, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                ON CONFLICT (task_id) DO UPDATE SET
                    current_value = EXCLUDED.current_value,
                    total_value = EXCLUDED.total_value,
                    message = EXCLUDED.message,
                    updated_at = CURRENT_TIMESTAMP
            """,
                task_id, entity_id, progress_type, current_value,
                total_value, message
            )
            
        # Send WebSocket update for real-time progress
        await send_task_progress(
            task_id=task_id,
            progress_type=progress_type,
            current_value=current_value,
            total_value=total_value,
            message=message,
            entity_id=entity_id,
            metadata={"task_type": "conversation_intelligence"}
        )
        logger.info(f"Progress update: {task_id} - {progress_type} - {current_value}/{total_value} - {message}")
        
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")