"""
Caching service for PRSNL using Redis
"""
import json
import logging
from typing import Optional, Any, Union
from datetime import timedelta, datetime
import redis.asyncio as redis
from functools import wraps
import hashlib
import base64

logger = logging.getLogger(__name__)

class SecureJSONEncoder(json.JSONEncoder):
    """Secure JSON encoder that handles complex types without pickle"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return {'__datetime__': obj.isoformat()}
        elif isinstance(obj, bytes):
            return {'__bytes__': base64.b64encode(obj).decode('utf-8')}
        elif hasattr(obj, '__dict__'):
            # For custom objects, only serialize basic attributes
            return {'__object__': obj.__class__.__name__, '__data__': {
                k: v for k, v in obj.__dict__.items() 
                if isinstance(v, (str, int, float, bool, list, dict, type(None)))
            }}
        # For unsupported types, convert to string representation
        return {'__string__': str(obj)}

def secure_json_decode(obj):
    """Secure JSON decoder that reconstructs safe objects"""
    if isinstance(obj, dict):
        if '__datetime__' in obj:
            return datetime.fromisoformat(obj['__datetime__'])
        elif '__bytes__' in obj:
            return base64.b64decode(obj['__bytes__'].encode('utf-8'))
        elif '__string__' in obj:
            return obj['__string__']
        elif '__object__' in obj:
            # Don't reconstruct arbitrary objects for security - return dict instead
            return obj['__data__']
    return obj

class CacheService:
    """Redis-based caching service"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = True
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle encoding/decoding
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            self.enabled = False
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            value = await self.redis_client.get(key)
            if value:
                # Secure JSON deserialization only
                try:
                    return json.loads(value, object_hook=secure_json_decode)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to deserialize cached value for key {key}: {e}")
                    # Remove corrupted cache entry
                    await self.redis_client.delete(key)
                    return None
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache with optional expiration"""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            # Secure JSON serialization only
            try:
                serialized = json.dumps(value, cls=SecureJSONEncoder)
            except (TypeError, ValueError) as e:
                logger.warning(f"Failed to serialize value for caching: {e}")
                return False
            
            # Convert timedelta to seconds
            if isinstance(expire, timedelta):
                expire = int(expire.total_seconds())
                
            await self.redis_client.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.enabled or not self.redis_client:
            return 0
            
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments"""
        parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                parts.append(str(arg))
            else:
                # Hash complex objects
                parts.append(hashlib.sha256(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                parts.append(f"{k}:{v}")
            else:
                parts.append(f"{k}:{hashlib.sha256(str(v).encode()).hexdigest()[:8]}")
        
        return ":".join(parts)


# Cache key prefixes
class CacheKeys:
    """Cache key prefixes for different data types"""
    ITEM = "item"
    SEARCH = "search"
    TAGS = "tags"
    TIMELINE = "timeline"
    SIMILAR = "similar"
    STATS = "stats"
    USER = "user"


# Cache decorators
def cache_result(
    prefix: str, 
    expire: Union[int, timedelta] = 3600,
    key_func: Optional[callable] = None
):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache service from first argument if it's self
            cache_service = None
            if args and hasattr(args[0], 'cache'):
                cache_service = args[0].cache
            
            if not cache_service or not cache_service.enabled:
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Skip 'self' argument for methods
                cache_args = args[1:] if args and hasattr(args[0], 'cache') else args
                cache_key = cache_service.make_key(prefix, *cache_args, **kwargs)
            
            # Try to get from cache
            cached = await cache_service.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_service.set(cache_key, result, expire)
            logger.debug(f"Cached result for {cache_key}")
            
            return result
        return wrapper
    return decorator


def invalidate_cache(patterns: list[str]):
    """Decorator to invalidate cache patterns after function execution"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute function
            result = await func(*args, **kwargs)
            
            # Get cache service from first argument if it's self
            if args and hasattr(args[0], 'cache'):
                cache_service = args[0].cache
                if cache_service and cache_service.enabled:
                    for pattern in patterns:
                        await cache_service.clear_pattern(pattern)
                        logger.debug(f"Invalidated cache pattern: {pattern}")
            
            return result
        return wrapper
    return decorator


# Import settings at module level
from app.config import settings

# Global cache instance
cache_service = CacheService(redis_url=settings.REDIS_URL)