"""
Performance Monitoring Service using Sentry SDK 2.33.0
Provides advanced profiling and performance insights
"""
import time
import functools
from typing import Any, Callable, Dict, Optional
from contextlib import contextmanager
import sentry_sdk
from sentry_sdk import start_transaction, set_measurement
from app.core.sentry import set_transaction_tag
from app.core.logger import get_logger

logger = get_logger(__name__)


class PerformanceMonitor:
    """Advanced performance monitoring with Sentry 2.33.0 profiling"""
    
    @staticmethod
    @contextmanager
    def profile_operation(operation_name: str, operation_type: str = "task", tags: Optional[Dict[str, str]] = None):
        """
        Context manager for profiling operations with Sentry 2.33.0
        
        Example:
            with PerformanceMonitor.profile_operation("document_extraction", "ai_task", {"model": "gpt-4"}):
                # Your operation here
                pass
        """
        transaction = start_transaction(op=operation_type, name=operation_name)
        
        # Add custom tags for better filtering in Sentry
        if tags:
            for key, value in tags.items():
                transaction.set_tag(key, value)
        
        # Add performance metadata
        transaction.set_tag("monitor.version", "2.33.0")
        transaction.set_tag("profiling.enabled", "true")
        
        start_time = time.perf_counter()
        
        try:
            with transaction:
                yield transaction
        finally:
            # Record performance metrics
            duration = time.perf_counter() - start_time
            set_measurement("operation.duration", duration, "millisecond")
            
            # Log performance data
            logger.info(f"Operation '{operation_name}' completed in {duration:.2f}ms")
    
    @staticmethod
    def profile_endpoint(transaction_name: Optional[str] = None):
        """
        Decorator for profiling FastAPI endpoints with enhanced metrics
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                name = transaction_name or f"endpoint.{func.__name__}"
                
                with PerformanceMonitor.profile_operation(
                    name, 
                    "http.server",
                    {"endpoint": func.__name__, "async": "true"}
                ):
                    return await func(*args, **kwargs)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                name = transaction_name or f"endpoint.{func.__name__}"
                
                with PerformanceMonitor.profile_operation(
                    name,
                    "http.server", 
                    {"endpoint": func.__name__, "async": "false"}
                ):
                    return func(*args, **kwargs)
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    @staticmethod
    def profile_database_query(query_type: str = "select"):
        """
        Decorator for profiling database operations
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with PerformanceMonitor.profile_operation(
                    f"db.{query_type}",
                    "db.query",
                    {"query.type": query_type, "db.system": "postgresql"}
                ):
                    return await func(*args, **kwargs)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with PerformanceMonitor.profile_operation(
                    f"db.{query_type}",
                    "db.query",
                    {"query.type": query_type, "db.system": "postgresql"}
                ):
                    return func(*args, **kwargs)
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    @staticmethod
    def profile_ai_operation(model: str, operation: str = "inference"):
        """
        Decorator for profiling AI/ML operations with model-specific metrics
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with PerformanceMonitor.profile_operation(
                    f"ai.{operation}",
                    "ai.operation",
                    {
                        "ai.model": model,
                        "ai.operation": operation,
                        "ai.provider": "azure_openai"
                    }
                ) as transaction:
                    # Track token usage if available
                    result = await func(*args, **kwargs)
                    
                    # Extract token metrics if present
                    if hasattr(result, "usage"):
                        set_measurement("ai.tokens.prompt", result.usage.prompt_tokens, "token")
                        set_measurement("ai.tokens.completion", result.usage.completion_tokens, "token")
                        set_measurement("ai.tokens.total", result.usage.total_tokens, "token")
                    
                    return result
            
            return async_wrapper
        
        return decorator
    
    @staticmethod
    def track_memory_usage():
        """
        Track memory usage for the current transaction
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            set_measurement("memory.rss", memory_info.rss / 1024 / 1024, "megabyte")
            set_measurement("memory.vms", memory_info.vms / 1024 / 1024, "megabyte")
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=0.1)
            set_measurement("cpu.usage", cpu_percent, "percent")
            
        except ImportError:
            logger.warning("psutil not installed, memory tracking disabled")
        except Exception as e:
            logger.error(f"Error tracking memory usage: {e}")
    
    @staticmethod
    def create_performance_middleware():
        """
        Create FastAPI middleware for automatic performance monitoring
        """
        from fastapi import Request
        from starlette.middleware.base import BaseHTTPMiddleware
        
        class PerformanceMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Skip health checks and static files
                if request.url.path in ["/health", "/docs", "/openapi.json"]:
                    return await call_next(request)
                
                # Start performance monitoring
                with PerformanceMonitor.profile_operation(
                    f"{request.method} {request.url.path}",
                    "http.server",
                    {
                        "http.method": request.method,
                        "http.path": request.url.path,
                        "http.host": request.url.hostname or "localhost"
                    }
                ):
                    # Track memory before request
                    PerformanceMonitor.track_memory_usage()
                    
                    # Process request
                    response = await call_next(request)
                    
                    # Track response metrics
                    set_measurement("http.response.status_code", response.status_code, "none")
                    
                    # Track memory after request
                    PerformanceMonitor.track_memory_usage()
                    
                    return response
        
        return PerformanceMiddleware


# Convenience functions for common profiling scenarios
def profile_critical_section(name: str, **tags):
    """
    Profile a critical section of code
    Usage:
        with profile_critical_section("data_processing", data_size=1000):
            # Your code here
    """
    return PerformanceMonitor.profile_operation(name, "task", tags)


def track_custom_metric(metric_name: str, value: float, unit: str = "none"):
    """
    Track a custom metric in the current transaction
    """
    set_measurement(metric_name, value, unit)


# Export commonly used decorators
profile_endpoint = PerformanceMonitor.profile_endpoint
profile_database = PerformanceMonitor.profile_database_query
profile_ai = PerformanceMonitor.profile_ai_operation