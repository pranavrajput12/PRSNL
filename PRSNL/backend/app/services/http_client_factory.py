"""
HTTPClientFactory - Centralized HTTP client management with dependency injection
Provides optimized connection pooling and unified client configuration
"""

import asyncio
import logging
from typing import Dict, Optional, Any, Union
from contextlib import asynccontextmanager
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


class ClientType(str, Enum):
    """Types of HTTP clients with specific configurations"""
    GITHUB = "github"
    AZURE_OPENAI = "azure_openai"
    GENERAL = "general"
    MEDIA_DOWNLOAD = "media_download"
    CRAWL = "crawl"


class HTTPClientConfig(BaseModel):
    """Configuration for HTTP client instances"""
    timeout: float = 30.0
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 5.0
    retries: int = 3
    headers: Dict[str, str] = Field(default_factory=dict)
    base_url: Optional[str] = None
    follow_redirects: bool = True
    verify: bool = True
    

class HTTPClientFactory:
    """
    Centralized HTTP client factory with dependency injection
    
    Features:
    - Connection pooling optimization
    - Client reuse and lifecycle management
    - Type-specific configurations
    - Automatic cleanup and connection management
    """
    
    def __init__(self):
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._configs: Dict[ClientType, HTTPClientConfig] = {}
        self._setup_default_configs()
        self._cleanup_lock = asyncio.Lock()
        
    def _setup_default_configs(self):
        """Setup default configurations for different client types"""
        
        # GitHub API Client
        self._configs[ClientType.GITHUB] = HTTPClientConfig(
            timeout=30.0,
            max_connections=50,
            max_keepalive_connections=10,
            keepalive_expiry=10.0,
            retries=3,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "PRSNL-SecondBrain/1.0",
                "Authorization": f"token {settings.GITHUB_TOKEN}" if settings.GITHUB_TOKEN else ""
            },
            base_url="https://api.github.com",
            follow_redirects=True
        )
        
        # Azure OpenAI Client
        self._configs[ClientType.AZURE_OPENAI] = HTTPClientConfig(
            timeout=120.0,  # Longer timeout for AI operations
            max_connections=30,
            max_keepalive_connections=8,
            keepalive_expiry=30.0,
            retries=2,
            headers={
                "Content-Type": "application/json",
                "api-key": settings.AZURE_OPENAI_API_KEY,
                "User-Agent": "PRSNL-SecondBrain/1.0"
            },
            base_url=settings.AZURE_OPENAI_ENDPOINT,
            follow_redirects=False
        )
        
        # General purpose client
        self._configs[ClientType.GENERAL] = HTTPClientConfig(
            timeout=30.0,
            max_connections=100,
            max_keepalive_connections=20,
            keepalive_expiry=5.0,
            retries=3,
            headers={
                "User-Agent": "PRSNL-SecondBrain/1.0"
            },
            follow_redirects=True
        )
        
        # Media download client (for large files)
        self._configs[ClientType.MEDIA_DOWNLOAD] = HTTPClientConfig(
            timeout=300.0,  # 5 minutes for large downloads
            max_connections=20,
            max_keepalive_connections=5,
            keepalive_expiry=60.0,
            retries=2,
            headers={
                "User-Agent": "PRSNL-SecondBrain/1.0"
            },
            follow_redirects=True
        )
        
        # Crawl client for web scraping
        self._configs[ClientType.CRAWL] = HTTPClientConfig(
            timeout=60.0,
            max_connections=50,
            max_keepalive_connections=15,
            keepalive_expiry=10.0,
            retries=3,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            follow_redirects=True
        )
    
    def _create_client(self, client_type: ClientType, config: HTTPClientConfig) -> httpx.AsyncClient:
        """Create a new HTTP client with optimized configuration"""
        
        # Create optimized limits
        limits = httpx.Limits(
            max_connections=config.max_connections,
            max_keepalive_connections=config.max_keepalive_connections,
            keepalive_expiry=config.keepalive_expiry
        )
        
        # Create timeout configuration
        timeout = httpx.Timeout(
            connect=config.timeout / 4,  # 25% of total timeout for connection
            read=config.timeout,
            write=config.timeout / 2,
            pool=config.timeout / 10
        )
        
        # Create client with configuration
        client_kwargs = {
            'limits': limits,
            'timeout': timeout,
            'headers': config.headers,
            'follow_redirects': config.follow_redirects,
            'verify': config.verify
        }
        
        # Only add base_url if it's not None
        if config.base_url is not None:
            client_kwargs['base_url'] = config.base_url
        
        client = httpx.AsyncClient(**client_kwargs)
        
        logger.info(f"Created HTTP client for {client_type.value} with limits: {limits}")
        return client
    
    async def get_client(self, client_type: ClientType = ClientType.GENERAL) -> httpx.AsyncClient:
        """
        Get or create an HTTP client for the specified type
        
        Args:
            client_type: Type of client to get
            
        Returns:
            Configured HTTP client instance
        """
        client_key = client_type.value
        
        # Return existing client if available
        if client_key in self._clients:
            client = self._clients[client_key]
            if not client.is_closed:
                return client
            else:
                # Remove closed client
                del self._clients[client_key]
        
        # Create new client
        config = self._configs.get(client_type, self._configs[ClientType.GENERAL])
        client = self._create_client(client_type, config)
        self._clients[client_key] = client
        
        return client
    
    @asynccontextmanager
    async def client_session(self, client_type: ClientType = ClientType.GENERAL):
        """
        Context manager for HTTP client sessions
        
        Args:
            client_type: Type of client to use
            
        Yields:
            HTTP client instance
        """
        client = await self.get_client(client_type)
        try:
            yield client
        finally:
            # Client will be reused, no need to close here
            pass
    
    async def make_request(
        self,
        method: str,
        url: str,
        client_type: ClientType = ClientType.GENERAL,
        **kwargs
    ) -> httpx.Response:
        """
        Make an HTTP request using the specified client type
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            client_type: Type of client to use
            **kwargs: Additional request parameters
            
        Returns:
            HTTP response
        """
        client = await self.get_client(client_type)
        
        # Add retries with exponential backoff
        config = self._configs.get(client_type, self._configs[ClientType.GENERAL])
        max_retries = config.retries
        
        for attempt in range(max_retries + 1):
            try:
                response = await client.request(method, url, **kwargs)
                
                # Check if we should retry on this status
                if response.status_code >= 500 and attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                return response
                
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                if attempt < max_retries:
                    logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"All retry attempts failed for {url}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                raise
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics for all clients"""
        stats = {}
        
        for client_type, client in self._clients.items():
            if not client.is_closed:
                # Get connection pool stats
                transport = client._transport
                if hasattr(transport, '_pool'):
                    pool = transport._pool
                    stats[client_type] = {
                        "total_connections": len(pool._connections),
                        "idle_connections": len([c for c in pool._connections if not c.is_busy()]),
                        "max_connections": pool._max_connections,
                        "max_keepalive": pool._max_keepalive_connections,
                        "client_closed": client.is_closed
                    }
                else:
                    stats[client_type] = {
                        "client_closed": client.is_closed,
                        "transport_type": type(transport).__name__
                    }
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all HTTP clients"""
        health_status = {
            "status": "healthy",
            "clients": {},
            "total_clients": len(self._clients),
            "active_clients": 0
        }
        
        for client_type, client in self._clients.items():
            client_health = {
                "type": client_type,
                "is_closed": client.is_closed,
                "base_url": str(client.base_url) if client.base_url else None
            }
            
            if not client.is_closed:
                health_status["active_clients"] += 1
                client_health["status"] = "active"
                
                # Try a simple health check if it's a service with known health endpoint
                if client_type == "github":
                    try:
                        response = await client.get("/rate_limit", timeout=5.0)
                        client_health["api_accessible"] = response.status_code == 200
                    except Exception:
                        client_health["api_accessible"] = False
            else:
                client_health["status"] = "closed"
            
            health_status["clients"][client_type] = client_health
        
        return health_status
    
    async def close_client(self, client_type: ClientType):
        """Close a specific client"""
        client_key = client_type.value
        if client_key in self._clients:
            client = self._clients[client_key]
            if not client.is_closed:
                await client.aclose()
            del self._clients[client_key]
            logger.info(f"Closed HTTP client for {client_type.value}")
    
    async def close_all_clients(self):
        """Close all HTTP clients"""
        async with self._cleanup_lock:
            for client_type, client in self._clients.items():
                if not client.is_closed:
                    try:
                        await client.aclose()
                        logger.info(f"Closed HTTP client for {client_type}")
                    except Exception as e:
                        logger.warning(f"Error closing client {client_type}: {e}")
            
            self._clients.clear()
            logger.info("All HTTP clients closed")
    
    async def refresh_client(self, client_type: ClientType):
        """Refresh a client by closing and recreating it"""
        await self.close_client(client_type)
        await self.get_client(client_type)
        logger.info(f"Refreshed HTTP client for {client_type.value}")
    
    def update_config(self, client_type: ClientType, config: HTTPClientConfig):
        """Update configuration for a client type"""
        self._configs[client_type] = config
        
        # If client exists, refresh it to use new config
        if client_type.value in self._clients:
            asyncio.create_task(self.refresh_client(client_type))
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_all_clients()


# Singleton instance
http_client_factory = HTTPClientFactory()


# Convenience functions for common operations
async def get_github_client() -> httpx.AsyncClient:
    """Get GitHub API client"""
    return await http_client_factory.get_client(ClientType.GITHUB)


async def get_azure_openai_client() -> httpx.AsyncClient:
    """Get Azure OpenAI client"""
    return await http_client_factory.get_client(ClientType.AZURE_OPENAI)


async def get_general_client() -> httpx.AsyncClient:
    """Get general purpose HTTP client"""
    return await http_client_factory.get_client(ClientType.GENERAL)


async def get_media_download_client() -> httpx.AsyncClient:
    """Get media download client"""
    return await http_client_factory.get_client(ClientType.MEDIA_DOWNLOAD)


async def get_crawl_client() -> httpx.AsyncClient:
    """Get web crawling client"""
    return await http_client_factory.get_client(ClientType.CRAWL)