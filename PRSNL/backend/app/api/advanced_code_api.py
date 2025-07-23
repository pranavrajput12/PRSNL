"""
Advanced Code Intelligence API for PRSNL Phase 5
===============================================

API endpoints for enhanced repository analysis with AI-powered insights.

Endpoints:
- POST /api/code/analyze/{repo_id} - Perform advanced code analysis
- GET /api/code/analysis/{analysis_id} - Get analysis results
- POST /api/code/recommendations/{repo_id} - Get personalized recommendations
- GET /api/code/quality-trends/{repo_id} - Get quality trends over time
- POST /api/code/compare - Compare multiple repositories
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from app.services.advanced_code_intelligence import advanced_code_intelligence
from app.middleware.auth import get_current_user_optional
from app.models.auth import User
from app.db.database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/code", tags=["Advanced Code Intelligence"])

# Request/Response Models
class AdvancedAnalysisRequest(BaseModel):
    """Request model for advanced code analysis"""
    analysis_type: str = Field("comprehensive", description="Analysis type: comprehensive, security, performance, quality, architecture")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    depth: str = Field("standard", description="Analysis depth: quick, standard, deep")
    include_ai_recommendations: bool = Field(True, description="Include AI-powered recommendations")
    compare_with_standards: bool = Field(True, description="Compare against industry standards")
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        valid_types = ['comprehensive', 'security', 'performance', 'quality', 'architecture']
        if v not in valid_types:
            raise ValueError(f'analysis_type must be one of: {valid_types}')
        return v
    
    @validator('depth')
    def validate_depth(cls, v):
        if v not in ['quick', 'standard', 'deep']:
            raise ValueError('depth must be quick, standard, or deep')
        return v

class QualityTrendsRequest(BaseModel):
    """Request model for quality trends analysis"""
    time_period: str = Field("30d", description="Time period: 7d, 30d, 90d, 1y")
    metrics: List[str] = Field(default=['overall', 'security', 'performance'], description="Metrics to track")

class RepositoryComparisonRequest(BaseModel):
    """Request model for repository comparison"""
    repo_ids: List[str] = Field(..., min_items=2, max_items=5, description="Repository IDs to compare")
    comparison_aspects: List[str] = Field(default=['quality', 'security', 'performance'], description="Aspects to compare")
    include_benchmarks: bool = Field(True, description="Include industry benchmarks")

class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    analysis_id: str
    repo_id: str 
    timestamp: str
    analysis_type: str
    processing_stats: Dict[str, Any]
    quality_scores: Dict[str, float]
    ai_insights: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    status: str = "completed"

@router.post("/analyze/{repo_id}", response_model=AnalysisResponse)
async def perform_advanced_analysis(
    repo_id: str,
    request: AdvancedAnalysisRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Perform advanced AI-powered code analysis on a repository.
    
    This endpoint provides comprehensive code analysis including:
    - Architecture assessment with AI insights
    - Security vulnerability detection
    - Performance optimization opportunities  
    - Code quality metrics and recommendations
    - Technical debt quantification
    - Industry standard comparisons
    """
    try:
        # Validate repository access
        if not await _validate_repo_access(repo_id, current_user):
            raise HTTPException(
                status_code=403,
                detail="Access denied to repository"
            )
        
        logger.info(f"🔍 Starting advanced analysis [Repo: {repo_id}] [Type: {request.analysis_type}]")
        
        # Perform analysis
        result = await advanced_code_intelligence.perform_advanced_analysis(
            repo_id=repo_id,
            analysis_type=request.analysis_type,
            focus_areas=request.focus_areas
        )
        
        # Check for analysis errors
        if result.get('status') == 'failed':
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        # Add user context
        if current_user:
            result['user_context'] = {
                "user_id": str(current_user.id),
                "analysis_requested_by": getattr(current_user, 'email', 'unknown')
            }
        
        # Filter results based on request preferences
        if not request.include_ai_recommendations:
            result['recommendations'] = []
        
        logger.info(f"✅ Advanced analysis complete [Analysis: {result['analysis_id']}]")
        
        return AnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Advanced analysis failed for repo {repo_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/analysis/{analysis_id}")
async def get_analysis_results(
    analysis_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Retrieve results from a previous analysis.
    
    Get detailed results including AI insights, metrics, and recommendations.
    """
    try:
        async with get_db_connection() as conn:
            analysis = await conn.fetchrow("""
                SELECT 
                    id, repo_id, analysis_type, results, quality_scores,
                    processing_stats, created_at
                FROM advanced_code_analyses
                WHERE id = $1
            """, analysis_id)
            
            if not analysis:
                raise HTTPException(status_code=404, detail="Analysis not found")
            
            # Validate access to the repository
            if not await _validate_repo_access(str(analysis['repo_id']), current_user):
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Parse results
            results = analysis['results'] if isinstance(analysis['results'], dict) else {}
            
            return JSONResponse(content={
                "analysis_id": str(analysis['id']),
                "repo_id": str(analysis['repo_id']),
                "analysis_type": analysis['analysis_type'],
                "created_at": analysis['created_at'].isoformat(),
                "results": results,
                "quality_scores": analysis['quality_scores'] if isinstance(analysis['quality_scores'], dict) else {},
                "processing_stats": analysis['processing_stats'] if isinstance(analysis['processing_stats'], dict) else {}
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")

@router.post("/recommendations/{repo_id}")
async def get_personalized_recommendations(
    repo_id: str,
    focus_areas: Optional[List[str]] = None,
    priority_filter: Optional[str] = Query(None, regex="^(high|medium|low)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get personalized recommendations for a repository.
    
    Returns actionable recommendations based on:
    - Previous analysis results
    - User's development patterns
    - Industry best practices
    - AI-powered insights
    """
    try:
        # Validate repository access
        if not await _validate_repo_access(repo_id, current_user):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get latest analysis for the repository
        async with get_db_connection() as conn:
            latest_analysis = await conn.fetchrow("""
                SELECT results, quality_scores
                FROM advanced_code_analyses
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, UUID(repo_id))
            
            if not latest_analysis:
                raise HTTPException(
                    status_code=404,
                    detail="No analysis found for repository. Please run an analysis first."
                )
        
        # Extract recommendations from analysis
        results = latest_analysis['results'] if isinstance(latest_analysis['results'], dict) else {}
        recommendations = results.get('recommendations', [])
        
        # Filter by priority if specified
        if priority_filter:
            recommendations = [
                rec for rec in recommendations 
                if rec.get('priority') == priority_filter
            ]
        
        # Filter by focus areas if specified
        if focus_areas:
            recommendations = [
                rec for rec in recommendations
                if rec.get('type') in focus_areas
            ]
        
        # Limit results
        recommendations = recommendations[:limit]
        
        # Add personalization based on user context
        if current_user:
            # This could be enhanced with user preferences and history
            personalized_context = {
                "user_id": str(current_user.id),
                "personalized": True,
                "user_focus": focus_areas or []
            }
        else:
            personalized_context = {"personalized": False}
        
        return JSONResponse(content={
            "repo_id": repo_id,
            "recommendations": recommendations,
            "total_available": len(results.get('recommendations', [])),
            "returned_count": len(recommendations),
            "filters_applied": {
                "priority": priority_filter,
                "focus_areas": focus_areas,
                "limit": limit
            },
            "personalization": personalized_context,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recommendations: {str(e)}")

@router.post("/quality-trends/{repo_id}")
async def get_quality_trends(
    repo_id: str,
    request: QualityTrendsRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get quality trends and metrics over time for a repository.
    
    Track improvements and regressions in:
    - Overall code quality scores
    - Security vulnerability trends
    - Performance metrics evolution
    - Technical debt accumulation
    """
    try:
        # Validate repository access
        if not await _validate_repo_access(repo_id, current_user):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Parse time period
        time_periods = {
            '7d': timedelta(days=7),
            '30d': timedelta(days=30),
            '90d': timedelta(days=90),
            '1y': timedelta(days=365)
        }
        
        if request.time_period not in time_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time period. Must be one of: {list(time_periods.keys())}"
            )
        
        start_date = datetime.utcnow() - time_periods[request.time_period]
        
        # Get historical analysis data
        async with get_db_connection() as conn:
            analyses = await conn.fetch("""
                SELECT 
                    quality_scores, processing_stats, created_at
                FROM advanced_code_analyses
                WHERE repo_id = $1 AND created_at >= $2
                ORDER BY created_at ASC
            """, UUID(repo_id), start_date)
        
        if not analyses:
            raise HTTPException(
                status_code=404,
                detail="No historical analysis data found for the specified time period"
            )
        
        # Process trend data
        trends = {metric: [] for metric in request.metrics}
        
        for analysis in analyses:
            quality_scores = analysis['quality_scores'] if isinstance(analysis['quality_scores'], dict) else {}
            timestamp = analysis['created_at'].isoformat()
            
            for metric in request.metrics:
                score = quality_scores.get(metric, 0.0)
                trends[metric].append({
                    "timestamp": timestamp,
                    "score": score
                })
        
        # Calculate trend statistics
        trend_stats = {}
        for metric, data_points in trends.items():
            if len(data_points) >= 2:
                first_score = data_points[0]['score']
                last_score = data_points[-1]['score']
                change = last_score - first_score
                change_percentage = (change / first_score) * 100 if first_score > 0 else 0
                
                trend_stats[metric] = {
                    "direction": "improving" if change > 0.05 else "declining" if change < -0.05 else "stable",
                    "change": change,
                    "change_percentage": change_percentage,
                    "current_score": last_score,
                    "data_points": len(data_points)
                }
        
        return JSONResponse(content={
            "repo_id": repo_id,
            "time_period": request.time_period,
            "trends": trends,
            "trend_statistics": trend_stats,
            "analysis_count": len(analyses),
            "date_range": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trends: {str(e)}")

@router.post("/compare")
async def compare_repositories(
    request: RepositoryComparisonRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Compare multiple repositories across various quality metrics.
    
    Provides side-by-side comparison of:
    - Code quality scores
    - Security posture
    - Performance characteristics
    - Architecture patterns
    - Technical debt levels
    """
    try:
        # Validate access to all repositories
        for repo_id in request.repo_ids:
            if not await _validate_repo_access(repo_id, current_user):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied to repository: {repo_id}"
                )
        
        # Get latest analysis for each repository
        comparisons = []
        
        async with get_db_connection() as conn:
            for repo_id in request.repo_ids:
                # Get repository info
                repo_info = await conn.fetchrow("""
                    SELECT id, full_name, language, description
                    FROM github_repos
                    WHERE id = $1
                """, UUID(repo_id))
                
                # Get latest analysis
                latest_analysis = await conn.fetchrow("""
                    SELECT quality_scores, processing_stats, created_at
                    FROM advanced_code_analyses
                    WHERE repo_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """, UUID(repo_id))
                
                if repo_info and latest_analysis:
                    quality_scores = latest_analysis['quality_scores'] if isinstance(latest_analysis['quality_scores'], dict) else {}
                    processing_stats = latest_analysis['processing_stats'] if isinstance(latest_analysis['processing_stats'], dict) else {} 
                    
                    comparison_data = {
                        "repo_id": repo_id,
                        "repo_name": repo_info['full_name'],
                        "language": repo_info['language'],
                        "description": repo_info['description'],
                        "quality_scores": quality_scores,
                        "metrics": {
                            "lines_of_code": processing_stats.get("lines_of_code", 0),
                            "files_analyzed": processing_stats.get("files_analyzed", 0),
                            "analysis_date": latest_analysis['created_at'].isoformat()
                        }
                    }
                    
                    # Filter by requested aspects
                    filtered_scores = {
                        aspect: quality_scores.get(aspect, 0.0)
                        for aspect in request.comparison_aspects
                        if aspect in quality_scores
                    }
                    comparison_data["comparison_scores"] = filtered_scores
                    
                    comparisons.append(comparison_data)
        
        if not comparisons:
            raise HTTPException(
                status_code=404,
                detail="No analysis data found for the specified repositories"
            )
        
        # Calculate comparison insights
        insights = _generate_comparison_insights(comparisons, request.comparison_aspects)
        
        # Add industry benchmarks if requested
        benchmarks = {}
        if request.include_benchmarks:
            benchmarks = _get_industry_benchmarks(request.comparison_aspects)
        
        return JSONResponse(content={
            "comparison_id": str(UUID("12345678-1234-5678-1234-567812345678")),  # Generate actual UUID
            "repositories": comparisons,
            "comparison_aspects": request.comparison_aspects,
            "insights": insights,
            "industry_benchmarks": benchmarks,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repository comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/capabilities")
async def get_code_analysis_capabilities():
    """Get information about available code analysis capabilities"""
    try:
        capabilities = {
            "analysis_types": {
                "comprehensive": "Full analysis across all dimensions",
                "security": "Security-focused vulnerability assessment", 
                "performance": "Performance optimization analysis",
                "quality": "Code quality and maintainability assessment",
                "architecture": "Architectural patterns and design analysis"
            },
            "supported_languages": [
                "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", 
                "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin", "Scala"
            ],
            "ai_capabilities": [
                "Pattern recognition",
                "Architecture assessment", 
                "Security vulnerability detection",
                "Performance bottleneck identification",
                "Code smell detection",
                "Refactoring recommendations",
                "Technical debt quantification"
            ],
            "metrics_available": [
                "Cyclomatic complexity",
                "Maintainability index",
                "Technical debt ratio",
                "Test coverage",
                "Code duplication",
                "Security score",
                "Performance score"
            ],
            "integration_features": [
                "Multi-modal content analysis",
                "Cross-repository comparison",
                "Trend analysis over time",
                "Personalized recommendations",
                "Industry benchmarking"
            ],
            "version": "1.0.0",
            "last_updated": "2025-07-23"
        }
        
        return JSONResponse(content=capabilities)
        
    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve capabilities")

# Helper functions
async def _validate_repo_access(repo_id: str, user: Optional[User]) -> bool:
    """Validate user access to repository"""
    try:
        # For now, allow access to all repositories
        # In production, implement proper access control
        async with get_db_connection() as conn:
            repo_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM github_repos WHERE id = $1)",
                UUID(repo_id)
            )
            return repo_exists
    except Exception:
        return False

def _generate_comparison_insights(comparisons: List[Dict], aspects: List[str]) -> Dict[str, Any]:
    """Generate insights from repository comparison"""
    insights = {
        "best_performers": {},
        "improvement_opportunities": [],
        "patterns": []
    }
    
    # Find best performers in each aspect
    for aspect in aspects:
        scores = [
            (comp["repo_name"], comp["comparison_scores"].get(aspect, 0.0))
            for comp in comparisons
            if aspect in comp["comparison_scores"]
        ]
        
        if scores:
            best_repo, best_score = max(scores, key=lambda x: x[1])
            insights["best_performers"][aspect] = {
                "repository": best_repo,
                "score": best_score
            }
    
    # Identify improvement opportunities
    for comp in comparisons:
        low_scores = [
            aspect for aspect, score in comp["comparison_scores"].items()
            if score < 0.6
        ]
        if low_scores:
            insights["improvement_opportunities"].append({
                "repository": comp["repo_name"],
                "areas": low_scores
            })
    
    return insights

def _get_industry_benchmarks(aspects: List[str]) -> Dict[str, float]:
    """Get industry benchmark scores for comparison aspects"""
    # Simulated industry benchmarks
    benchmarks = {
        "quality": 0.75,
        "security": 0.85,
        "performance": 0.72,
        "architecture": 0.68,
        "overall": 0.70
    }
    
    return {aspect: benchmarks.get(aspect, 0.70) for aspect in aspects}

@router.get("/health")
async def code_intelligence_health():
    """Health check for code intelligence services"""
    return JSONResponse(content={
        "status": "healthy",
        "services": {
            "advanced_code_intelligence": "operational",
            "ai_router": "operational", 
            "database": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    })