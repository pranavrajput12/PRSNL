"""
AI Service wrapper for PRSNL
Provides a simple interface to Azure OpenAI for the voice service
"""

import logging
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI
# from langfuse import observe  # Temporarily disabled due to get_tracer error

from app.config import settings
# from app.core.langfuse_client import langfuse_client  # Temporarily disabled due to get_tracer error

logger = logging.getLogger(__name__)


class AIService:
    """Simple AI service wrapper for Azure OpenAI"""
    
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        
    # @observe(name="generate_response")  # Temporarily disabled due to get_tracer error
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a response using Azure OpenAI
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            model: Optional model override
            
        Returns:
            Dictionary with 'content' and metadata
        """
        try:
            # Model info will be tracked automatically by Langfuse through Azure OpenAI integration
            
            response = self.client.chat.completions.create(
                model=model or self.deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            raise
            
    async def complete(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Simple completion interface
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.generate_response(messages, **kwargs)
        return response["content"]