"""
Enhanced Caching Service with Redis 6.2.0 Client-Side Caching
Implements tracking-based invalidation for improved performance
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Union
import hashlib

import redis.asyncio as redis
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool

from app.config import settings
from app.services.performance_monitoring import profile_critical_section, track_custom_metric

logger = logging.getLogger(__name__)


class ClientSideCacheManager:
    """
    Manages client-side caching with Redis 6.2.0
    Uses tracking-based invalidation for automatic cache updates
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        cache_size: int = 10000,
        ttl_seconds: int = 3600
    ):
        self.redis_url = redis_url
        self.cache_size = cache_size
        self.default_ttl = ttl_seconds
        
        # Local cache storage
        self.local_cache: Dict[str, Any] = {}
        self.cache_metadata: Dict[str, datetime] = {}
        
        # Redis connections
        self.redis_client: Optional[Redis] = None
        self.tracking_client: Optional[Redis] = None
        self.invalidation_channel = "__redis__:invalidate"
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "invalidations": 0,
            "evictions": 0
        }
    
    async def connect(self):
        """Initialize Redis connections with client-side caching"""
        try:
            # Main connection pool
            pool = ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=50
            )
            
            # Primary client for operations
            self.redis_client = Redis(connection_pool=pool)
            
            # Enable client-side caching with TRACKING
            client_id = await self.redis_client.client_id()
            
            # Secondary client for invalidation messages
            self.tracking_client = Redis(connection_pool=pool)
            
            # Enable tracking on the main client
            await self.redis_client.execute_command(
                "CLIENT", "TRACKING", "ON",
                "REDIRECT", client_id,
                "BCAST"  # Broadcast mode for pattern-based invalidation
            )
            
            # Start invalidation listener
            asyncio.create_task(self._invalidation_listener())
            
            logger.info(f"Redis 6.2.0 client-side caching enabled (client_id: {client_id})")
            
        except Exception as e:
            logger.error(f"Failed to initialize client-side caching: {e}")
            # Fall back to regular Redis without client-side caching
            self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self):
        """Close Redis connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.tracking_client:
            await self.tracking_client.close()
    
    async def _invalidation_listener(self):
        """Listen for cache invalidation messages from Redis"""
        try:
            pubsub = self.tracking_client.pubsub()
            await pubsub.subscribe(self.invalidation_channel)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    # Handle invalidation
                    invalidated_keys = message.get("data", [])
                    if isinstance(invalidated_keys, list):
                        for key in invalidated_keys:
                            await self._invalidate_local(key)
                            
        except Exception as e:
            logger.error(f"Invalidation listener error: {e}")
    
    async def _invalidate_local(self, key: str):
        """Invalidate a key in the local cache"""
        if key in self.local_cache:
            del self.local_cache[key]
            del self.cache_metadata[key]
            self.stats["invalidations"] += 1
            logger.debug(f"Invalidated local cache key: {key}")
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache is full"""
        if len(self.local_cache) >= self.cache_size:
            # Find oldest entry
            oldest_key = min(self.cache_metadata.items(), key=lambda x: x[1])[0]
            del self.local_cache[oldest_key]
            del self.cache_metadata[oldest_key]
            self.stats["evictions"] += 1
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value with client-side caching
        First checks local cache, then Redis
        """
        # Check local cache first
        if key in self.local_cache:
            self.stats["hits"] += 1
            track_custom_metric("cache.client_side.hit", 1)
            return self.local_cache[key]
        
        # Miss - fetch from Redis
        self.stats["misses"] += 1
        track_custom_metric("cache.client_side.miss", 1)
        
        try:
            value = await self.redis_client.get(key)
            if value is not None:
                # Store in local cache
                self._evict_if_needed()
                self.local_cache[key] = value
                self.cache_metadata[key] = datetime.utcnow()
                
                # Enable tracking for this key
                await self.redis_client.execute_command("CLIENT", "CACHING", "YES")
                
            return value
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in both Redis and local cache"""
        try:
            ttl = ttl or self.default_ttl
            
            # Set in Redis
            success = await self.redis_client.setex(key, ttl, value)
            
            if success:
                # Update local cache
                self._evict_if_needed()
                self.local_cache[key] = value
                self.cache_metadata[key] = datetime.utcnow()
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from both Redis and local cache"""
        try:
            # Delete from Redis (will trigger invalidation)
            result = await self.redis_client.delete(key)
            
            # Also remove from local cache immediately
            await self._invalidate_local(key)
            
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys efficiently"""
        result = {}
        redis_keys = []
        
        # Check local cache first
        for key in keys:
            if key in self.local_cache:
                result[key] = self.local_cache[key]
                self.stats["hits"] += 1
            else:
                redis_keys.append(key)
                self.stats["misses"] += 1
        
        # Fetch missing keys from Redis
        if redis_keys:
            with profile_critical_section("redis_mget"):
                values = await self.redis_client.mget(redis_keys)
                
                for key, value in zip(redis_keys, values):
                    if value is not None:
                        result[key] = value
                        # Cache locally
                        self._evict_if_needed()
                        self.local_cache[key] = value
                        self.cache_metadata[key] = datetime.utcnow()
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / max(total_requests, 1)
        
        return {
            "total_requests": total_requests,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "invalidations": self.stats["invalidations"],
            "evictions": self.stats["evictions"],
            "local_cache_size": len(self.local_cache),
            "max_cache_size": self.cache_size
        }


class CacheKeyBuilder:
    """Helper class for building consistent cache keys"""
    
    @staticmethod
    def build_key(prefix: str, *args, **kwargs) -> str:
        """Build a cache key from prefix and arguments"""
        parts = [prefix]
        
        # Add positional arguments
        parts.extend(str(arg) for arg in args)
        
        # Add keyword arguments (sorted for consistency)
        if kwargs:
            kw_parts = [f"{k}:{v}" for k, v in sorted(kwargs.items())]
            parts.extend(kw_parts)
        
        return ":".join(parts)
    
    @staticmethod
    def build_pattern(prefix: str, pattern: str = "*") -> str:
        """Build a pattern for key matching"""
        return f"{prefix}:{pattern}"


def cache_async(
    prefix: str,
    ttl: int = 3600,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for async functions with client-side caching
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_builder: Optional custom key builder function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(prefix, *args, **kwargs)
            else:
                # Default key building
                key_parts = [prefix, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return json.loads(cached_value)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            await cache_manager.set(
                cache_key,
                json.dumps(result, default=str),
                ttl=ttl
            )
            
            return result
        
        return wrapper
    return decorator


# Global cache manager instance
cache_manager = ClientSideCacheManager(
    redis_url=settings.REDIS_URL,
    cache_size=settings.get("CLIENT_CACHE_SIZE", 10000),
    ttl_seconds=settings.get("CACHE_TTL", 3600)
)


# Convenience functions
async def get_cache_stats() -> Dict[str, Any]:
    """Get current cache statistics"""
    return cache_manager.get_stats()


async def invalidate_pattern(pattern: str) -> int:
    """Invalidate all keys matching a pattern"""
    if not cache_manager.redis_client:
        return 0
    
    keys = []
    async for key in cache_manager.redis_client.scan_iter(match=pattern):
        keys.append(key)
    
    if keys:
        return await cache_manager.redis_client.delete(*keys)
    
    return 0