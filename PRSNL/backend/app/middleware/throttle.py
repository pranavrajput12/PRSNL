"""
FastAPI-Throttle configuration for endpoint-specific rate limiting.
Provides protection against runaway uploads and resource-intensive operations.
"""

from fastapi_throttle import RateLimiter

# Aggressive throttling for high-cost embedding operations
# These endpoints trigger expensive AI model calls
embedding_limiter = RateLimiter(
    times=5,      # 5 requests
    seconds=300   # per 5 minutes (300 seconds)
)

# Moderate throttling for bulk operations
# File uploads and batch processing
bulk_operation_limiter = RateLimiter(
    times=10,     # 10 requests  
    seconds=60    # per minute
)

# Strict throttling for mass embedding generation
# Admin-level operations that process many items
mass_processing_limiter = RateLimiter(
    times=2,      # 2 requests
    seconds=600   # per 10 minutes
)

# Capture endpoint throttling (extension uploads)
# Protects against runaway extension behavior
capture_throttle_limiter = RateLimiter(
    times=30,     # 30 captures
    seconds=60    # per minute
)

# Search embedding throttling
# Semantic search operations
semantic_search_limiter = RateLimiter(
    times=50,     # 50 searches
    seconds=60    # per minute
)

# File upload throttling
# Individual file uploads from extensions
file_upload_limiter = RateLimiter(
    times=15,     # 15 files
    seconds=300   # per 5 minutes
)