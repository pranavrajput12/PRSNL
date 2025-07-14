"""
Package Intelligence Celery Tasks

Distributed tasks for analyzing package dependencies and security.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.package_intelligence_service import package_intelligence_service

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.package_intelligence_tasks.analyze_project_packages")
def analyze_project_packages(
    repo_id: str,
    job_id: str,
    package_files: Dict[str, str],
    project_path: str = ""
) -> Dict[str, Any]:
    """
    Analyze package dependencies for a project.
    
    Args:
        repo_id: Repository ID
        job_id: Job ID for tracking
        package_files: Dict of filename -> content for package files
        project_path: Path to the project
    
    Returns:
        Package analysis results
    """
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _analyze_project_packages_async(repo_id, job_id, package_files, project_path)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Package analysis failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _analyze_project_packages_async(
    repo_id: str,
    job_id: str,
    package_files: Dict[str, str],
    project_path: str
) -> Dict[str, Any]:
    """Async implementation of package analysis"""
    
    try:
        # Send initial progress
        await _send_progress_update(
            analyze_project_packages.request.id, job_id, 
            "package_analysis", 0, 5, "Starting package analysis"
        )
        
        # Validate inputs
        if not package_files:
            return {
                "status": "skipped",
                "message": "No package files found",
                "analysis_results": {}
            }
        
        await _send_progress_update(
            analyze_project_packages.request.id, job_id,
            "package_analysis", 1, 5, f"Found {len(package_files)} package files"
        )
        
        # Perform package analysis
        async with package_intelligence_service as service:
            await _send_progress_update(
                analyze_project_packages.request.id, job_id,
                "package_analysis", 2, 5, "Analyzing dependencies"
            )
            
            analysis_results = await service.analyze_project_dependencies(
                project_path, package_files
            )
            
            await _send_progress_update(
                analyze_project_packages.request.id, job_id,
                "package_analysis", 3, 5, "Processing security information"
            )
        
        # Store results in database
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO codemirror_analysis_results (
                    repo_id, task_id, analysis_type, results, created_at
                ) VALUES ($1, $2, $3, $4, $5)
            """, 
                UUID(repo_id) if repo_id else None, 
                analyze_project_packages.request.id, 
                "package_intelligence", 
                analysis_results, 
                datetime.utcnow()
            )
        
        # Persist package intelligence data to dedicated tables
        await service.persist_analysis_results(
            repo_id, 
            analyze_project_packages.request.id, 
            analysis_results
        )
        
        await _send_progress_update(
            analyze_project_packages.request.id, job_id,
            "package_analysis", 4, 5, "Generating insights"
        )
        
        # Generate insights from package analysis
        insights = await _generate_package_insights(analysis_results)
        
        await _send_progress_update(
            analyze_project_packages.request.id, job_id,
            "package_analysis", 5, 5, "Package analysis completed"
        )
        
        return {
            "status": "completed",
            "analysis_results": analysis_results,
            "insights": insights,
            "summary": {
                "total_dependencies": analysis_results.get('total_dependencies', 0),
                "total_vulnerabilities": analysis_results.get('total_vulnerabilities', 0),
                "package_managers": list(analysis_results.get('package_managers', {}).keys()),
                "recommendations_count": len(analysis_results.get('recommendations', []))
            }
        }
        
    except Exception as e:
        logger.error(f"Package analysis async failed: {e}", exc_info=True)
        await _send_progress_update(
            analyze_project_packages.request.id, job_id,
            "package_analysis", 0, 5, f"Analysis failed: {str(e)}"
        )
        return {"error": str(e), "status": "failed"}


@celery_app.task(name="app.workers.package_intelligence_tasks.check_package_security")
def check_package_security(
    package_name: str,
    package_manager: str,
    version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check security vulnerabilities for a specific package.
    
    Args:
        package_name: Name of the package
        package_manager: Package manager (npm, pypi, cargo, maven)
        version: Specific version to check (optional)
    
    Returns:
        Security analysis results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _check_package_security_async(package_name, package_manager, version)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Package security check failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _check_package_security_async(
    package_name: str,
    package_manager: str,
    version: Optional[str]
) -> Dict[str, Any]:
    """Async implementation of package security check"""
    
    try:
        async with package_intelligence_service as service:
            # Get package information
            if package_manager == 'npm':
                package_info = await service._get_npm_package_info(package_name)
            elif package_manager == 'pypi':
                package_info = await service._get_pypi_package_info(package_name)
            elif package_manager == 'cargo':
                package_info = await service._get_cargo_package_info(package_name)
            elif package_manager == 'maven':
                package_info = await service._get_maven_package_info(package_name)
            else:
                return {"error": f"Unsupported package manager: {package_manager}"}
            
            if not package_info:
                return {"error": f"Package not found: {package_name}"}
            
            # Check for vulnerabilities (placeholder - implement specific checks later)
            vulnerabilities = []
            
            # Check for maintenance issues
            maintenance_issues = []
            if package_info.deprecated:
                maintenance_issues.append("Package is deprecated")
            
            if package_info.last_updated:
                days_since_update = (datetime.utcnow() - package_info.last_updated.replace(tzinfo=None)).days
                if days_since_update > 365:
                    maintenance_issues.append(f"Package hasn't been updated in {days_since_update} days")
            
            return {
                "status": "completed",
                "package_info": package_info.__dict__,
                "vulnerabilities": vulnerabilities,
                "maintenance_issues": maintenance_issues,
                "security_score": _calculate_security_score(package_info, vulnerabilities, maintenance_issues)
            }
            
    except Exception as e:
        logger.error(f"Package security check async failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}


@celery_app.task(name="app.workers.package_intelligence_tasks.update_package_cache")
def update_package_cache(
    package_manager: str,
    package_names: List[str]
) -> Dict[str, Any]:
    """
    Update package information cache for specified packages.
    
    Args:
        package_manager: Package manager type
        package_names: List of package names to update
    
    Returns:
        Cache update results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _update_package_cache_async(package_manager, package_names)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Package cache update failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}
    finally:
        loop.close()


async def _update_package_cache_async(
    package_manager: str,
    package_names: List[str]
) -> Dict[str, Any]:
    """Async implementation of package cache update"""
    
    updated_count = 0
    failed_count = 0
    
    try:
        async with package_intelligence_service as service:
            for package_name in package_names:
                try:
                    # Force cache refresh by getting package info
                    if package_manager == 'npm':
                        package_info = await service._get_npm_package_info(package_name)
                    elif package_manager == 'pypi':
                        package_info = await service._get_pypi_package_info(package_name)
                    elif package_manager == 'cargo':
                        package_info = await service._get_cargo_package_info(package_name)
                    elif package_manager == 'maven':
                        package_info = await service._get_maven_package_info(package_name)
                    else:
                        failed_count += 1
                        continue
                    
                    if package_info:
                        updated_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to update cache for {package_name}: {e}")
                    failed_count += 1
        
        return {
            "status": "completed",
            "updated_count": updated_count,
            "failed_count": failed_count,
            "total_requested": len(package_names)
        }
        
    except Exception as e:
        logger.error(f"Package cache update async failed: {e}", exc_info=True)
        return {"error": str(e), "status": "failed"}


async def _generate_package_insights(analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate insights from package analysis results"""
    
    insights = []
    
    try:
        total_deps = analysis_results.get('total_dependencies', 0)
        total_vulns = analysis_results.get('total_vulnerabilities', 0)
        maintenance_issues = analysis_results.get('maintenance_issues', [])
        recommendations = analysis_results.get('recommendations', [])
        
        # Security insights
        if total_vulns > 0:
            severity = "high" if total_vulns >= 5 else "medium" if total_vulns >= 2 else "low"
            insights.append({
                "type": "security",
                "severity": severity,
                "title": f"{total_vulns} Security Vulnerabilities Found",
                "description": f"Found {total_vulns} potential security vulnerabilities in project dependencies",
                "recommendation": "Review and update vulnerable packages to their latest secure versions",
                "metadata": {"vulnerability_count": total_vulns}
            })
        
        # Maintenance insights
        if len(maintenance_issues) > 0:
            insights.append({
                "type": "maintenance",
                "severity": "medium",
                "title": f"{len(maintenance_issues)} Maintenance Issues",
                "description": f"Found {len(maintenance_issues)} packages with maintenance concerns",
                "recommendation": "Update stale packages and replace deprecated dependencies",
                "metadata": {"issues": maintenance_issues[:5]}  # Limit to first 5
            })
        
        # License insights
        license_summary = analysis_results.get('license_summary', {})
        if license_summary:
            insights.append({
                "type": "licensing",
                "severity": "low",
                "title": "License Compliance Review",
                "description": f"Project uses {len(license_summary)} different license types",
                "recommendation": "Review license compatibility for your project's intended use",
                "metadata": {"licenses": license_summary}
            })
        
        # Dependency health insights
        if total_deps > 50:
            insights.append({
                "type": "architecture",
                "severity": "medium",
                "title": "High Dependency Count",
                "description": f"Project has {total_deps} dependencies which may impact maintainability",
                "recommendation": "Consider reducing dependencies or implementing dependency management strategies",
                "metadata": {"dependency_count": total_deps}
            })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating package insights: {e}")
        return []


def _calculate_security_score(package_info, vulnerabilities: List, maintenance_issues: List) -> float:
    """Calculate a security score for a package (0-1, higher is better)"""
    
    score = 1.0
    
    # Reduce score for vulnerabilities
    score -= len(vulnerabilities) * 0.2
    
    # Reduce score for maintenance issues
    score -= len(maintenance_issues) * 0.1
    
    # Reduce score if deprecated
    if hasattr(package_info, 'deprecated') and package_info.deprecated:
        score -= 0.3
    
    # Reduce score for old packages
    if hasattr(package_info, 'last_updated') and package_info.last_updated:
        days_since_update = (datetime.utcnow() - package_info.last_updated.replace(tzinfo=None)).days
        if days_since_update > 365:
            score -= 0.2
        elif days_since_update > 180:
            score -= 0.1
    
    return max(0.0, min(1.0, score))


async def _send_progress_update(
    task_id: str, 
    job_id: str, 
    progress_type: str, 
    current_value: int,
    total_value: Optional[int] = None,
    message: Optional[str] = None
):
    """Send progress update (reuse from codemirror_tasks.py)"""
    try:
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO codemirror_task_progress (
                    task_id, job_id, progress_type, current_value, 
                    total_value, message
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                task_id, job_id, progress_type, current_value,
                total_value, message
            )
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")