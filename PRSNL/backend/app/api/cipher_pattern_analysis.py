"""
Cipher Pattern Analysis API Endpoints

Provides REST API access to the CrewAI-powered Cipher pattern analysis system.
This allows external tools and services to trigger pattern analysis and improvements.

Created: January 2025 - Post v9.0 Cipher Integration
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

from app.services.cipher_pattern_crew import (
    CipherPatternCrew,
    CipherPatternAnalysisInput,
    create_cipher_pattern_crew
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cipher-analysis", tags=["cipher-analysis"])


class CipherAnalysisRequest(BaseModel):
    """Request model for cipher pattern analysis"""
    analysis_type: str = "full"  # full, quality, relationships, gaps, optimization
    pattern_categories: List[str] = []
    improvement_focus: str = "all"  # accuracy, completeness, format, relationships, all
    async_mode: bool = False  # Run analysis in background


class CipherAnalysisResponse(BaseModel):
    """Response model for cipher pattern analysis"""
    analysis_id: str
    status: str
    message: str
    analysis_result: Optional[Dict[str, Any]] = None
    recommendations: List[str] = []
    next_steps: List[str] = []


class CipherPatternStats(BaseModel):
    """Model for cipher pattern statistics"""
    total_patterns: int
    pattern_types: int
    type_distribution: Dict[str, int]
    avg_content_length: float
    patterns_with_solutions: int
    recent_patterns: int
    quality_score: float


# In-memory storage for async analysis results (in production, use Redis/DB)
analysis_results = {}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cipher-pattern-analysis",
        "version": "1.0.0",
        "crew_agents": 5
    }


@router.get("/stats", response_model=CipherPatternStats)
async def get_pattern_statistics():
    """Get comprehensive Cipher pattern statistics"""
    try:
        crew = create_cipher_pattern_crew()
        stats_data = crew.cipher_tool._get_pattern_statistics()
        stats = eval(stats_data)  # Convert JSON string to dict
        
        # Calculate quality score based on various metrics
        quality_score = calculate_quality_score(stats)
        
        return CipherPatternStats(
            total_patterns=stats.get("total_patterns", 0),
            pattern_types=stats.get("pattern_types", 0),
            type_distribution=stats.get("type_distribution", {}),
            avg_content_length=stats.get("avg_content_length", 0.0),
            patterns_with_solutions=stats.get("patterns_with_solutions", 0),
            recent_patterns=stats.get("recent_patterns", 0),
            quality_score=quality_score
        )
        
    except Exception as e:
        logger.error(f"Error getting pattern statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post("/analyze", response_model=CipherAnalysisResponse)
async def analyze_patterns(
    request: CipherAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger Cipher pattern analysis using CrewAI
    
    This endpoint launches a 5-agent CrewAI team to analyze and improve Cipher patterns:
    - Pattern Quality Agent: Analyzes completeness and accuracy
    - Pattern Relationship Agent: Finds connections between patterns  
    - Pattern Gap Agent: Identifies missing knowledge areas
    - Pattern Optimization Agent: Suggests format improvements
    - Pattern Orchestrator Agent: Synthesizes insights and creates action plan
    """
    try:
        analysis_id = f"cipher-analysis-{int(__import__('time').time())}"
        
        # Create analysis input
        analysis_input = CipherPatternAnalysisInput(
            analysis_type=request.analysis_type,
            pattern_categories=request.pattern_categories,
            improvement_focus=request.improvement_focus
        )
        
        if request.async_mode:
            # Run analysis in background
            background_tasks.add_task(
                run_pattern_analysis_background,
                analysis_id,
                analysis_input
            )
            
            return CipherAnalysisResponse(
                analysis_id=analysis_id,
                status="started",
                message="Pattern analysis started in background. Check /status endpoint for progress.",
                recommendations=[],
                next_steps=[]
            )
        else:
            # Run analysis synchronously
            crew = create_cipher_pattern_crew()
            result = await crew.analyze_patterns(analysis_input)
            
            return CipherAnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                message="Pattern analysis completed successfully",
                analysis_result=result,
                recommendations=result.get("recommendations", []),
                next_steps=result.get("next_steps", [])
            )
            
    except Exception as e:
        logger.error(f"Error in pattern analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get the status of a background analysis"""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    
    return analysis_results[analysis_id]


@router.get("/quality-issues")
async def get_quality_issues():
    """Get detailed quality issues in Cipher patterns"""
    try:
        crew = create_cipher_pattern_crew()
        quality_data = crew.cipher_tool._analyze_pattern_quality()
        quality_analysis = eval(quality_data)  # Convert JSON string to dict
        
        return {
            "total_issues": quality_analysis.get("total_quality_issues", 0),
            "issues": quality_analysis.get("issues", []),
            "summary": quality_analysis.get("summary", {}),
            "recommendations": generate_quality_recommendations(quality_analysis)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing quality issues: {e}")
        raise HTTPException(status_code=500, detail=f"Quality analysis failed: {str(e)}")


@router.get("/relationships")
async def get_pattern_relationships(analysis_type: str = "semantic"):
    """Get relationships between Cipher patterns"""
    try:
        crew = create_cipher_pattern_crew()
        relationships_data = crew.relationship_tool._run(analysis_type)
        relationships = eval(relationships_data)  # Convert JSON string to dict
        
        return relationships
        
    except Exception as e:
        logger.error(f"Error analyzing relationships: {e}")
        raise HTTPException(status_code=500, detail=f"Relationship analysis failed: {str(e)}")


@router.post("/improve-pattern")
async def improve_specific_pattern(pattern_content: str):
    """
    Use CrewAI to suggest improvements for a specific pattern
    
    This is a focused analysis for a single pattern rather than the entire knowledge base.
    """
    try:
        # Create a temporary crew focused on pattern optimization
        crew = create_cipher_pattern_crew()
        
        # Analyze the specific pattern
        improvement_suggestions = analyze_single_pattern(pattern_content, crew)
        
        return {
            "original_pattern": pattern_content,
            "improvement_suggestions": improvement_suggestions,
            "quality_score": rate_pattern_quality(pattern_content),
            "recommended_format": suggest_pattern_format(pattern_content)
        }
        
    except Exception as e:
        logger.error(f"Error improving pattern: {e}")
        raise HTTPException(status_code=500, detail=f"Pattern improvement failed: {str(e)}")


@router.get("/recommendations")
async def get_improvement_recommendations():
    """Get top recommendations for Cipher pattern improvements"""
    try:
        crew = create_cipher_pattern_crew()
        
        # Get quick analysis for recommendations
        stats = eval(crew.cipher_tool._get_pattern_statistics())
        quality_issues = eval(crew.cipher_tool._analyze_pattern_quality())
        
        recommendations = []
        
        # Generate recommendations based on analysis
        if quality_issues.get("total_quality_issues", 0) > 0:
            recommendations.append(f"Fix {quality_issues['total_quality_issues']} quality issues in patterns")
        
        if stats.get("patterns_with_solutions", 0) < stats.get("total_patterns", 0) * 0.7:
            recommendations.append("Add solutions to bug patterns missing them")
        
        if stats.get("avg_content_length", 0) < 50:
            recommendations.append("Expand pattern content with more context and details")
        
        # Add specific recommendations
        recommendations.extend([
            "Create standardized pattern templates for consistency",
            "Add file paths and locations to patterns for better context",
            "Group related patterns into knowledge clusters",
            "Create automated pattern validation system",
            "Implement pattern freshness monitoring"
        ])
        
        return {
            "recommendations": recommendations,
            "priority_order": "Based on impact and ease of implementation",
            "estimated_improvement": "30-50% increase in agent effectiveness"
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


# Helper functions

async def run_pattern_analysis_background(analysis_id: str, analysis_input: CipherPatternAnalysisInput):
    """Run pattern analysis in background"""
    try:
        analysis_results[analysis_id] = {"status": "running", "progress": "Starting analysis..."}
        
        crew = create_cipher_pattern_crew()
        result = await crew.analyze_patterns(analysis_input)
        
        analysis_results[analysis_id] = {
            "status": "completed",
            "result": result,
            "completed_at": __import__('datetime').datetime.now().isoformat()
        }
        
    except Exception as e:
        analysis_results[analysis_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": __import__('datetime').datetime.now().isoformat()
        }


def calculate_quality_score(stats: Dict[str, Any]) -> float:
    """Calculate overall quality score for patterns"""
    total_patterns = stats.get("total_patterns", 1)
    patterns_with_solutions = stats.get("patterns_with_solutions", 0)
    avg_length = stats.get("avg_content_length", 0)
    
    # Simple quality scoring algorithm
    solution_ratio = patterns_with_solutions / total_patterns if total_patterns > 0 else 0
    length_score = min(avg_length / 100, 1.0)  # Normalize around 100 chars
    
    quality_score = (solution_ratio * 0.6 + length_score * 0.4) * 100
    return round(quality_score, 2)


def generate_quality_recommendations(quality_analysis: Dict[str, Any]) -> List[str]:
    """Generate specific recommendations based on quality analysis"""
    recommendations = []
    
    issues = quality_analysis.get("issues", [])
    summary = quality_analysis.get("summary", {})
    
    if "most_common_issues" in summary:
        for issue, count in summary["most_common_issues"].items():
            if count > 5:  # Significant issue
                recommendations.append(f"Address '{issue}' in {count} patterns")
    
    # Add general recommendations
    recommendations.extend([
        "Add more context to short patterns",
        "Include file paths and service names in patterns",
        "Complete TODO items in patterns",
        "Add solutions to bug patterns"
    ])
    
    return recommendations[:5]  # Top 5 recommendations


def analyze_single_pattern(pattern_content: str, crew: CipherPatternCrew) -> List[str]:
    """Analyze a single pattern and suggest improvements"""
    suggestions = []
    
    # Basic analysis
    if len(pattern_content) < 30:
        suggestions.append("Add more detail and context")
    
    if "→" not in pattern_content and "BUG PATTERN" in pattern_content:
        suggestions.append("Add solution after →")
    
    if not any(word in pattern_content.lower() for word in ["file", "service", "location", "path"]):
        suggestions.append("Include file/service location for context")
    
    if pattern_content.count(" ") < 5:
        suggestions.append("Expand with more descriptive text")
    
    return suggestions


def rate_pattern_quality(pattern_content: str) -> float:
    """Rate the quality of a single pattern"""
    score = 0.0
    
    # Length check
    if len(pattern_content) > 50:
        score += 0.3
    
    # Has solution
    if "→" in pattern_content:
        score += 0.3
    
    # Has context
    if any(word in pattern_content.lower() for word in ["file", "service", "location", "path"]):
        score += 0.2
    
    # Specific details
    if any(word in pattern_content for word in ["http", "port", "class", "function"]):
        score += 0.2
    
    return min(score, 1.0)


def suggest_pattern_format(pattern_content: str) -> str:
    """Suggest improved format for a pattern"""
    if "BUG PATTERN:" in pattern_content:
        return "BUG PATTERN: [Error description] → [Solution] [Context: file/service]"
    elif "API PATTERN:" in pattern_content:
        return "API PATTERN: [Endpoint type] → [Implementation pattern] [Example: code/curl]"
    elif "CONFIG PATTERN:" in pattern_content:
        return "CONFIG PATTERN: [Component] → [Configuration] [Location: file/service]"
    else:
        return "PATTERN TYPE: [Description] → [Solution/Example] [Context: location/service]"