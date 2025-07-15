"""
DragonflyDB Service for high-performance pub/sub and caching.

This service provides Redis-compatible pub/sub functionality using DragonflyDB
for enterprise-grade real-time features and caching.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.asyncio.client import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class DragonflyDBService:
    """
    High-performance pub/sub and caching service using DragonflyDB.
    
    DragonflyDB is a Redis-compatible, multi-threaded, memory-efficient
    data store designed for modern workloads.
    """
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.pubsub_client: Optional[Redis] = None
        self._connected = False
        self._connection_lock = asyncio.Lock()
        
    async def connect(self):
        """Connect to DragonflyDB instance."""
        async with self._connection_lock:
            if self._connected:
                return
                
            try:
                # Create connection pool for regular operations
                self.redis_client = redis.Redis(
                    host=getattr(settings, 'DRAGONFLYDB_HOST', 'localhost'),
                    port=getattr(settings, 'DRAGONFLYDB_PORT', 6379),
                    password=getattr(settings, 'DRAGONFLYDB_PASSWORD', None),
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                # Separate connection for pub/sub
                self.pubsub_client = redis.Redis(
                    host=getattr(settings, 'DRAGONFLYDB_HOST', 'localhost'),
                    port=getattr(settings, 'DRAGONFLYDB_PORT', 6379),
                    password=getattr(settings, 'DRAGONFLYDB_PASSWORD', None),
                    decode_responses=True,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                # Test connection
                await self.redis_client.ping()
                await self.pubsub_client.ping()
                
                self._connected = True
                logger.info("Connected to DragonflyDB")
                
            except Exception as e:
                logger.error(f"Failed to connect to DragonflyDB: {e}")
                await self.disconnect()
                raise
    
    async def disconnect(self):
        """Disconnect from DragonflyDB."""
        async with self._connection_lock:
            if self.redis_client:
                await self.redis_client.close()
                self.redis_client = None
            
            if self.pubsub_client:
                await self.pubsub_client.close()
                self.pubsub_client = None
                
            self._connected = False
            logger.info("Disconnected from DragonflyDB")
    
    async def ensure_connected(self):
        """Ensure connection is established."""
        if not self._connected:
            await self.connect()
    
    async def publish(self, channel: str, message: Union[str, Dict[str, Any]]) -> int:
        """
        Publish message to a channel.
        
        Args:
            channel: Channel name
            message: Message to publish (str or dict)
            
        Returns:
            Number of subscribers that received the message
        """
        await self.ensure_connected()
        
        if isinstance(message, dict):
            message = json.dumps(message)
        
        try:
            result = await self.redis_client.publish(channel, message)
            logger.debug(f"Published to channel {channel}: {result} subscribers")
            return result
        except Exception as e:
            logger.error(f"Failed to publish to channel {channel}: {e}")
            raise
    
    async def subscribe(self, *channels: str) -> AsyncGenerator[str, None]:
        """
        Subscribe to one or more channels.
        
        Args:
            *channels: Channel names to subscribe to
            
        Yields:
            Messages received from subscribed channels
        """
        await self.ensure_connected()
        
        pubsub = self.pubsub_client.pubsub()
        
        try:
            await pubsub.subscribe(*channels)
            logger.info(f"Subscribed to channels: {channels}")
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield message['data']
                    
        except Exception as e:
            logger.error(f"Error in subscription: {e}")
            raise
        finally:
            await pubsub.close()
    
    async def psubscribe(self, *patterns: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribe to channels matching patterns.
        
        Args:
            *patterns: Pattern names to subscribe to
            
        Yields:
            Messages with channel info from pattern-subscribed channels
        """
        await self.ensure_connected()
        
        pubsub = self.pubsub_client.pubsub()
        
        try:
            await pubsub.psubscribe(*patterns)
            logger.info(f"Pattern subscribed to: {patterns}")
            
            async for message in pubsub.listen():
                if message['type'] == 'pmessage':
                    yield {
                        'pattern': message['pattern'],
                        'channel': message['channel'],
                        'data': message['data']
                    }
                    
        except Exception as e:
            logger.error(f"Error in pattern subscription: {e}")
            raise
        finally:
            await pubsub.close()
    
    # Caching methods
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        await self.ensure_connected()
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Union[str, Dict[str, Any]], 
                  ex: Optional[int] = None) -> bool:
        """
        Set key-value pair with optional expiration.
        
        Args:
            key: Key name
            value: Value to store
            ex: Expiration time in seconds
            
        Returns:
            True if successful
        """
        await self.ensure_connected()
        
        if isinstance(value, dict):
            value = json.dumps(value)
            
        try:
            result = await self.redis_client.set(key, value, ex=ex)
            return result
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        await self.ensure_connected()
        try:
            return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete keys {keys}: {e}")
            return 0
    
    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        await self.ensure_connected()
        try:
            return await self.redis_client.exists(*keys)
        except Exception as e:
            logger.error(f"Failed to check existence of keys {keys}: {e}")
            return 0
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash field values."""
        await self.ensure_connected()
        try:
            # Convert dict values to JSON strings if needed
            json_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    json_mapping[k] = json.dumps(v)
                else:
                    json_mapping[k] = str(v)
            
            return await self.redis_client.hset(name, mapping=json_mapping)
        except Exception as e:
            logger.error(f"Failed to set hash {name}: {e}")
            return 0
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        await self.ensure_connected()
        try:
            return await self.redis_client.hget(name, key)
        except Exception as e:
            logger.error(f"Failed to get hash field {name}:{key}: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash field values."""
        await self.ensure_connected()
        try:
            return await self.redis_client.hgetall(name)
        except Exception as e:
            logger.error(f"Failed to get all hash fields for {name}: {e}")
            return {}
    
    async def expire(self, name: str, time: int) -> bool:
        """Set expiration time for a key."""
        await self.ensure_connected()
        try:
            return await self.redis_client.expire(name, time)
        except Exception as e:
            logger.error(f"Failed to set expiration for {name}: {e}")
            return False
    
    async def ttl(self, name: str) -> int:
        """Get time to live for a key."""
        await self.ensure_connected()
        try:
            return await self.redis_client.ttl(name)
        except Exception as e:
            logger.error(f"Failed to get TTL for {name}: {e}")
            return -1
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        await self.ensure_connected()
        try:
            return await self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Failed to get keys with pattern {pattern}: {e}")
            return []
    
    async def flushdb(self) -> bool:
        """Clear the current database."""
        await self.ensure_connected()
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Failed to flush database: {e}")
            return False
    
    async def info(self) -> Dict[str, Any]:
        """Get server information."""
        await self.ensure_connected()
        try:
            return await self.redis_client.info()
        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            return {}
    
    async def ping(self) -> bool:
        """Ping the server."""
        await self.ensure_connected()
        try:
            response = await self.redis_client.ping()
            return response == "PONG"
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False


# Create singleton instance
dragonflydb_service = DragonflyDBService()