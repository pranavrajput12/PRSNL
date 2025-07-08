"""Health check endpoints for monitoring and readiness probes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import psutil
import os
from datetime import datetime
from app.db.database import get_db_pool
from app.config import settings
import redis.asyncio as aioredis

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "prsnl-backend"
    }

@router.get("/health/live")
async def liveness_probe() -> Dict[str, Any]:
    """Kubernetes liveness probe - checks if service is alive"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe - checks if service is ready to accept requests"""
    checks = {
        "database": False,
        "redis": False,
        "disk_space": False,
        "memory": False
    }
    
    # Check database
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["database"] = True
    except Exception:
        pass
    
    # Check Redis
    try:
        redis_client = await aioredis.from_url(settings.REDIS_URL or "redis://redis:6379")
        await redis_client.ping()
        await redis_client.close()
        checks["redis"] = True
    except Exception:
        pass
    
    # Check disk space (require at least 1GB free)
    try:
        disk_usage = psutil.disk_usage('/')
        if disk_usage.free > 1024 * 1024 * 1024:  # 1GB
            checks["disk_space"] = True
    except Exception:
        pass
    
    # Check memory (require at least 100MB free)
    try:
        memory = psutil.virtual_memory()
        if memory.available > 100 * 1024 * 1024:  # 100MB
            checks["memory"] = True
    except Exception:
        pass
    
    # All checks must pass for readiness
    all_healthy = all(checks.values())
    
    if not all_healthy:
        raise HTTPException(status_code=503, detail={
            "status": "not ready",
            "checks": checks
        })
    
    return {
        "status": "ready",
        "checks": checks
    }

@router.get("/health/detailed")
async def detailed_health() -> Dict[str, Any]:
    """Detailed health information for debugging"""
    health_info = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {},
        "services": {},
        "metrics": {}
    }
    
    # System info
    try:
        health_info["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
    except Exception as e:
        health_info["system"] = {"error": str(e)}
    
    # Database check
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            item_count = await conn.fetchval("SELECT COUNT(*) FROM items")
        health_info["services"]["database"] = {
            "status": "connected",
            "item_count": item_count
        }
    except Exception as e:
        health_info["services"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Redis check
    try:
        redis_client = await aioredis.from_url(settings.REDIS_URL or "redis://redis:6379")
        info = await redis_client.info()
        await redis_client.close()
        health_info["services"]["redis"] = {
            "status": "connected",
            "used_memory": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0)
        }
    except Exception as e:
        health_info["services"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check if any service is unhealthy
    for service in health_info["services"].values():
        if isinstance(service, dict) and service.get("status") == "error":
            health_info["status"] = "degraded"
            break
    
    return health_info