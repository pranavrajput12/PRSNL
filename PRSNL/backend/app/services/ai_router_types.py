"""
Shared types and enums for AI routing system
This module contains common classes and enums used by both ai_router and ai_router_enhanced
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class AIProvider(Enum):
    AZURE_OPENAI = "azure_openai"
    FALLBACK = "fallback"


class TaskType(Enum):
    EMBEDDING = "embedding"
    TEXT_GENERATION = "text_generation"
    VISION = "vision"
    STREAMING = "streaming"


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class AITask:
    type: TaskType
    content: Any
    options: Dict[str, Any] = None
    priority: int = 5  # 1-10, higher is more important


@dataclass
class ProviderConfig:
    name: AIProvider
    max_tokens_per_request: int
    supports_streaming: bool
    supports_vision: bool
    supports_embeddings: bool
    avg_response_time_ms: float
    success_rate: float = 0.95


@dataclass
class RoutingDecision:
    """Enhanced routing decision with reasoning"""
    provider: AIProvider
    complexity: TaskComplexity
    reasoning: str
    confidence: float
    estimated_tokens: int
    recommended_model: str
    fallback_options: List[AIProvider]
    optimization_notes: List[str]