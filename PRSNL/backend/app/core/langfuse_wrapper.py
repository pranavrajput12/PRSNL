"""
Langfuse wrapper to handle compatibility issues with OpenTelemetry

This wrapper provides a safe way to use langfuse decorators that handles
the get_tracer() attributes parameter error gracefully.
"""

import functools
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Try to import langfuse, but handle if it's not available or has issues
try:
    from langfuse import observe as _langfuse_observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.warning("Langfuse not available - observability decorators will be no-ops")
except Exception as e:
    LANGFUSE_AVAILABLE = False
    logger.error(f"Error importing langfuse: {e}")


def observe(name: Optional[str] = None, **kwargs) -> Callable:
    """
    Safe wrapper around langfuse observe decorator.
    
    If langfuse is available and working, uses the real decorator.
    Otherwise, returns a no-op decorator that just passes through the function.
    
    This handles the get_tracer() attributes parameter error by catching
    any exceptions during both decoration and runtime execution.
    """
    def decorator(func: Callable) -> Callable:
        if not LANGFUSE_AVAILABLE:
            return func
            
        try:
            # Try to apply the langfuse decorator
            decorated_func = _langfuse_observe(name=name, **kwargs)(func)
            
            # Wrap the decorated function to catch runtime errors
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await decorated_func(*args, **kwargs)
                except TypeError as e:
                    if "get_tracer() got an unexpected keyword argument 'attributes'" in str(e):
                        logger.debug(f"Langfuse runtime error for {name}, falling back to original function")
                        return await func(*args, **kwargs)
                    raise
                except Exception as e:
                    # If it's a known langfuse/opentelemetry issue, fall back
                    error_msg = str(e)
                    if "get_tracer" in error_msg and "attributes" in error_msg:
                        logger.debug(f"Langfuse runtime compatibility error for {name}, falling back to original function")
                        return await func(*args, **kwargs)
                    raise
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return decorated_func(*args, **kwargs)
                except TypeError as e:
                    if "get_tracer() got an unexpected keyword argument 'attributes'" in str(e):
                        logger.debug(f"Langfuse runtime error for {name}, falling back to original function")
                        return func(*args, **kwargs)
                    raise
                except Exception as e:
                    # If it's a known langfuse/opentelemetry issue, fall back
                    error_msg = str(e)
                    if "get_tracer" in error_msg and "attributes" in error_msg:
                        logger.debug(f"Langfuse runtime compatibility error for {name}, falling back to original function")
                        return func(*args, **kwargs)
                    raise
            
            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
                
        except TypeError as e:
            # Handle the specific get_tracer() error during decoration
            if "get_tracer() got an unexpected keyword argument 'attributes'" in str(e):
                logger.debug(f"Langfuse decorator incompatible with OpenTelemetry version for {name}")
                return func
            # Re-raise other TypeErrors
            raise
        except Exception as e:
            # Log other exceptions and return the original function
            logger.error(f"Error applying langfuse observe decorator to {name}: {e}")
            return func
    
    return decorator


# For backward compatibility, provide a direct alternative
def safe_observe(name: Optional[str] = None, **kwargs) -> Callable:
    """Alias for observe() for clarity"""
    return observe(name=name, **kwargs)