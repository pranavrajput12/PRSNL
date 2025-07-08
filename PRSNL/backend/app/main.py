from fastapi import FastAPI, Request, Response, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import os
import asyncpg
import httpx
import shutil
import logging
import sys

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/prsnl_debug.log')
    ]
)

# Set specific loggers to DEBUG
logging.getLogger("app.api.ws").setLevel(logging.DEBUG)
logging.getLogger("app.services.unified_ai_service").setLevel(logging.DEBUG)
logging.getLogger("app.db.database").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

from app.config import settings
from app.worker import listen_for_notifications
from app.api.middleware import RequestIDMiddleware, LoggingMiddleware, ExceptionHandlerMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import limiter, rate_limit_handler, RateLimitExceeded
from app.core.errors import StandardError, standard_error_handler, generic_error_handler
from app.monitoring.metrics import HEALTH_CHECK_STATUS, STORAGE_USAGE_BYTES

from prometheus_client import generate_latest
from starlette_exporter import PrometheusMiddleware, handle_metrics

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add Prometheus middleware
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
app.add_middleware(AuthMiddleware)  # Add auth middleware after exception handler
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.db.database import create_db_pool, close_db_pool, apply_migrations, init_sqlalchemy
from app.core.background_tasks import background_tasks
from app.services.storage_manager import StorageManager
from app.services.cache import cache_service

# Placeholder for worker task
worker_task = None

@app.on_event("startup")
async def startup_event():
    logger.info("Starting PRSNL backend...")
    logger.debug(f"Database URL: {settings.DATABASE_URL}")
    logger.debug(f"Azure OpenAI configured: {settings.AZURE_OPENAI_API_KEY is not None}")
    
    await create_db_pool()
    await init_sqlalchemy()
    await apply_migrations()
    
    # Initialize cache
    if settings.CACHE_ENABLED:
        await cache_service.connect()
    
    global worker_task
    worker_task = asyncio.create_task(listen_for_notifications(settings.DATABASE_URL))
    print("Worker started in background.")

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
            print("Worker task cancelled successfully.")
    print("Worker stopped.")
    
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
            print(f"Error during periodic cleanup: {e}")
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
from app.api import capture, search, timeline, items, admin, videos, telegram, tags, vision, ws, ai_suggest, debug
from app.api import analytics, questions, video_streaming
from app.api import categorization, duplicates, summarization, health
from app.api import insights
from app.api.v2 import items as v2_items
# Still disabled - working on these next:
# from app.api import knowledge_graph, second_brain

app.include_router(capture.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(timeline.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)
app.include_router(tags.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(videos.router, prefix=settings.API_V1_STR)
app.include_router(telegram.router, prefix=settings.API_V1_STR)
app.include_router(vision.router, prefix=settings.API_V1_STR)
app.include_router(ai_suggest.router, prefix=settings.API_V1_STR)
app.include_router(debug.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(questions.router, prefix=settings.API_V1_STR)
app.include_router(video_streaming.router, prefix=settings.API_V1_STR)
app.include_router(categorization.router, prefix=settings.API_V1_STR)
app.include_router(duplicates.router, prefix=settings.API_V1_STR)
app.include_router(summarization.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)  # New health endpoints
app.include_router(insights.router, prefix=settings.API_V1_STR)
# app.include_router(knowledge_graph.router, prefix=settings.API_V1_STR)
# app.include_router(second_brain.router, prefix=settings.API_V1_STR)
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
