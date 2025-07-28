"""
AI Router Service - Intelligently routes AI tasks to appropriate providers
Optimizes for cost, performance, and availability
Can be enhanced with LangChain ReAct agent for content-based routing
"""
import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Literal, Optional

from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
from app.config import settings
from app.services.ai_router_types import (
    AIProvider, TaskType, AITask, ProviderConfig, RoutingDecision
)
from app.core.langfuse_client import langfuse_client

logger = logging.getLogger(__name__)

class AIRouter:
    """Routes AI tasks to the most appropriate provider based on multiple factors"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        # Usage tracking now handled by Langfuse
        self.provider_health = {provider: True for provider in AIProvider}
        self.enhanced_ai_router = None
        self._init_enhanced_router()
    
    def _init_enhanced_router(self):
        """Initialize enhanced router if available"""
        try:
            from app.services.ai_router_enhanced import enhanced_ai_router
            self.enhanced_ai_router = enhanced_ai_router
            enhanced_ai_router.set_base_router(self)
            logger.info("Enhanced AI router initialized successfully")
        except ImportError:
            logger.debug("Enhanced AI router not available")
        except Exception as e:
            logger.error(f"Failed to initialize enhanced AI router: {e}")
        
    def _initialize_providers(self) -> Dict[AIProvider, ProviderConfig]:
        """Initialize provider configurations"""
        return {
            AIProvider.AZURE_OPENAI: ProviderConfig(
                name=AIProvider.AZURE_OPENAI,
                max_tokens_per_request=8192,
                supports_streaming=True,
                supports_vision=True,  # Confirmed: GPT-4.1 supports vision
                supports_embeddings=True,
                avg_response_time_ms=500
            ),
            AIProvider.FALLBACK: ProviderConfig(
                name=AIProvider.FALLBACK,
                max_tokens_per_request=1000,
                supports_streaming=False,
                supports_vision=False,
                supports_embeddings=False,
                avg_response_time_ms=10
            )
        }
    
    @observe(name="route_task")
    async def route_task(self, task: AITask) -> AIProvider:
        """
        Route task to the best provider based on:
        1. Task requirements (vision, streaming, embeddings)
        2. Provider availability
        3. Cost optimization
        4. Performance requirements
        """
        suitable_providers = self._get_suitable_providers(task)
        
        if not suitable_providers:
            logger.warning(f"No suitable providers for task {task.type}")
            return AIProvider.FALLBACK
            
        # Score providers based on multiple factors
        scores = {}
        for provider in suitable_providers:
            scores[provider] = self._calculate_provider_score(provider, task)
            
        # Select provider with highest score
        best_provider = max(scores, key=scores.get)
        
        logger.info(f"Routing {task.type} task to {best_provider.value}")
        return best_provider
    
    def _get_suitable_providers(self, task: AITask) -> List[AIProvider]:
        """Get providers that can handle the task requirements"""
        suitable = []
        
        for provider, config in self.providers.items():
            # Skip unhealthy providers
            if not self.provider_health.get(provider, True):
                continue
                
            # Check task compatibility
            if task.type == TaskType.VISION and not config.supports_vision:
                continue
            if task.type == TaskType.EMBEDDING and not config.supports_embeddings:
                continue
            if task.type == TaskType.STREAMING and not config.supports_streaming:
                continue
                
            suitable.append(provider)
            
        return suitable
    
    def _calculate_provider_score(self, provider: AIProvider, task: AITask) -> float:
        """Calculate provider score based on multiple factors"""
        config = self.providers[provider]
        score = 0.0
        
        # Provider preference scoring (Langfuse tracks actual costs)
        if provider == AIProvider.FALLBACK:
            score += 5  # Lower score for fallback
        else:
            score += 30  # Prefer primary providers
            
        # Performance factor (faster = higher score)
        score += 1000 / config.avg_response_time_ms * 10
        
        # Reliability factor
        score += config.success_rate * 20
        
        # Priority factor
        if task.priority >= 8 and provider == AIProvider.AZURE_OPENAI:
            score += 20  # Use premium provider for high priority
            
        # Langfuse tracks usage patterns for load balancing insights
            
        return score
    
    async def execute_with_fallback(self, task: AITask, execute_fn) -> Any:
        """Execute task with automatic fallback on failure"""
        # Use enhanced routing if available and enabled
        if self._should_use_enhanced_routing(task):
            try:
                logger.info("Using enhanced AI routing with ReAct agent")
                return await self.enhanced_ai_router.execute_with_enhanced_routing(task, execute_fn)
            except Exception as e:
                logger.warning(f"Enhanced routing failed, falling back to basic routing: {e}")
                # Fall through to basic routing
        
        # Basic routing
        providers = [await self.route_task(task)]
        
        # Add fallback chain
        if providers[-1] != AIProvider.FALLBACK:
            providers.append(AIProvider.FALLBACK)
            
        last_error = None
        
        for provider in providers:
            try:
                start_time = time.time()
                result = await execute_fn(provider, task)
                
                # Update stats on success
                self._update_stats(provider, success=True, 
                                 response_time=time.time() - start_time)
                
                return result
                
            except Exception as e:
                logger.error(f"Provider {provider.value} failed: {e}")
                last_error = e
                self._update_stats(provider, success=False)
                
                # Mark provider as unhealthy if failed
                # Langfuse tracks error patterns
                self.provider_health[provider] = False
                asyncio.create_task(self._health_check(provider))
                    
        # All providers failed
        raise last_error or Exception("All AI providers failed")
    
    def _should_use_enhanced_routing(self, task: AITask) -> bool:
        """Determine if enhanced routing should be used"""
        # Check if enhanced routing is available
        if not self.enhanced_ai_router or not self.enhanced_ai_router.enabled:
            return False
            
        # Use enhanced routing for complex tasks or high priority
        if task.priority >= 7:
            return True
            
        # Use enhanced routing for specific task types
        if task.type in [TaskType.TEXT_GENERATION, TaskType.VISION]:
            return True
            
        # Use enhanced routing if content is complex
        if isinstance(task.content, str) and len(task.content) > 1000:
            return True
            
        return False
    
    def _update_stats(self, provider: AIProvider, success: bool, 
                     response_time: float = 0, tokens: int = 0):
        """Update provider statistics - usage tracking handled by Langfuse"""
        if success and response_time > 0:
            # Update average response time for routing decisions
            config = self.providers[provider]
            current_avg = config.avg_response_time_ms
            new_avg = (current_avg * 0.9 + response_time * 1000 * 0.1)
            config.avg_response_time_ms = new_avg
    
    async def _health_check(self, provider: AIProvider):
        """Periodically check provider health"""
        await asyncio.sleep(60)  # Wait before retry
        
        # Simple health check - could be enhanced
        self.provider_health[provider] = True
        self.usage_stats[provider]["errors"] = 0
        logger.info(f"Provider {provider.value} marked as healthy again")
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get usage report - now handled by Langfuse"""
        # Langfuse provides comprehensive usage tracking and cost analysis
        return {
            "message": "Usage tracking is now handled by Langfuse",
            "langfuse_url": settings.LANGFUSE_HOST,
            "provider_health": {
                provider.value: health 
                for provider, health in self.provider_health.items()
            }
        }
    
    async def stream_task(self, task: AITask):
        """Stream AI response in chunks for real-time display"""
        provider = await self.route_task(task)
        
        try:
            if provider == AIProvider.AZURE_OPENAI:
                # Stream from Azure OpenAI
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    api_key=settings.AZURE_OPENAI_API_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
                
                stream = client.chat.completions.create(
                    model=settings.AZURE_OPENAI_DEPLOYMENT,
                    messages=[{"role": "user", "content": task.content}],
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                        
                                    
        except Exception as e:
            logger.error(f"Streaming error with {provider.value}: {e}")
            yield f"Error: {str(e)}"
    
    def recommend_optimization(self) -> List[str]:
        """Provide optimization recommendations - enhanced by Langfuse insights"""
        recommendations = [
            "Visit Langfuse dashboard for detailed usage analytics and cost optimization insights",
            f"Dashboard URL: {settings.LANGFUSE_HOST}"
        ]
        
        # Check provider health
        for provider, is_healthy in self.provider_health.items():
            if not is_healthy:
                recommendations.append(
                    f"{provider.value} is currently unhealthy. Check configuration."
                )
        
        # Add enhanced routing recommendations if available
        if self.enhanced_ai_router and self.enhanced_ai_router.enabled:
            enhanced_recommendations = self.enhanced_ai_router._generate_routing_recommendations()
            recommendations.extend([f"[Enhanced] {rec}" for rec in enhanced_recommendations])
                
        return recommendations
    
    def get_enhanced_routing_report(self) -> Dict[str, Any]:
        """Get comprehensive routing report including enhanced insights"""
        enhanced_available = self.enhanced_ai_router is not None
        enhanced_enabled = enhanced_available and self.enhanced_ai_router.enabled
        
        report = {
            "basic_usage": self.get_usage_report(),
            "recommendations": self.recommend_optimization(),
            "enhanced_routing_available": enhanced_available
        }
        
        if enhanced_enabled:
            try:
                report["enhanced_insights"] = self.enhanced_ai_router.get_performance_report()
                report["enhanced_routing_enabled"] = True
            except Exception as e:
                logger.error(f"Failed to get enhanced routing report: {e}")
                report["enhanced_routing_enabled"] = False
                report["enhanced_error"] = str(e)
        else:
            report["enhanced_routing_enabled"] = False
            
        return report


# Global router instance
ai_router = AIRouter()