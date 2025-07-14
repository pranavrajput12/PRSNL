"""
Package Intelligence API - Endpoints for package dependency analysis

Provides API endpoints for analyzing package dependencies, security vulnerabilities,
and package health metrics.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.db.database import get_db_pool
from app.workers.package_intelligence_tasks import (
    analyze_project_packages, 
    check_package_security, 
    update_package_cache
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/package-intelligence", tags=["package_intelligence"])

# Request/Response Models
class PackageAnalysisRequest(BaseModel):
    package_files: Dict[str, str]  # filename -> content
    project_path: Optional[str] = ""

class PackageSecurityRequest(BaseModel):
    package_name: str
    package_manager: str  # npm, pypi, cargo, maven
    version: Optional[str] = None

class PackageCacheUpdateRequest(BaseModel):
    package_manager: str
    package_names: List[str]

class PackageInfoResponse(BaseModel):
    name: str
    version: str
    manager: str
    description: Optional[str]
    license: Optional[str]
    homepage: Optional[str]
    repository: Optional[str]
    downloads: Optional[int]
    last_updated: Optional[str]
    deprecated: bool
    security_score: Optional[float]

class PackageAnalysisResponse(BaseModel):
    project_path: str
    analysis_timestamp: str
    total_dependencies: int
    total_vulnerabilities: int
    package_managers: Dict[str, Any]
    security_summary: Dict[str, int]
    license_summary: Dict[str, int]
    maintenance_issues: List[str]
    recommendations: List[str]

# Endpoints
@router.post("/analyze-project")
async def analyze_project_dependencies(
    request: PackageAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Analyze package dependencies for a project"""
    
    try:
        if not request.package_files:
            raise HTTPException(status_code=400, detail="No package files provided")
        
        # Generate job ID for tracking
        import uuid
        job_id = f"pkg_analysis_{uuid.uuid4().hex[:8]}"
        
        # Start analysis task
        task = analyze_project_packages.delay(
            repo_id="",  # Not tied to specific repo
            job_id=job_id,
            package_files=request.package_files,
            project_path=request.project_path or ""
        )
        
        return {
            "job_id": job_id,
            "task_id": task.id,
            "status": "started",
            "message": f"Package analysis started for {len(request.package_files)} files",
            "monitor_url": f"/api/tasks/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Package analysis start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.get("/analysis/{task_id}")
async def get_analysis_results(
    task_id: str,
    current_user = Depends(get_current_user)
):
    """Get package analysis results by task ID"""
    
    try:
        from celery.result import AsyncResult
        from app.workers.celery_app import celery_app
        
        task_result = AsyncResult(task_id, app=celery_app)
        
        if not task_result.ready():
            return {
                "task_id": task_id,
                "status": task_result.status,
                "message": "Analysis in progress"
            }
        
        if task_result.failed():
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(task_result.result)
            }
        
        result = task_result.result
        return {
            "task_id": task_id,
            "status": "completed",
            "results": result
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")

@router.post("/check-security")
async def check_package_security_endpoint(
    request: PackageSecurityRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Check security status of a specific package"""
    
    try:
        # Start security check task
        task = check_package_security.delay(
            package_name=request.package_name,
            package_manager=request.package_manager,
            version=request.version
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Security check started for {request.package_name}",
            "monitor_url": f"/api/tasks/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Package security check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start security check: {str(e)}")

@router.post("/update-cache")
async def update_package_cache_endpoint(
    request: PackageCacheUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Update package information cache"""
    
    try:
        if not request.package_names:
            raise HTTPException(status_code=400, detail="No package names provided")
        
        # Start cache update task
        task = update_package_cache.delay(
            package_manager=request.package_manager,
            package_names=request.package_names
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Cache update started for {len(request.package_names)} packages",
            "monitor_url": f"/api/tasks/status/{task.id}"
        }
        
    except Exception as e:
        logger.error(f"Cache update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start cache update: {str(e)}")

@router.get("/stats")
async def get_package_intelligence_stats(
    days: int = Query(7, ge=1, le=30),
    current_user = Depends(get_current_user)
):
    """Get package intelligence usage statistics"""
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Get analysis stats
            stats = await db.fetchrow("""
                SELECT 
                    COUNT(*) as total_analyses,
                    COUNT(CASE WHEN results->>'status' = 'completed' THEN 1 END) as successful,
                    COUNT(CASE WHEN results->>'status' = 'failed' THEN 1 END) as failed,
                    AVG((results->'analysis_results'->>'total_dependencies')::int) as avg_dependencies,
                    AVG((results->'analysis_results'->>'total_vulnerabilities')::int) as avg_vulnerabilities
                FROM codemirror_analysis_results
                WHERE analysis_type = 'package_intelligence'
                AND created_at > NOW() - INTERVAL '%s days'
            """, days)
            
            # Get package manager distribution
            manager_stats = await db.fetch("""
                SELECT 
                    manager_type,
                    COUNT(*) as count
                FROM (
                    SELECT jsonb_object_keys(results->'analysis_results'->'package_managers') as manager_type
                    FROM codemirror_analysis_results
                    WHERE analysis_type = 'package_intelligence'
                    AND created_at > NOW() - INTERVAL '%s days'
                ) managers
                GROUP BY manager_type
                ORDER BY count DESC
            """, days)
            
            return {
                "period_days": days,
                "total_analyses": stats['total_analyses'] or 0,
                "successful": stats['successful'] or 0,
                "failed": stats['failed'] or 0,
                "success_rate": (stats['successful'] / stats['total_analyses'] * 100) if stats['total_analyses'] > 0 else 0,
                "avg_dependencies": round(stats['avg_dependencies'] or 0, 1),
                "avg_vulnerabilities": round(stats['avg_vulnerabilities'] or 0, 1),
                "package_manager_distribution": [
                    {"manager": row['manager_type'], "count": row['count']}
                    for row in manager_stats
                ]
            }
            
    except Exception as e:
        logger.error(f"Error getting package intelligence stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/supported-managers")
async def get_supported_package_managers():
    """Get list of supported package managers and their capabilities"""
    
    return {
        "package_managers": [
            {
                "name": "npm",
                "display_name": "npm (Node.js)",
                "file_patterns": ["package.json"],
                "registry_url": "https://registry.npmjs.org",
                "capabilities": {
                    "package_info": True,
                    "vulnerability_check": False,  # Requires package-lock.json
                    "license_info": True,
                    "maintenance_metrics": True
                }
            },
            {
                "name": "pypi",
                "display_name": "PyPI (Python)",
                "file_patterns": ["requirements.txt", "requirements-dev.txt", "requirements-test.txt"],
                "registry_url": "https://pypi.org",
                "capabilities": {
                    "package_info": True,
                    "vulnerability_check": False,  # Commercial APIs only
                    "license_info": True,
                    "maintenance_metrics": True
                }
            },
            {
                "name": "cargo",
                "display_name": "Cargo (Rust)",
                "file_patterns": ["Cargo.toml"],
                "registry_url": "https://crates.io",
                "capabilities": {
                    "package_info": True,
                    "vulnerability_check": True,  # RustSec database
                    "license_info": True,
                    "maintenance_metrics": True
                }
            },
            {
                "name": "maven",
                "display_name": "Maven (Java)",
                "file_patterns": ["pom.xml"],
                "registry_url": "https://search.maven.org",
                "capabilities": {
                    "package_info": True,
                    "vulnerability_check": False,  # Limited free API
                    "license_info": False,
                    "maintenance_metrics": True
                }
            }
        ]
    }

@router.get("/health")
async def get_package_intelligence_health():
    """Health check for package intelligence service"""
    
    try:
        # Test connectivity to package registries
        import aiohttp
        
        registries = [
            ("npm", "https://registry.npmjs.org/express"),
            ("pypi", "https://pypi.org/pypi/requests/json"),
            ("cargo", "https://crates.io/api/v1/crates/serde"),
            ("maven", "https://search.maven.org/solrsearch/select?q=a:junit&rows=1&wt=json")
        ]
        
        health_status = {}
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for name, url in registries:
                try:
                    async with session.get(url) as response:
                        health_status[name] = {
                            "status": "healthy" if response.status == 200 else "degraded",
                            "response_code": response.status
                        }
                except Exception as e:
                    health_status[name] = {
                        "status": "unhealthy",
                        "error": str(e)
                    }
        
        overall_healthy = all(
            status["status"] == "healthy" 
            for status in health_status.values()
        )
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "registries": health_status,
            "capabilities": {
                "free_apis_only": True,
                "caching_enabled": True,
                "async_processing": True
            }
        }
        
    except Exception as e:
        logger.error(f"Package intelligence health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }