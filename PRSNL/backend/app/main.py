from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os

from app.config import settings
from app.worker import listen_for_notifications

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Placeholder for worker task
worker_task = None

@app.on_event("startup")
async def startup_event():
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

from app.api import capture, search, timeline, items

app.include_router(capture.router, prefix=settings.API_V1_STR)
app.include_router(search.router, prefix=settings.API_V1_STR)
app.include_router(timeline.router, prefix=settings.API_V1_STR)
app.include_router(items.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "PRSNL Backend"}
