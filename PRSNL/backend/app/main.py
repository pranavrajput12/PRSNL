import asyncio
import logging
import os
import shutil
import socket
import sys
import tempfile

# Environment-aware logging configuration
from app.config import settings

# Configure logging based on environment
log_level = getattr(logging, settings.LOG_LEVEL.upper())
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" if settings.ENVIRONMENT == "production" else "🔍 %(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Set specific loggers based on environment
if settings.ENABLE_VERBOSE_LOGGING:
    logging.getLogger("app.api.ws").setLevel(logging.DEBUG)
    logging.getLogger("app.middleware.auth").setLevel(logging.DEBUG)
    logging.getLogger("app.services").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
else:
    # Production logging levels
    logging.getLogger("app.api.ws").setLevel(logging.WARNING)
    logging.getLogger("app.middleware.auth").setLevel(logging.INFO)
    logging.getLogger("app.services").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

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
from app.core.sentry import init_sentry

# Import observability (disabled - missing dependencies)
# TODO: Fix observability dependencies in Docker build
# from app.core.observability import instrument_fastapi_app

# Import performance monitoring
from app.services.performance_monitoring import PerformanceMonitor

# Configure comprehensive logging with secure temp file
# Environment-aware file logging (only in development)
if settings.ENABLE_VERBOSE_LOGGING and settings.ENVIRONMENT != "production":
    temp_dir = tempfile.mkdtemp(prefix='prsnl_logs_')
    log_file = os.path.join(temp_dir, 'prsnl_debug.log')
    
    # Add file handler for development debugging
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    
    # Additional debug loggers for development
    logging.getLogger("app.services.unified_ai_service").setLevel(logging.DEBUG)
    logging.getLogger("app.db.database").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

# Initialize Sentry before other imports
init_sentry()

from prometheus_client import generate_latest
from starlette_exporter import handle_metrics, PrometheusMiddleware

from app.api.middleware import ExceptionHandlerMiddleware, RequestIDMiddleware
from app.config import settings
from app.core.errors import generic_error_handler, standard_error_handler, StandardError
from app.middleware.auth import AuthMiddleware
from app.middleware.unified_auth import unified_auth
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
app.add_middleware(AuthMiddleware)  # JWT authentication middleware
app.add_middleware(APIResponseTimeMiddleware)
app.add_middleware(RequestIDMiddleware)

# Add Sentry 2.33.0 Performance Monitoring middleware
app.add_middleware(PerformanceMonitor.create_performance_middleware())
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
from app.services.codemirror_realtime_service import realtime_service
from app.workers.celery_app import celery_app

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
    
    # Start CodeMirror real-time service
    await realtime_service.start()
    logger.info("✅ CodeMirror real-time service started")
    
    # Initialize Celery app for task dispatching
    logger.info(f"✅ Celery app initialized: {celery_app.main}")
    logger.info(f"✅ Celery broker: {celery_app.conf.broker_url}")
    logger.info(f"✅ Celery backend: {celery_app.conf.result_backend}")
    logger.info(f"✅ Celery task modules: {len(celery_app.conf.include)} modules loaded")
    
    global worker_task
    worker_task = asyncio.create_task(listen_for_notifications(settings.DATABASE_URL))
    logger.info("Worker started in background.")

    # STEP 2: Debug route dumping (only in development)
    if settings.ENABLE_VERBOSE_LOGGING and settings.ENVIRONMENT != "production":
        if os.getenv("DEBUG_ROUTES", "false").lower() == "true":
            logger.debug("=== ALL REGISTERED ROUTES ===")
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    logger.debug(f"ROUTE: {route.path} METHODS: {getattr(route, 'methods', 'N/A')}")
                elif hasattr(route, 'path_regex'):
                    logger.debug(f"ROUTE: {route.path_regex.pattern} METHODS: {getattr(route, 'methods', 'N/A')}")
                else:
                    logger.debug(f"ROUTE: {route} TYPE: {type(route)}")
            logger.debug("=== END ROUTES ===")

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
    
    # Stop CodeMirror real-time service
    await realtime_service.stop()
    logger.info("✅ CodeMirror real-time service stopped")
    
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

from app.api import auth  # Authentication API endpoints
from app.api import questions  # Questions API for suggested questions
from app.api import librechat_bridge  # New LibreChat integration bridge
from app.api import openclip  # OpenCLIP vision service
from app.api import crawl_ai_integration  # New Crawl.ai multi-agent system
from app.api import persistence  # New unified job persistence system
from app.api import codemirror  # CodeMirror - AI repository intelligence
from app.api import codemirror_websocket  # CodeMirror WebSocket for real-time sync
from app.api import task_monitoring  # Enterprise task monitoring for Celery
from app.api import package_intelligence  # Package dependency intelligence
from app.api import background_processing  # Phase 1 Celery background processing
from app.api import knowledge_graph_api  # Phase 2 Knowledge Graph API
# from app.api import agent_monitoring_api  # Phase 2 Agent Monitoring API - temporarily disabled
from app.api import github  # GitHub OAuth and repository sync
from app.api import websocket_enhanced  # Enhanced WebSocket with FastAPI 0.116.1 improvements
# from app.api import enhanced_processing  # Enhanced processing with new package features - temporarily disabled due to OpenTelemetry conflicts
from app.api import voice  # Voice chat with Cortex personality
from app.api import user_settings  # User settings API
# from app.api import crew_api  # Crew.ai autonomous agent system - temporarily disabled
# Phase 5: Advanced AI Features
from app.api import multimodal_ai  # Multi-modal AI processing (Vision + Text + Voice)
# from app.api import advanced_code_api  # Advanced code intelligence - temporarily disabled due to missing bandit
# from app.api import natural_language_api  # Natural language system control - temporarily disabled due to bandit dependency
from app.api import (
    admin,
    ai,
    ai_suggest,
    analytics,
    capture,
    categorization,
    content_types,
    content_urls,
    conversations,  # Neural Echo - AI chat conversations
    conversation_intelligence,  # AI-powered conversation analysis
    conversation_groups,  # Conversation groups endpoint
    debug,
    development,
    duplicates,
    embeddings,
    enhanced_search,
    file_upload,
    firecrawl,
    health,
    # import_data,  # Temporarily disabled due to CrewAI OpenTelemetry conflicts
    insights,
    items,
    questions,
    rag,
    search,
    summarization,
    tags,
    timeline,
    user_profile,  # User profile and settings management
    video_streaming,
    videos,
    vision,
    ws,
)
from app.api.v2 import items as v2_items

# STEP 3: Include routers with optional debug logging
if settings.ENABLE_VERBOSE_LOGGING:
    logger.debug(f"Including capture router: {capture.router}")
    logger.debug(f"Capture router routes: {[r.path for r in capture.router.routes]}")
    logger.debug(f"API_V1_STR: {settings.API_V1_STR}")

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])  # Authentication endpoints at /api/auth
app.include_router(capture.router, prefix=settings.API_V1_STR)

if settings.ENABLE_VERBOSE_LOGGING:
    logger.debug("Capture router included successfully")
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(timeline.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)
app.include_router(tags.router, prefix=settings.API_V1_STR)
app.include_router(user_profile.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(videos.router, prefix=settings.API_V1_STR)
app.include_router(vision.router, prefix=settings.API_V1_STR)
app.include_router(ai_suggest.router, prefix=settings.API_V1_STR)
app.include_router(crawl_ai_integration.router, prefix=settings.API_V1_STR)  # Crawl.ai multi-agent system
app.include_router(debug.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(questions.router, prefix=settings.API_V1_STR)
app.include_router(video_streaming.router, prefix=settings.API_V1_STR)
app.include_router(categorization.router, prefix=settings.API_V1_STR)
app.include_router(duplicates.router, prefix=settings.API_V1_STR)
app.include_router(summarization.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(insights.router, prefix=settings.API_V1_STR)
# app.include_router(import_data.router, prefix=settings.API_V1_STR)  # Temporarily disabled
app.include_router(conversations.router, prefix=settings.API_V1_STR)  # Neural Echo - AI chat conversations
app.include_router(conversation_intelligence.router, prefix=settings.API_V1_STR)  # AI-powered analysis
app.include_router(conversation_groups.router, prefix=settings.API_V1_STR)  # Conversation groups endpoint
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
app.include_router(persistence.router, prefix=settings.API_V1_STR + "/persistence", tags=["persistence"])  # Unified job persistence system
app.include_router(codemirror.router)  # CodeMirror - AI repository intelligence (includes /api/code-cortex/codemirror prefix)
app.include_router(codemirror_websocket.router)  # CodeMirror WebSocket endpoints for real-time sync
app.include_router(task_monitoring.router)  # Enterprise task monitoring for Celery
app.include_router(package_intelligence.router)  # Package dependency intelligence
app.include_router(background_processing.router)  # Phase 1 Celery background processing
app.include_router(knowledge_graph_api.router)  # Phase 2 Knowledge Graph API
# app.include_router(agent_monitoring_api.router)  # Phase 2 Agent Monitoring API - temporarily disabled
app.include_router(github.router)  # GitHub OAuth and repository sync
# app.include_router(crew_api.router)  # Crew.ai autonomous agent system - temporarily disabled
app.include_router(content_urls.router)  # No prefix, includes /api in router
app.include_router(librechat_bridge.router)  # LibreChat integration bridge
app.include_router(ws.router)
app.include_router(websocket_enhanced.router)  # Enhanced WebSocket with FastAPI 0.116.1 improvements
# app.include_router(enhanced_processing.router)  # Enhanced processing with updated package features - temporarily disabled
app.include_router(voice.router, prefix=settings.API_V1_STR)  # Voice chat with Cortex personality
app.include_router(user_settings.router, prefix=settings.API_V1_STR)  # User settings API

# Phase 5: Advanced AI Features - Multi-modal Processing & Intelligence
app.include_router(multimodal_ai.router)  # Multi-modal AI processing (includes /api/multimodal prefix)
# app.include_router(advanced_code_api.router)  # Advanced code intelligence (includes /api/code prefix) - temporarily disabled
# app.include_router(natural_language_api.router)  # Natural language system control (includes /api/nl prefix) - temporarily disabled

# V2 API endpoints with improved standards
app.include_router(v2_items.router, prefix="/api/v2", tags=["v2-items"])

# Mount static files for media
media_path = os.path.abspath(settings.MEDIA_DIR)
if os.path.exists(media_path):
    app.mount("/media", StaticFiles(directory=media_path), name="media")

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

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
