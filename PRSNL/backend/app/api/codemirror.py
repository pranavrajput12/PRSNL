"""
CodeMirror API - AI-powered repository intelligence endpoints

Part of Code Cortex, provides deep code analysis and pattern recognition.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.db.database import get_db_connection
from app.services.job_persistence_service import JobPersistenceService
from app.services.codemirror_service import CodeMirrorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/code-cortex/codemirror", tags=["codemirror"])

# Request/Response Models
class AnalysisRequest(BaseModel):
    repo_id: str
    analysis_depth: str = "standard"  # quick, standard, deep
    include_patterns: bool = True
    include_insights: bool = True

class CLISyncRequest(BaseModel):
    cli_analysis_id: str
    cli_version: str
    machine_id: Optional[str] = None
    analysis_results: dict
    local_path: str
    repo_name: str

class PatternResponse(BaseModel):
    id: str
    pattern_signature: str
    pattern_type: str
    description: Optional[str]
    occurrence_count: int
    solutions: List[dict]
    confidence: float

class InsightResponse(BaseModel):
    id: str
    insight_type: str
    title: str
    description: str
    severity: Optional[str]
    recommendation: str
    confidence_score: float

class AnalysisResponse(BaseModel):
    id: str
    status: str
    job_id: Optional[str]
    analysis_type: str
    analysis_depth: str
    progress: int
    results: Optional[dict]
    insights: Optional[List[InsightResponse]]
    patterns: Optional[List[PatternResponse]]

# Endpoints
@router.post("/analyze/{repo_id}")
async def start_analysis(
    repo_id: str,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Start AI-powered repository analysis"""
    
    # Verify repo ownership
    async with get_db_connection() as db:
        repo = await db.fetchrow("""
            SELECT gr.* FROM github_repos gr
            JOIN github_accounts ga ON gr.account_id = ga.id
            WHERE gr.id = $1 AND ga.user_id = $2
        """, UUID(repo_id), current_user.id)
        
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
    
    # Create job in persistence system
    job_id = f"codemirror_{repo_id}_{datetime.now().timestamp()}"
    
    async with await get_db_connection() as conn:
        job_service = JobPersistenceService(conn)
        await job_service.create_job(
            job_id=job_id,
            job_type="crawl_ai",
            input_data={
                "repo_id": repo_id,
                "user_id": str(current_user.id),
                "analysis_type": "codemirror",
                "analysis_depth": request.analysis_depth,
                "include_patterns": request.include_patterns,
                "include_insights": request.include_insights
            },
            tags=["codemirror", "repository_analysis", request.analysis_depth]
        )
    
    # Queue background analysis
    background_tasks.add_task(
        CodeMirrorService().analyze_repository,
        repo_id,
        job_id,
        str(current_user.id),
        request.analysis_depth
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"CodeMirror analysis started with {request.analysis_depth} depth",
        "monitor_url": f"/api/persistence/status/{job_id}",
        "websocket_channel": f"codemirror.{job_id}"
    }

@router.get("/analyses/{repo_id}")
async def get_analyses(
    repo_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """Get CodeMirror analyses for a repository"""
    
    async with get_db_connection() as db:
        # Verify access
        has_access = await db.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM github_repos gr
                JOIN github_accounts ga ON gr.account_id = ga.id
                WHERE gr.id = $1 AND ga.user_id = $2
            )
        """, UUID(repo_id), current_user.id)
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get analyses
        analyses = await db.fetch("""
            SELECT 
                ca.id,
                ca.analysis_type,
                ca.analysis_depth,
                ca.results,
                ca.security_score,
                ca.performance_score,
                ca.quality_score,
                ca.created_at,
                pj.status as job_status,
                pj.progress_percentage as progress
            FROM codemirror_analyses ca
            LEFT JOIN processing_jobs pj ON ca.job_id = pj.job_id
            WHERE ca.repo_id = $1
            ORDER BY ca.created_at DESC
            LIMIT $2
        """, UUID(repo_id), limit)
        
        return [dict(analysis) for analysis in analyses]

@router.get("/patterns")
async def get_patterns(
    pattern_type: Optional[str] = None,
    min_occurrences: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Get detected code patterns for the user"""
    
    async with get_db_connection() as db:
        query = """
            SELECT 
                id,
                pattern_signature,
                pattern_type,
                description,
                occurrence_count,
                repository_count,
                solutions,
                ai_confidence as confidence,
                last_seen_at
            FROM codemirror_patterns
            WHERE user_id = $1 AND occurrence_count >= $2
        """
        
        params = [current_user.id, min_occurrences]
        
        if pattern_type:
            query += " AND pattern_type = $3"
            params.append(pattern_type)
        
        query += " ORDER BY occurrence_count DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        patterns = await db.fetch(query, *params)
        
        return [
            PatternResponse(
                id=str(p['id']),
                pattern_signature=p['pattern_signature'],
                pattern_type=p['pattern_type'],
                description=p['description'],
                occurrence_count=p['occurrence_count'],
                solutions=p['solutions'] or [],
                confidence=p['confidence'] or 0.0
            )
            for p in patterns
        ]

@router.get("/insights/{analysis_id}")
async def get_insights(
    analysis_id: str,
    insight_type: Optional[str] = None,
    status: str = Query("open", regex="^(open|acknowledged|applied|dismissed)$"),
    current_user = Depends(get_current_user)
):
    """Get insights from a specific analysis"""
    
    async with get_db_connection() as db:
        # Verify access
        has_access = await db.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM codemirror_analyses ca
                JOIN github_repos gr ON ca.repo_id = gr.id
                JOIN github_accounts ga ON gr.account_id = ga.id
                WHERE ca.id = $1 AND ga.user_id = $2
            )
        """, UUID(analysis_id), current_user.id)
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get insights
        query = """
            SELECT 
                id,
                insight_type,
                title,
                description,
                severity,
                recommendation,
                code_before,
                code_after,
                confidence_score,
                status
            FROM codemirror_insights
            WHERE analysis_id = $1 AND status = $2
        """
        
        params = [UUID(analysis_id), status]
        
        if insight_type:
            query += " AND insight_type = $3"
            params.append(insight_type)
        
        query += " ORDER BY confidence_score DESC"
        
        insights = await db.fetch(query, *params)
        
        return [
            InsightResponse(
                id=str(i['id']),
                insight_type=i['insight_type'],
                title=i['title'],
                description=i['description'],
                severity=i['severity'],
                recommendation=i['recommendation'],
                confidence_score=i['confidence_score']
            )
            for i in insights
        ]

@router.put("/insights/{insight_id}/status")
async def update_insight_status(
    insight_id: str,
    status: str = Query(..., regex="^(acknowledged|applied|dismissed)$"),
    current_user = Depends(get_current_user)
):
    """Update the status of an insight"""
    
    async with get_db_connection() as db:
        # Verify ownership
        has_access = await db.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM codemirror_insights ci
                JOIN codemirror_analyses ca ON ci.analysis_id = ca.id
                JOIN github_repos gr ON ca.repo_id = gr.id
                JOIN github_accounts ga ON gr.account_id = ga.id
                WHERE ci.id = $1 AND ga.user_id = $2
            )
        """, UUID(insight_id), current_user.id)
        
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update status
        timestamp_field = f"{status}_at"
        await db.execute(f"""
            UPDATE codemirror_insights
            SET status = $1, {timestamp_field} = NOW()
            WHERE id = $2
        """, status, UUID(insight_id))
        
        return {"message": f"Insight {status} successfully"}

@router.post("/cli/sync")
async def sync_cli_analysis(
    request: CLISyncRequest,
    current_user = Depends(get_current_user)
):
    """Sync analysis results from CLI tool"""
    
    async with get_db_connection() as db:
        # Create sync token
        import secrets
        sync_token = secrets.token_urlsafe(32)
        
        # Check if repo mapping exists
        repo_mapping = await db.fetchrow("""
            SELECT id, repo_id FROM codemirror_repo_mappings
            WHERE user_id = $1 AND local_path = $2
        """, current_user.id, request.local_path)
        
        if not repo_mapping:
            # Create new mapping
            mapping_id = await db.fetchval("""
                INSERT INTO codemirror_repo_mappings (
                    user_id, local_path, repo_name, 
                    integrations, dependencies, cli_version
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, 
                current_user.id, 
                request.local_path, 
                request.repo_name,
                request.analysis_results.get('integrations', {}),
                request.analysis_results.get('dependencies', {}),
                request.cli_version
            )
            repo_id = None
        else:
            mapping_id = repo_mapping['id']
            repo_id = repo_mapping['repo_id']
        
        # Create analysis record
        analysis_id = await db.fetchval("""
            INSERT INTO codemirror_analyses (
                repo_id, analysis_type, analysis_depth,
                results, file_count, total_lines,
                languages_detected, frameworks_detected,
                security_score, performance_score, quality_score
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """,
            repo_id,
            'cli',
            request.analysis_results.get('depth', 'standard'),
            request.analysis_results,
            request.analysis_results.get('file_count', 0),
            request.analysis_results.get('total_lines', 0),
            request.analysis_results.get('languages', []),
            request.analysis_results.get('frameworks', []),
            request.analysis_results.get('scores', {}).get('security'),
            request.analysis_results.get('scores', {}).get('performance'),
            request.analysis_results.get('scores', {}).get('quality')
        )
        
        # Create sync record
        await db.execute("""
            INSERT INTO codemirror_cli_sync (
                user_id, sync_token, cli_analysis_id,
                web_analysis_id, cli_version, machine_id,
                sync_status, synced_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
        """,
            current_user.id,
            sync_token,
            request.cli_analysis_id,
            analysis_id,
            request.cli_version,
            request.machine_id,
            'synced'
        )
        
        # Process patterns and insights in background
        service = CodeMirrorService()
        await service.process_cli_results(
            str(analysis_id),
            str(current_user.id),
            request.analysis_results
        )
        
        return {
            "sync_token": sync_token,
            "analysis_id": str(analysis_id),
            "status": "synced",
            "message": "CLI analysis synced successfully"
        }

@router.post("/synthesize")
async def synthesize_solution(
    problem_description: str,
    file_context: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Synthesize a solution based on detected patterns and past solutions"""
    
    service = CodeMirrorService()
    solution = await service.synthesize_solution(
        user_id=str(current_user.id),
        problem_description=problem_description,
        file_context=file_context
    )
    
    return solution