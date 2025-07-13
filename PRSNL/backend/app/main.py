import asyncio
import logging
import os
import shutil
import socket
import sys
import tempfile

import asyncpg
import httpx
from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure uvloop for 2-4x async performance boost
try:
    import uvloop

    # Only install on non-Windows platforms (uvloop doesn't support Windows)
    if sys.platform != 'win32':
        uvloop.install()
        logging.info("🚀 uvloop installed - async performance optimized")
    else:
        logging.info("⚠️ uvloop not available on Windows - using default asyncio")
except ImportError:
    logging.warning("⚠️ uvloop not available - install with: pip install uvloop")

# Import Sentry
# from app.core.sentry import init_sentry

# Import observability (disabled - missing dependencies)
# TODO: Fix observability dependencies in Docker build
# from app.core.observability import instrument_fastapi_app

# Configure comprehensive logging with secure temp file
# Create secure temporary directory for logs
temp_dir = tempfile.mkdtemp(prefix='prsnl_logs_')
log_file = os.path.join(temp_dir, 'prsnl_debug.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)

# Set specific loggers to DEBUG
logging.getLogger("app.api.ws").setLevel(logging.DEBUG)
logging.getLogger("app.services.unified_ai_service").setLevel(logging.DEBUG)
logging.getLogger("app.db.database").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Initialize Sentry before other imports
# init_sentry()  # Temporarily disabled

from prometheus_client import generate_latest
from starlette_exporter import handle_metrics, PrometheusMiddleware

from app.api.middleware import ExceptionHandlerMiddleware, RequestIDMiddleware
from app.config import settings
from app.core.errors import generic_error_handler, standard_error_handler, StandardError
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import APIResponseTimeMiddleware
from app.middleware.rate_limit import limiter, rate_limit_handler, RateLimitExceeded
from app.monitoring.metrics import HEALTH_CHECK_STATUS, STORAGE_USAGE_BYTES
from app.worker import listen_for_notifications

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 🔍 Two-line drop-in observability setup
# instrument_fastapi_app(app)

# Add legacy Prometheus middleware (enhanced by observability)
app.add_middleware(PrometheusMiddleware, app_name="prsnl_backend", group_paths=True)
app.add_route("/metrics", handle_metrics)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add standard error handlers
app.add_exception_handler(StandardError, standard_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Add custom middleware
app.add_middleware(ExceptionHandlerMiddleware)
# app.add_middleware(AuthMiddleware)  # Temporarily disabled for debugging
app.add_middleware(APIResponseTimeMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.background_tasks import background_tasks
from app.db.database import (
    apply_migrations,
    close_db_pool,
    create_db_pool,
    init_sqlalchemy,
)
from app.services.cache import cache_service
from app.services.storage_manager import StorageManager

# Placeholder for worker task
worker_task = None

def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return False
        except socket.error:
            return True

@app.on_event("startup")
async def startup_event():
    logger.info("Starting PRSNL backend...")
    logger.debug(f"Database URL: {settings.DATABASE_URL}")
    logger.debug(f"Azure OpenAI configured: {settings.AZURE_OPENAI_API_KEY is not None}")
    
    # Startup assertion: Check if our port is available
    if is_port_in_use(settings.BACKEND_PORT):
        logger.error(f"🚨 Port {settings.BACKEND_PORT} is already in use!")
        logger.error("Run 'make kill-ports' or './scripts/kill_ports.sh kill' to free up ports")
        # Don't assert in production, just warn
        if settings.ENVIRONMENT == "development":
            raise RuntimeError(f"Port {settings.BACKEND_PORT} conflict detected! Another process is using this port.")
    
    await create_db_pool()
    await init_sqlalchemy()
    await apply_migrations()
    
    # Initialize cache
    if settings.CACHE_ENABLED:
        await cache_service.connect()
    
    global worker_task
    worker_task = asyncio.create_task(listen_for_notifications(settings.DATABASE_URL))
    logger.info("Worker started in background.")

    # STEP 2: Dump all registered routes to debug routing issue (controlled by env var)
    if os.getenv("DEBUG_ROUTES", "false").lower() == "true":
        logger.warning("🚀 === ALL REGISTERED ROUTES ===")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                logger.warning(f"🚀 ROUTE: {route.path} METHODS: {getattr(route, 'methods', 'N/A')}")
            elif hasattr(route, 'path_regex'):
                logger.warning(f"🚀 ROUTE: {route.path_regex.pattern} METHODS: {getattr(route, 'methods', 'N/A')}")
            else:
                logger.warning(f"🚀 ROUTE: {route} TYPE: {type(route)}")
        logger.warning("🚀 === END ROUTES ===")

    # Schedule periodic cleanup tasks
    storage_manager = StorageManager()
    background_tasks.add_task(run_periodic_cleanup, storage_manager)
    background_tasks.add_task(update_storage_metrics_periodically, storage_manager)

@app.on_event("shutdown")
async def shutdown_event():
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task # Await cancellation to ensure it's done
        except asyncio.CancelledError:
            logger.info("Worker task cancelled successfully.")
    logger.info("Worker stopped.")
    
    # Close cache connection
    if settings.CACHE_ENABLED:
        await cache_service.disconnect()
    
    await close_db_pool()
    await background_tasks.shutdown()

async def run_periodic_cleanup(storage_manager: StorageManager):
    """Runs periodic cleanup tasks."""
    while True:
        try:
            await storage_manager.cleanup_orphaned_files()
            await storage_manager.cleanup_temp_files()
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")
        await asyncio.sleep(3600) # Run every hour (3600 seconds)

async def update_storage_metrics_periodically(storage_manager: StorageManager):
    """Updates storage metrics periodically."""
    while True:
        try:
            stats = await storage_manager.get_storage_metrics()
            STORAGE_USAGE_BYTES.labels(type='total').set(stats['total_size_bytes'])
            STORAGE_USAGE_BYTES.labels(type='videos').set(stats['video_size_bytes'])
            STORAGE_USAGE_BYTES.labels(type='thumbnails').set(stats['thumbnail_size_bytes'])
            STORAGE_USAGE_BYTES.labels(type='temp').set(stats['temp_size_bytes'])
        except Exception as e:
            logging.error(f"Error updating storage metrics: {e}")
        await asyncio.sleep(600) # Update every 10 minutes (600 seconds)

from fastapi.staticfiles import StaticFiles

from app.api import librechat_bridge  # New LibreChat integration bridge
from app.api import openclip  # OpenCLIP vision service
from app.api import (
    admin,
    ai,
    ai_suggest,
    analytics,
    capture,
    categorization,
    content_types,
    content_urls,
    debug,
    development,
    duplicates,
    embeddings,
    enhanced_search,
    file_upload,
    firecrawl,
    health,
    import_data,
    insights,
    items,
    questions,
    rag,
    search,
    summarization,
    tags,
    timeline,
    video_streaming,
    videos,
    vision,
    ws,
)
from app.api.v2 import items as v2_items

# STEP 3: Debug capture router inclusion
logger.warning(f"🔍 ABOUT TO INCLUDE CAPTURE ROUTER: {capture.router}")
logger.warning(f"🔍 CAPTURE ROUTER ROUTES: {[r.path for r in capture.router.routes]}")
logger.warning(f"🔍 API_V1_STR: {settings.API_V1_STR}")

app.include_router(capture.router, prefix=settings.API_V1_STR)
logger.warning("🔍 CAPTURE ROUTER INCLUDED")
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(timeline.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)
app.include_router(tags.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(videos.router, prefix=settings.API_V1_STR)
app.include_router(vision.router, prefix=settings.API_V1_STR)
app.include_router(ai_suggest.router, prefix=settings.API_V1_STR)
app.include_router(debug.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(questions.router, prefix=settings.API_V1_STR)
app.include_router(video_streaming.router, prefix=settings.API_V1_STR)
app.include_router(categorization.router, prefix=settings.API_V1_STR)
app.include_router(duplicates.router, prefix=settings.API_V1_STR)
app.include_router(summarization.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(insights.router, prefix=settings.API_V1_STR)
app.include_router(import_data.router, prefix=settings.API_V1_STR)
# Backward compatibility alias
@app.get("/api/import-data")
async def import_data_alias():
    """Backward compatibility redirect to import endpoints"""
    return {
        "message": "Import endpoints have moved",
        "new_base_url": "/api/import",
        "available_endpoints": [
            "/api/import/",
            "/api/import/json", 
            "/api/import/bookmarks",
            "/api/import/notes",
            "/api/import/urls/bulk"
        ],
        "documentation": "Use GET /api/import/ for full endpoint documentation"
    }
app.include_router(file_upload.router, prefix=settings.API_V1_STR + "/file")
app.include_router(content_types.router, prefix=settings.API_V1_STR)
app.include_router(development.router, prefix=settings.API_V1_STR)
app.include_router(ai.router, prefix=settings.API_V1_STR)
app.include_router(rag.router, prefix=settings.API_V1_STR)  # Haystack RAG service
app.include_router(firecrawl.router, prefix=settings.API_V1_STR)
app.include_router(enhanced_search.router, prefix=settings.API_V1_STR)
app.include_router(embeddings.router, prefix=settings.API_V1_STR)
app.include_router(openclip.router, prefix=settings.API_V1_STR)  # OpenCLIP vision service
app.include_router(content_urls.router)  # No prefix, includes /api in router
app.include_router(librechat_bridge.router)  # LibreChat integration bridge
app.include_router(ws.router)

# V2 API endpoints with improved standards
app.include_router(v2_items.router, prefix="/api/v2", tags=["v2-items"])

# Mount static files for media
media_path = os.path.abspath(settings.MEDIA_DIR)
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")

# Mount test files
app_path = os.path.dirname(os.path.abspath(__file__))
app.mount("/test", StaticFiles(directory=app_path, html=True), name="test")

@app.get("/health", summary="Health Check", response_description="API health status")
async def health_check():
    status_info = {
        "database": {"status": "DOWN", "details": ""},
        "azure_openai": {"status": "DOWN", "details": ""},
        "disk_space": {"status": "UNKNOWN", "details": ""},
        "overall_status": "DOWN"
    }

    # Check Database Connection
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        await conn.close()
        status_info["database"]["status"] = "UP"
    except Exception as e:
        status_info["database"]["details"] = str(e)

    # Check Azure OpenAI Availability
    try:
        if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.AZURE_OPENAI_ENDPOINT}/openai/models?api-version={settings.AZURE_OPENAI_API_VERSION}",
                    headers={"api-key": settings.AZURE_OPENAI_API_KEY},
                    timeout=5
                )
                response.raise_for_status()
                status_info["azure_openai"]["status"] = "UP"
        else:
            status_info["azure_openai"]["details"] = "Not configured"
    except httpx.RequestError as e:
        status_info["azure_openai"]["details"] = f"Request error: {e}"
    except httpx.HTTPStatusError as e:
        status_info["azure_openai"]["details"] = f"HTTP error: {e.response.status_code}"
    except Exception as e:
        status_info["azure_openai"]["details"] = str(e)

    # Check Disk Space
    try:
        total, used, free = shutil.disk_usage("/")
        status_info["disk_space"]["status"] = "UP"
        status_info["disk_space"]["details"] = {
            "total": f"{total / (1024**3):.2f} GB",
            "used": f"{used / (1024**3):.2f} GB",
            "free": f"{free / (1024**3):.2f} GB",
            "percentage_free": f"{free / total * 100:.2f}%"
        }
    except Exception as e:
        status_info["disk_space"]["status"] = "DOWN"
        status_info["disk_space"]["details"] = str(e)

    # Determine overall status
    if (status_info["database"]["status"] == "UP" and
            status_info["azure_openai"]["status"] == "UP" and
            status_info["disk_space"]["status"] == "UP"):
        status_info["overall_status"] = "UP"
        HEALTH_CHECK_STATUS.set(1)
        return status_info
    else:
        HEALTH_CHECK_STATUS.set(0)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=status_info)

@app.get("/")
def read_root():
    return {"message": "PRSNL Backend"}
