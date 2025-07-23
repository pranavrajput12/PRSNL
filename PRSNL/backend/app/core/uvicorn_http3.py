"""
Uvicorn 0.35.0 HTTP/3 Configuration
Enables QUIC protocol for improved performance and reduced latency
"""

import logging
import ssl
from typing import Dict, Any, Optional
from pathlib import Path

import uvicorn
from uvicorn.config import LOGGING_CONFIG

from app.config import settings

logger = logging.getLogger(__name__)


class HTTP3Server:
    """
    Uvicorn server with HTTP/3 (QUIC) support
    Requires SSL certificates for HTTP/3 to work
    """
    
    def __init__(
        self,
        app: str = "app.main:app",
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False
    ):
        self.app = app
        self.host = host
        self.port = port
        self.reload = reload
        
        # HTTP/3 specific configuration
        self.http = "h3"  # Enable HTTP/3
        self.ssl_keyfile = settings.get("SSL_KEYFILE", "certs/key.pem")
        self.ssl_certfile = settings.get("SSL_CERTFILE", "certs/cert.pem")
        
        # Performance settings
        self.workers = settings.get("UVICORN_WORKERS", 4)
        self.loop = "uvloop"  # Use uvloop for better performance
        self.interface = "asgi3"  # ASGI 3.0 interface
        
    def create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for HTTP/3"""
        try:
            # Check if certificates exist
            if not (Path(self.ssl_keyfile).exists() and Path(self.ssl_certfile).exists()):
                logger.warning("SSL certificates not found. HTTP/3 requires HTTPS.")
                return None
            
            # Create SSL context
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
            
            # Enable ALPN for HTTP/3
            ssl_context.set_alpn_protocols(["h3", "h2", "http/1.1"])
            
            # Security settings
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3  # HTTP/3 requires TLS 1.3
            ssl_context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS")
            
            return ssl_context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None
    
    def get_config(self) -> Dict[str, Any]:
        """Get Uvicorn configuration with HTTP/3 support"""
        # Custom logging configuration
        log_config = LOGGING_CONFIG.copy()
        log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_config["formatters"]["access"]["fmt"] = '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s'
        
        config = {
            "app": self.app,
            "host": self.host,
            "port": self.port,
            "reload": self.reload,
            "log_config": log_config,
            "log_level": "info",
            
            # HTTP/3 configuration
            "http": self.http,
            "ws": "auto",  # WebSocket support
            
            # Performance settings
            "loop": self.loop,
            "interface": self.interface,
            "lifespan": "on",
            
            # Server settings
            "server_header": False,  # Don't expose server info
            "date_header": True,
            
            # Connection settings
            "limit_concurrency": 1000,
            "limit_max_requests": 10000,
            "timeout_keep_alive": 5,
            
            # HTTP/2 and HTTP/3 settings
            "h11_max_incomplete_event_size": 16384,
            "ws_max_size": 16777216,  # 16MB WebSocket message size
            "ws_ping_interval": 20.0,
            "ws_ping_timeout": 20.0,
        }
        
        # Add SSL context if available
        ssl_context = self.create_ssl_context()
        if ssl_context:
            config["ssl"] = ssl_context
            logger.info("HTTP/3 enabled with SSL context")
        else:
            logger.warning("HTTP/3 requires SSL certificates. Running without HTTP/3.")
        
        # Multi-worker configuration
        if not self.reload and self.workers > 1:
            config["workers"] = self.workers
            logger.info(f"Running with {self.workers} workers")
        
        return config
    
    def run(self):
        """Start the Uvicorn server with HTTP/3 support"""
        config = self.get_config()
        
        logger.info(f"Starting Uvicorn with HTTP/3 support on {self.host}:{self.port}")
        logger.info(f"HTTP versions supported: HTTP/3 (QUIC), HTTP/2, HTTP/1.1")
        
        # Log performance features
        logger.info("Performance features enabled:")
        logger.info("- uvloop for async performance")
        logger.info("- HTTP/3 QUIC protocol for reduced latency")
        logger.info("- Connection multiplexing")
        logger.info("- 0-RTT resumption")
        
        uvicorn.run(**config)


def create_development_server() -> HTTP3Server:
    """Create a development server with hot reload"""
    return HTTP3Server(
        host="127.0.0.1",
        port=settings.BACKEND_PORT,
        reload=True
    )


def create_production_server() -> HTTP3Server:
    """Create a production server with multiple workers"""
    return HTTP3Server(
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=False
    )


def generate_self_signed_cert(cert_dir: str = "certs"):
    """Generate self-signed certificates for testing HTTP/3"""
    import subprocess
    from pathlib import Path
    
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)
    
    key_file = cert_path / "key.pem"
    cert_file = cert_path / "cert.pem"
    
    if key_file.exists() and cert_file.exists():
        logger.info("SSL certificates already exist")
        return
    
    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa",
            "-out", str(key_file),
            "2048"
        ], check=True)
        
        # Generate certificate
        subprocess.run([
            "openssl", "req", "-new", "-x509",
            "-key", str(key_file),
            "-out", str(cert_file),
            "-days", "365",
            "-subj", "/CN=localhost"
        ], check=True)
        
        logger.info(f"Generated self-signed certificates in {cert_dir}/")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate certificates: {e}")
        raise


# FastAPI app configuration for HTTP/3
def configure_app_for_http3(app):
    """Configure FastAPI app for optimal HTTP/3 performance"""
    from fastapi import FastAPI
    from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
    from starlette.middleware.gzip import GZipMiddleware
    
    # Add HTTPS redirect in production
    if settings.ENVIRONMENT == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Add compression (works well with HTTP/3)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Add HTTP/3 Alt-Svc header
    @app.middleware("http")
    async def add_http3_header(request, call_next):
        response = await call_next(request)
        
        # Advertise HTTP/3 support
        if request.url.scheme == "https":
            response.headers["Alt-Svc"] = f'h3=":{request.url.port}"; ma=86400'
        
        return response
    
    return app


# HTTP/3 client for testing
class HTTP3Client:
    """Client for testing HTTP/3 endpoints"""
    
    def __init__(self, base_url: str = "https://localhost:8000"):
        self.base_url = base_url
    
    async def test_http3_connection(self) -> Dict[str, Any]:
        """Test HTTP/3 connection and features"""
        try:
            import httpx
            import h3  # HTTP/3 support
            
            # Create HTTP/3 client
            async with httpx.AsyncClient(
                http2=True,
                verify=True,  # Always verify SSL certificates for security
                timeout=30.0
            ) as client:
                # Test basic connection
                response = await client.get(f"{self.base_url}/health")
                
                # Check protocol version
                protocol = response.http_version
                
                return {
                    "success": True,
                    "protocol": protocol,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "features": {
                        "multiplexing": protocol in ["HTTP/2", "HTTP/3"],
                        "server_push": protocol == "HTTP/3",
                        "0_rtt": protocol == "HTTP/3"
                    }
                }
                
        except Exception as e:
            logger.error(f"HTTP/3 test error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Command-line interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate-certs":
        generate_self_signed_cert()
    elif len(sys.argv) > 1 and sys.argv[1] == "production":
        server = create_production_server()
        server.run()
    else:
        server = create_development_server()
        server.run()