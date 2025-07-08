"""
AI Router Service - Intelligently routes AI tasks to appropriate providers
Optimizes for cost, performance, and availability
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Literal
from enum import Enum
from dataclasses import dataclass
import time
import json
from app.config import settings

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    AZURE_OPENAI = "azure_openai"
    FALLBACK = "fallback"

class TaskType(Enum):
    EMBEDDING = "embedding"
    TEXT_GENERATION = "text_generation"
    VISION = "vision"
    STREAMING = "streaming"

@dataclass
class AITask:
    type: TaskType
    content: Any
    options: Dict[str, Any] = None
    priority: int = 5  # 1-10, higher is more important

@dataclass
class ProviderConfig:
    name: AIProvider
    cost_per_1k_tokens: float
    max_tokens_per_request: int
    supports_streaming: bool
    supports_vision: bool
    supports_embeddings: bool
    avg_response_time_ms: float
    success_rate: float = 0.95

class AIRouter:
    """Routes AI tasks to the most appropriate provider based on multiple factors"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.usage_stats = {provider: {"requests": 0, "tokens": 0, "errors": 0} 
                           for provider in AIProvider}
        self.provider_health = {provider: True for provider in AIProvider}
        
    def _initialize_providers(self) -> Dict[AIProvider, ProviderConfig]:
        """Initialize provider configurations"""
        return {
            AIProvider.AZURE_OPENAI: ProviderConfig(
                name=AIProvider.AZURE_OPENAI,
                cost_per_1k_tokens=0.03,  # GPT-4.1 pricing
                max_tokens_per_request=8192,
                supports_streaming=True,
                supports_vision=True,  # Confirmed: GPT-4.1 supports vision
                supports_embeddings=True,
                avg_response_time_ms=500
            ),
            AIProvider.FALLBACK: ProviderConfig(
                name=AIProvider.FALLBACK,
                cost_per_1k_tokens=0.0,
                max_tokens_per_request=1000,
                supports_streaming=False,
                supports_vision=False,
                supports_embeddings=False,
                avg_response_time_ms=10
            )
        }
    
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
        
        # Cost factor (lower cost = higher score)
        if config.cost_per_1k_tokens == 0:
            score += 30  # Prefer free providers
        else:
            score += 10 / config.cost_per_1k_tokens
            
        # Performance factor (faster = higher score)
        score += 1000 / config.avg_response_time_ms * 10
        
        # Reliability factor
        score += config.success_rate * 20
        
        # Priority factor
        if task.priority >= 8 and provider == AIProvider.AZURE_OPENAI:
            score += 20  # Use premium provider for high priority
            
        # Load balancing factor
        usage = self.usage_stats[provider]["requests"]
        if usage > 0:
            score -= min(usage / 100, 10)  # Penalize overused providers
            
        return score
    
    async def execute_with_fallback(self, task: AITask, execute_fn) -> Any:
        """Execute task with automatic fallback on failure"""
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
                
                # Mark provider as unhealthy if too many failures
                if self.usage_stats[provider]["errors"] > 5:
                    self.provider_health[provider] = False
                    asyncio.create_task(self._health_check(provider))
                    
        # All providers failed
        raise last_error or Exception("All AI providers failed")
    
    def _update_stats(self, provider: AIProvider, success: bool, 
                     response_time: float = 0, tokens: int = 0):
        """Update provider usage statistics"""
        stats = self.usage_stats[provider]
        stats["requests"] += 1
        stats["tokens"] += tokens
        
        if not success:
            stats["errors"] += 1
        else:
            # Update average response time
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
        """Get detailed usage report for cost tracking"""
        report = {
            "total_requests": sum(stats["requests"] for stats in self.usage_stats.values()),
            "total_tokens": sum(stats["tokens"] for stats in self.usage_stats.values()),
            "estimated_cost": 0.0,
            "provider_breakdown": {}
        }
        
        for provider, stats in self.usage_stats.items():
            config = self.providers[provider]
            cost = (stats["tokens"] / 1000) * config.cost_per_1k_tokens
            report["estimated_cost"] += cost
            
            report["provider_breakdown"][provider.value] = {
                "requests": stats["requests"],
                "tokens": stats["tokens"],
                "errors": stats["errors"],
                "cost": cost,
                "avg_response_time_ms": config.avg_response_time_ms,
                "health": self.provider_health[provider]
            }
            
        return report
    
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
        """Provide optimization recommendations based on usage"""
        recommendations = []
        
        # Check if we're over-relying on expensive providers
        azure_usage = self.usage_stats[AIProvider.AZURE_OPENAI]["requests"]
        total_usage = sum(stats["requests"] for stats in self.usage_stats.values())
        
        if total_usage > 0 and azure_usage / total_usage > 0.8:
            recommendations.append(
                "High Azure OpenAI usage detected. Consider implementing caching to reduce costs"
            )
            
        # Check error rates
        for provider, stats in self.usage_stats.items():
            if stats["requests"] > 10 and stats["errors"] / stats["requests"] > 0.1:
                recommendations.append(
                    f"{provider.value} has high error rate. Check configuration."
                )
                
        return recommendations


# Global router instance
ai_router = AIRouter()