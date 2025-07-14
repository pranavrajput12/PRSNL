"""
Agent-Specific Retry Strategies

Phase 2: Intelligent retry mechanisms with agent-specific strategies,
exponential backoff, circuit breakers, and adaptive retry logic.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from celery import Task
from celery.exceptions import Retry

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Available retry strategies"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"
    ADAPTIVE = "adaptive"
    CIRCUIT_BREAKER = "circuit_breaker"
    NO_RETRY = "no_retry"


class FailureType(Enum):
    """Types of failures for different retry strategies"""
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AI_SERVICE_ERROR = "ai_service_error"
    DATABASE_ERROR = "database_error"
    MEMORY_ERROR = "memory_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    strategy: RetryStrategy
    max_retries: int
    base_delay: float  # seconds
    max_delay: float  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60  # seconds
    failure_types: List[FailureType] = None


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    failure_type: FailureType
    error_message: str
    timestamp: datetime
    delay_used: float
    strategy_applied: RetryStrategy


class BaseRetryStrategy(ABC):
    """Base class for retry strategies"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempts: List[RetryAttempt] = []
    
    @abstractmethod
    def should_retry(self, attempt_number: int, failure_type: FailureType, error: Exception) -> bool:
        """Determine if we should retry based on the failure"""
        pass
    
    @abstractmethod
    def calculate_delay(self, attempt_number: int, failure_type: FailureType) -> float:
        """Calculate delay before next retry"""
        pass
    
    def record_attempt(self, attempt_number: int, failure_type: FailureType, error: Exception, delay: float):
        """Record a retry attempt"""
        attempt = RetryAttempt(
            attempt_number=attempt_number,
            failure_type=failure_type,
            error_message=str(error),
            timestamp=datetime.utcnow(),
            delay_used=delay,
            strategy_applied=self.config.strategy
        )
        self.attempts.append(attempt)


class ExponentialBackoffStrategy(BaseRetryStrategy):
    """Exponential backoff with jitter"""
    
    def should_retry(self, attempt_number: int, failure_type: FailureType, error: Exception) -> bool:
        if attempt_number >= self.config.max_retries:
            return False
        
        # Don't retry validation errors
        if failure_type == FailureType.VALIDATION_ERROR:
            return False
        
        # Check if this failure type is retryable
        if self.config.failure_types and failure_type not in self.config.failure_types:
            return False
        
        return True
    
    def calculate_delay(self, attempt_number: int, failure_type: FailureType) -> float:
        # Base exponential delay
        delay = self.config.base_delay * (self.config.exponential_base ** attempt_number)
        
        # Apply jitter if enabled
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Special handling for rate limits - longer delays
        if failure_type == FailureType.RATE_LIMIT:
            delay *= 2
        
        return delay


class AdaptiveRetryStrategy(BaseRetryStrategy):
    """Adaptive retry strategy that learns from failure patterns"""
    
    def __init__(self, config: RetryConfig):
        super().__init__(config)
        self.failure_history: Dict[FailureType, List[datetime]] = {}
        self.success_after_retry: Dict[FailureType, int] = {}
    
    def should_retry(self, attempt_number: int, failure_type: FailureType, error: Exception) -> bool:
        if attempt_number >= self.config.max_retries:
            return False
        
        # Never retry validation errors
        if failure_type == FailureType.VALIDATION_ERROR:
            return False
        
        # Analyze recent failure patterns
        recent_failures = self._get_recent_failures(failure_type, minutes=30)
        
        # If too many recent failures of same type, reduce retry attempts
        if len(recent_failures) > 10:
            return attempt_number < max(1, self.config.max_retries // 2)
        
        # Check historical success rate after retries
        success_rate = self._get_retry_success_rate(failure_type)
        if success_rate < 0.2:  # Less than 20% success rate
            return attempt_number < 2
        
        return True
    
    def calculate_delay(self, attempt_number: int, failure_type: FailureType) -> float:
        # Base delay from config
        delay = self.config.base_delay
        
        # Adjust based on failure frequency
        recent_failures = self._get_recent_failures(failure_type, minutes=10)
        if len(recent_failures) > 5:
            delay *= 2  # Double delay if many recent failures
        
        # Adaptive exponential backoff
        delay *= (1.5 ** attempt_number)
        
        # Apply jitter
        if self.config.jitter:
            import random
            delay *= (0.7 + random.random() * 0.6)  # 70-130% of calculated delay
        
        return min(delay, self.config.max_delay)
    
    def _get_recent_failures(self, failure_type: FailureType, minutes: int) -> List[datetime]:
        """Get recent failures of a specific type"""
        if failure_type not in self.failure_history:
            return []
        
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [ts for ts in self.failure_history[failure_type] if ts > cutoff]
    
    def _get_retry_success_rate(self, failure_type: FailureType) -> float:
        """Get historical success rate for retries of this failure type"""
        if failure_type not in self.success_after_retry:
            return 0.5  # Default neutral success rate
        
        total_attempts = len(self.failure_history.get(failure_type, []))
        if total_attempts == 0:
            return 0.5
        
        successes = self.success_after_retry[failure_type]
        return successes / total_attempts
    
    def record_failure(self, failure_type: FailureType):
        """Record a failure for learning"""
        if failure_type not in self.failure_history:
            self.failure_history[failure_type] = []
        self.failure_history[failure_type].append(datetime.utcnow())
    
    def record_success_after_retry(self, failure_type: FailureType):
        """Record a successful retry for learning"""
        if failure_type not in self.success_after_retry:
            self.success_after_retry[failure_type] = 0
        self.success_after_retry[failure_type] += 1


class CircuitBreakerStrategy(BaseRetryStrategy):
    """Circuit breaker pattern for failing services"""
    
    def __init__(self, config: RetryConfig):
        super().__init__(config)
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.circuit_open = False
    
    def should_retry(self, attempt_number: int, failure_type: FailureType, error: Exception) -> bool:
        # Check if circuit is open
        if self.circuit_open:
            # Check if timeout period has passed
            if self.last_failure_time and \
               (datetime.utcnow() - self.last_failure_time).seconds > self.config.circuit_breaker_timeout:
                self.circuit_open = False
                self.failure_count = 0
            else:
                return False
        
        if attempt_number >= self.config.max_retries:
            return False
        
        # Don't retry validation errors
        if failure_type == FailureType.VALIDATION_ERROR:
            return False
        
        return True
    
    def calculate_delay(self, attempt_number: int, failure_type: FailureType) -> float:
        # Linear backoff for circuit breaker
        delay = self.config.base_delay * (attempt_number + 1)
        
        # Add jitter
        if self.config.jitter:
            import random
            delay *= (0.8 + random.random() * 0.4)  # 80-120% of calculated delay
        
        return min(delay, self.config.max_delay)
    
    def record_failure(self):
        """Record a failure and check if circuit should open"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.config.circuit_breaker_threshold:
            self.circuit_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def record_success(self):
        """Record a success and reset failure count"""
        self.failure_count = 0
        self.circuit_open = False


class RetryStrategyFactory:
    """Factory for creating retry strategies"""
    
    _strategies = {
        RetryStrategy.EXPONENTIAL_BACKOFF: ExponentialBackoffStrategy,
        RetryStrategy.ADAPTIVE: AdaptiveRetryStrategy,
        RetryStrategy.CIRCUIT_BREAKER: CircuitBreakerStrategy,
    }
    
    @classmethod
    def create_strategy(cls, config: RetryConfig) -> BaseRetryStrategy:
        """Create a retry strategy based on configuration"""
        strategy_class = cls._strategies.get(config.strategy)
        if not strategy_class:
            raise ValueError(f"Unknown retry strategy: {config.strategy}")
        
        return strategy_class(config)


class AgentRetryMixin:
    """Mixin for Celery tasks with intelligent retry logic"""
    
    # Agent-specific retry configurations
    AGENT_RETRY_CONFIGS = {
        "conversation_intelligence": RetryConfig(
            strategy=RetryStrategy.ADAPTIVE,
            max_retries=3,
            base_delay=30.0,
            max_delay=300.0,
            failure_types=[
                FailureType.AI_SERVICE_ERROR,
                FailureType.NETWORK_ERROR,
                FailureType.TIMEOUT
            ]
        ),
        "knowledge_graph": RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=5,
            base_delay=10.0,
            max_delay=120.0,
            failure_types=[
                FailureType.DATABASE_ERROR,
                FailureType.NETWORK_ERROR,
                FailureType.AI_SERVICE_ERROR
            ]
        ),
        "content_analysis": RetryConfig(
            strategy=RetryStrategy.CIRCUIT_BREAKER,
            max_retries=3,
            base_delay=20.0,
            max_delay=180.0,
            circuit_breaker_threshold=5,
            circuit_breaker_timeout=120,
            failure_types=[
                FailureType.AI_SERVICE_ERROR,
                FailureType.RATE_LIMIT,
                FailureType.TIMEOUT
            ]
        ),
        "pattern_detection": RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=4,
            base_delay=15.0,
            max_delay=240.0,
            failure_types=[
                FailureType.AI_SERVICE_ERROR,
                FailureType.MEMORY_ERROR,
                FailureType.DATABASE_ERROR
            ]
        ),
        "file_processing": RetryConfig(
            strategy=RetryStrategy.ADAPTIVE,
            max_retries=5,
            base_delay=5.0,
            max_delay=60.0,
            failure_types=[
                FailureType.NETWORK_ERROR,
                FailureType.TIMEOUT,
                FailureType.MEMORY_ERROR
            ]
        ),
        "media_processing": RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            max_retries=3,
            base_delay=60.0,  # Longer delays for heavy processing
            max_delay=600.0,
            failure_types=[
                FailureType.MEMORY_ERROR,
                FailureType.TIMEOUT,
                FailureType.UNKNOWN_ERROR
            ]
        ),
        "default": RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=3,
            base_delay=10.0,
            max_delay=120.0,
            failure_types=[
                FailureType.NETWORK_ERROR,
                FailureType.TIMEOUT,
                FailureType.UNKNOWN_ERROR
            ]
        )
    }
    
    def __init__(self):
        self.retry_strategies: Dict[str, BaseRetryStrategy] = {}
    
    def get_retry_strategy(self, agent_type: str) -> BaseRetryStrategy:
        """Get or create retry strategy for agent type"""
        if agent_type not in self.retry_strategies:
            config = self.AGENT_RETRY_CONFIGS.get(agent_type, self.AGENT_RETRY_CONFIGS["default"])
            self.retry_strategies[agent_type] = RetryStrategyFactory.create_strategy(config)
        
        return self.retry_strategies[agent_type]
    
    def classify_error(self, error: Exception) -> FailureType:
        """Classify error type for retry strategy"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ["connection", "network", "dns", "timeout"]):
            if "timeout" in error_str:
                return FailureType.TIMEOUT
            return FailureType.NETWORK_ERROR
        
        # Rate limiting
        if any(keyword in error_str for keyword in ["rate limit", "too many requests", "quota exceeded"]):
            return FailureType.RATE_LIMIT
        
        # AI service errors
        if any(keyword in error_str for keyword in ["openai", "azure", "ai service", "model"]):
            return FailureType.AI_SERVICE_ERROR
        
        # Database errors
        if any(keyword in error_str for keyword in ["database", "postgres", "sql", "connection pool"]):
            return FailureType.DATABASE_ERROR
        
        # Memory errors
        if any(keyword in error_str for keyword in ["memory", "out of memory", "memoryerror"]):
            return FailureType.MEMORY_ERROR
        
        # Validation errors
        if any(keyword in error_type for keyword in ["validation", "pydantic", "schema"]):
            return FailureType.VALIDATION_ERROR
        
        return FailureType.UNKNOWN_ERROR
    
    def intelligent_retry(self, agent_type: str, error: Exception, attempt_number: int) -> Tuple[bool, float]:
        """
        Determine if task should retry and calculate delay.
        
        Returns:
            Tuple of (should_retry, delay_seconds)
        """
        try:
            strategy = self.get_retry_strategy(agent_type)
            failure_type = self.classify_error(error)
            
            # Check if we should retry
            should_retry = strategy.should_retry(attempt_number, failure_type, error)
            
            if not should_retry:
                logger.info(f"Not retrying {agent_type} task after {attempt_number} attempts: {failure_type}")
                return False, 0.0
            
            # Calculate delay
            delay = strategy.calculate_delay(attempt_number, failure_type)
            
            # Record the attempt
            strategy.record_attempt(attempt_number, failure_type, error, delay)
            
            # Special handling for adaptive and circuit breaker strategies
            if isinstance(strategy, AdaptiveRetryStrategy):
                strategy.record_failure(failure_type)
            elif isinstance(strategy, CircuitBreakerStrategy):
                strategy.record_failure()
            
            logger.info(f"Retrying {agent_type} task (attempt {attempt_number + 1}) after {delay:.1f}s delay: {failure_type}")
            
            return True, delay
            
        except Exception as e:
            logger.error(f"Error in intelligent retry logic: {e}")
            # Fallback to simple retry
            return attempt_number < 3, min(10.0 * (2 ** attempt_number), 60.0)
    
    def record_retry_success(self, agent_type: str, failure_type: FailureType):
        """Record successful retry for learning"""
        strategy = self.get_retry_strategy(agent_type)
        
        if isinstance(strategy, AdaptiveRetryStrategy):
            strategy.record_success_after_retry(failure_type)
        elif isinstance(strategy, CircuitBreakerStrategy):
            strategy.record_success()


class IntelligentRetryTask(Task, AgentRetryMixin):
    """
    Enhanced Celery task base class with intelligent retry capabilities.
    
    Usage:
        @celery_app.task(base=IntelligentRetryTask, bind=True, agent_type="content_analysis")
        def my_task(self, ...):
            # Task implementation
    """
    
    def __init__(self):
        super().__init__()
        AgentRetryMixin.__init__(self)
    
    def retry(self, args=None, kwargs=None, exc=None, throw=True, eta=None, countdown=None, max_retries=None, **options):
        """Override retry method to use intelligent retry logic"""
        
        # Get agent type from task options or default
        agent_type = getattr(self, 'agent_type', 'default')
        
        # Use intelligent retry logic
        should_retry, delay = self.intelligent_retry(agent_type, exc, self.request.retries)
        
        if not should_retry:
            # Don't retry - let the task fail
            if throw:
                raise exc
            return
        
        # Use calculated delay
        if countdown is None:
            countdown = delay
        
        # Call parent retry method
        super().retry(
            args=args,
            kwargs=kwargs,
            exc=exc,
            throw=throw,
            eta=eta,
            countdown=countdown,
            max_retries=max_retries,
            **options
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle successful task completion"""
        super().on_success(retval, task_id, args, kwargs)
        
        # Record success if this was a retry
        if self.request.retries > 0:
            agent_type = getattr(self, 'agent_type', 'default')
            # We don't know the exact failure type here, but record general success
            self.record_retry_success(agent_type, FailureType.UNKNOWN_ERROR)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        super().on_failure(exc, task_id, args, kwargs, einfo)
        
        agent_type = getattr(self, 'agent_type', 'default')
        failure_type = self.classify_error(exc)
        
        logger.error(f"Task {task_id} ({agent_type}) failed permanently: {failure_type} - {exc}")


# Utility function for applying retry strategies to existing tasks
def apply_retry_strategy(task_func: Callable, agent_type: str):
    """
    Decorator to apply retry strategy to existing task functions.
    
    Usage:
        @apply_retry_strategy(agent_type="content_analysis")
        @celery_app.task
        def my_task(...):
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            task_instance = func.__self__ if hasattr(func, '__self__') else None
            
            if isinstance(task_instance, Task):
                # Add retry mixin capabilities
                if not hasattr(task_instance, 'intelligent_retry'):
                    task_instance.__class__ = type(
                        task_instance.__class__.__name__,
                        (task_instance.__class__, AgentRetryMixin),
                        {}
                    )
                    AgentRetryMixin.__init__(task_instance)
                
                # Set agent type
                task_instance.agent_type = agent_type
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example usage configurations for different scenarios
SCENARIO_CONFIGS = {
    "high_availability": {
        "conversation_intelligence": RetryConfig(
            strategy=RetryStrategy.ADAPTIVE,
            max_retries=5,
            base_delay=10.0,
            max_delay=120.0
        ),
        "knowledge_graph": RetryConfig(
            strategy=RetryStrategy.CIRCUIT_BREAKER,
            max_retries=3,
            base_delay=30.0,
            max_delay=300.0,
            circuit_breaker_threshold=3
        )
    },
    "cost_optimized": {
        "content_analysis": RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            max_retries=2,
            base_delay=30.0,
            max_delay=180.0
        ),
        "ai_processing": RetryConfig(
            strategy=RetryStrategy.FIXED_DELAY,
            max_retries=1,
            base_delay=60.0,
            max_delay=60.0
        )
    },
    "performance_focused": {
        "file_processing": RetryConfig(
            strategy=RetryStrategy.ADAPTIVE,
            max_retries=6,
            base_delay=5.0,
            max_delay=30.0
        ),
        "media_processing": RetryConfig(
            strategy=RetryStrategy.LINEAR_BACKOFF,
            max_retries=4,
            base_delay=15.0,
            max_delay=120.0
        )
    }
}