from fastapi import FastAPI, Request, Response, status, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import asyncpg
import httpx
import shutil

from app.config import settings
from app.worker import listen_for_notifications
from app.api.middleware import RequestIDMiddleware, LoggingMiddleware, ExceptionHandlerMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add custom middleware
app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.db.database import create_db_pool, close_db_pool
from app.core.background_tasks import background_tasks

# Placeholder for worker task
worker_task = None

@app.on_event("startup")
async def startup_event():
    await create_db_pool()
    global worker_task
    worker_task = asyncio.create_task(listen_for_notifications(settings.DATABASE_URL))
    print("Worker started in background.")

@app.on_event("shutdown")
async def shutdown_event():
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task # Await cancellation to ensure it's done
        except asyncio.CancelledError:
            print("Worker task cancelled successfully.")
    print("Worker stopped.")
    await close_db_pool()
    await background_tasks.shutdown()

from app.api import capture, search, timeline, items

app.include_router(capture.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(timeline.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)

@app.get("/health", summary="Health Check", response_description="API health status")
async def health_check():
    status_info = {
        "database": {"status": "DOWN", "details": ""},
        "ollama": {"status": "DOWN", "details": ""},
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

    # Check Ollama Availability
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
            response.raise_for_status()
            status_info["ollama"]["status"] = "UP"
    except httpx.RequestError as e:
        status_info["ollama"]["details"] = f"Request error: {e}"
    except httpx.HTTPStatusError as e:
        status_info["ollama"]["details"] = f"HTTP error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        status_info["ollama"]["details"] = str(e)

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
            status_info["ollama"]["status"] == "UP" and
            status_info["disk_space"]["status"] == "UP"):
        status_info["overall_status"] = "UP"
        return status_info
    else:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=status_info)

@app.get("/")
def read_root():
    return {"message": "PRSNL Backend"}
