"""
Redis-based caching service for external API calls and expensive operations.

This service provides system-wide caching for:
- GitHub API responses 
- Stack Overflow API calls
- Documentation site data
- Rich preview generation
- Any other external API data

Features:
- TTL-based expiration
- ETag support for conditional requests
- Rate limit protection
- Offline fallback support
- Automatic cache invalidation
"""

import os
import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import redis.asyncio as aioredis
import logging

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for external API responses."""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.default_ttl = 3600  # 1 hour default
        self.long_ttl = 86400    # 24 hours for stable data
        self.short_ttl = 300     # 5 minutes for volatile data
        
    async def connect(self):
        """Initialize Redis connection."""
        if not self.redis:
            try:
                self.redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                await self.redis.ping()
                logger.info(f"✅ Redis connected: {self.redis_url}")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {e}")
                self.redis = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    def _generate_cache_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """Generate a consistent cache key."""
        # Include kwargs in key for parameter-specific caching
        key_data = f"{prefix}:{identifier}"
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = "&".join(f"{k}={v}" for k, v in sorted_kwargs)
            key_data += f":{kwargs_str}"
        
        # Hash long keys to prevent Redis key length issues
        if len(key_data) > 200:
            key_hash = hashlib.sha256(key_data.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_data.replace(" ", "_").replace(":", "_")
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data by key."""
        if not self.redis:
            await self.connect()
            if not self.redis:
                return None
        
        try:
            cached_data = await self.redis.get(key)
            if cached_data:
                data = json.loads(cached_data)
                
                # Check if data has expired (additional check)
                if 'expires_at' in data:
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    if datetime.utcnow() > expires_at:
                        await self.delete(key)
                        return None
                
                logger.debug(f"🎯 Cache HIT: {key}")
                return data.get('value')
            
            logger.debug(f"❌ Cache MISS: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Dict[str, Any], 
        ttl: Optional[int] = None,
        etag: Optional[str] = None
    ) -> bool:
        """Set cached data with TTL."""
        if not self.redis:
            await self.connect()
            if not self.redis:
                return False
        
        try:
            ttl = ttl or self.default_ttl
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            cache_data = {
                'value': value,
                'cached_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at.isoformat(),
                'etag': etag,
                'ttl': ttl
            }
            
            await self.redis.setex(
                key, 
                ttl, 
                json.dumps(cache_data, default=str)
            )
            
            logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached data."""
        if not self.redis:
            return False
        
        try:
            result = await self.redis.delete(key)
            logger.debug(f"🗑️ Cache DELETE: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def get_or_set(
        self,
        key: str,
        fetch_func: Callable,
        ttl: Optional[int] = None,
        force_refresh: bool = False,
        **fetch_kwargs
    ) -> Optional[Dict[str, Any]]:
        """Get from cache or fetch and cache if not found."""
        if not force_refresh:
            cached = await self.get(key)
            if cached is not None:
                return cached
        
        # Fetch fresh data
        try:
            fresh_data = await fetch_func(**fetch_kwargs)
            if fresh_data:
                await self.set(key, fresh_data, ttl)
                return fresh_data
        except Exception as e:
            logger.error(f"Fetch function failed for {key}: {e}")
            
            # Try to return stale cache if available
            if not force_refresh:
                stale_data = await self.get(key)
                if stale_data:
                    logger.info(f"🔄 Returning stale cache for {key}")
                    return stale_data
        
        return None
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        if not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info(f"🗑️ Invalidated {deleted} keys matching: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Pattern invalidation error: {e}")
            return 0
    
    # Convenience methods for specific use cases
    
    async def cache_github_repo(
        self, 
        owner: str, 
        repo: str, 
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache GitHub repository data."""
        key = self._generate_cache_key("github", f"{owner}/{repo}")
        return await self.set(key, data, ttl or self.long_ttl)
    
    async def get_github_repo(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get cached GitHub repository data."""
        key = self._generate_cache_key("github", f"{owner}/{repo}")
        return await self.get(key)
    
    async def cache_api_response(
        self,
        api_name: str,
        endpoint: str,
        params: Dict[str, Any],
        response_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache generic API response."""
        key = self._generate_cache_key(f"api:{api_name}", endpoint, **params)
        return await self.set(key, response_data, ttl or self.default_ttl)
    
    async def get_api_response(
        self,
        api_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached API response."""
        params = params or {}
        key = self._generate_cache_key(f"api:{api_name}", endpoint, **params)
        return await self.get(key)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.redis:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis.info()
            return {
                "status": "connected",
                "memory_used": info.get("used_memory_human", "N/A"),
                "keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                    2
                )
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global cache service instance
cache_service = CacheService()

# Convenience functions for easy import
async def get_cached(key: str) -> Optional[Dict[str, Any]]:
    """Quick cache get."""
    return await cache_service.get(key)

async def set_cached(key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
    """Quick cache set."""
    return await cache_service.set(key, value, ttl)

async def cached_fetch(
    key: str,
    fetch_func: Callable,
    ttl: Optional[int] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """Quick cached fetch."""
    return await cache_service.get_or_set(key, fetch_func, ttl, **kwargs)