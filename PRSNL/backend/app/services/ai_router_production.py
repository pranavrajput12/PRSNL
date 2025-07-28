"""
AI Router Service - Production version using Azure OpenAI only
Simplified for consistent performance and quality in production
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
from app.core.langfuse_client import langfuse_client

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    AZURE_OPENAI = "azure_openai"

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
    success_rate: float = 0.99

class AIRouter:
    """Production AI Router - Uses Azure OpenAI exclusively"""
    
    def __init__(self):
        self.provider = AIProvider.AZURE_OPENAI
        # Usage tracking now handled by Langfuse
        self.provider_config = ProviderConfig(
            name=AIProvider.AZURE_OPENAI,
            max_tokens_per_request=8192,
            supports_streaming=True,
            supports_vision=True,
            supports_embeddings=True,
            avg_response_time_ms=500
        )
    
    @observe(name="route_task_production")
    def route_task(self, task: AITask) -> AIProvider:
        """
        Route task - always returns Azure OpenAI in production
        """
        logger.info(f"Routing {task.type.value} task to {self.provider.value}")
        # Task metadata will be tracked automatically by Langfuse
        return self.provider
    
    @observe(name="execute_with_fallback")
    async def execute_with_fallback(self, task: AITask, execute_fn) -> Any:
        """
        Execute task with Azure OpenAI - no fallback for consistency
        """
        provider = self.route_task(task)
        
        try:
            start_time = time.time()
            result = await execute_fn(provider, task)
            
            # Update stats on success
            response_time = time.time() - start_time
            self._update_stats(success=True, response_time=response_time)
            
            return result
            
        except Exception as e:
            logger.error(f"Azure OpenAI failed: {e}")
            self._update_stats(success=False)
            raise e
    
    def _update_stats(self, success: bool, response_time: float = 0, tokens: int = 0):
        """Update usage statistics"""
        self.usage_stats["requests"] += 1
        self.usage_stats["tokens"] += tokens
        
        if not success:
            self.usage_stats["errors"] += 1
        else:
            # Update average response time
            current_avg = self.provider_config.avg_response_time_ms
            new_avg = (current_avg * 0.9 + response_time * 1000 * 0.1)
            self.provider_config.avg_response_time_ms = new_avg
            
        # Calculate cost
        if tokens > 0:
            cost = (tokens / 1000) * self.provider_config.cost_per_1k_tokens
            self.usage_stats["total_cost"] += cost
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get usage report for monitoring"""
        error_rate = 0
        if self.usage_stats["requests"] > 0:
            error_rate = self.usage_stats["errors"] / self.usage_stats["requests"]
            
        return {
            "provider": self.provider.value,
            "environment": "production",
            "total_requests": self.usage_stats["requests"],
            "total_tokens": self.usage_stats["tokens"],
            "total_errors": self.usage_stats["errors"],
            "error_rate": error_rate,
            "estimated_cost": self.usage_stats["total_cost"],
            "avg_response_time_ms": self.provider_config.avg_response_time_ms,
            "features": {
                "vision": self.provider_config.supports_vision,
                "streaming": self.provider_config.supports_streaming,
                "embeddings": self.provider_config.supports_embeddings
            }
        }
    
    async def stream_task(self, task: AITask):
        """Stream AI response using Azure OpenAI"""
        import json

        from app.config import settings
        
        try:
            # Stream from Azure OpenAI
            from openai import AsyncAzureOpenAI
            client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            stream = await client.chat.completions.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": task.content}],
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def validate_configuration(self) -> List[str]:
        """Validate that required configuration is present"""
        from app.config import settings
        errors = []
        
        if not settings.AZURE_OPENAI_API_KEY:
            errors.append("AZURE_OPENAI_API_KEY is not set")
        if not settings.AZURE_OPENAI_ENDPOINT:
            errors.append("AZURE_OPENAI_ENDPOINT is not set")
        if not settings.AZURE_OPENAI_DEPLOYMENT:
            errors.append("AZURE_OPENAI_DEPLOYMENT is not set")
                
        return errors


# Global router instance
ai_router = AIRouter()

# Validate on startup
config_errors = ai_router.validate_configuration()
if config_errors:
    logger.warning(f"AI Router configuration issues: {', '.join(config_errors)}")