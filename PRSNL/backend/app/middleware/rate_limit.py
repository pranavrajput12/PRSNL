"""
Rate limiting middleware for PRSNL API
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
import os

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute", "1000 per hour"],
    enabled=os.getenv("RATE_LIMITING_ENABLED", "true").lower() == "true"
)

# Define specific rate limits for different endpoints
capture_limiter = limiter.limit("10 per minute")
search_limiter = limiter.limit("30 per minute")
admin_limiter = limiter.limit("5 per minute")
webhook_limiter = limiter.limit("60 per minute")  # Higher for webhooks

# Aggressive throttling for high-cost embedding operations
embedding_limiter = limiter.limit("5 per 5 minutes")

# Moderate throttling for bulk operations
bulk_operation_limiter = limiter.limit("10 per minute")

# Strict throttling for mass embedding generation
mass_processing_limiter = limiter.limit("2 per 10 minutes")

# Capture endpoint throttling (extension uploads)
capture_throttle_limiter = limiter.limit("30 per minute")

# Search embedding throttling
semantic_search_limiter = limiter.limit("50 per minute")

# File upload throttling
file_upload_limiter = limiter.limit("15 per 5 minutes")

# OpenCLIP vision processing throttling
openclip_limiter = limiter.limit("30 per minute")

# Configure rate limit response
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    response = {
        "error": "rate_limit_exceeded",
        "message": f"Rate limit exceeded: {exc.detail}",
        "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None
    }
    return JSONResponse(
        status_code=429,
        content=response,
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"}
    )

# Export for use in main.py
__all__ = [
    'limiter', 
    'capture_limiter', 
    'search_limiter', 
    'admin_limiter',
    'webhook_limiter',
    'embedding_limiter',
    'bulk_operation_limiter',
    'mass_processing_limiter',
    'capture_throttle_limiter',
    'semantic_search_limiter',
    'file_upload_limiter',
    'openclip_limiter',
    'rate_limit_handler',
    'RateLimitExceeded'
]