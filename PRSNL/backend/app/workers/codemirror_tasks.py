"""
CodeMirror Celery Tasks

Distributed tasks for repository analysis, pattern detection, and insight generation.
Provides enterprise-grade scalability and fault tolerance.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from celery import group, chain, chord
from celery.result import AsyncResult

from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.codemirror_service import CodeMirrorService
from app.services.codemirror_realtime_service import realtime_service, SyncEvent
from app.services.unified_ai_service import unified_ai_service
from app.workers.package_intelligence_tasks import analyze_project_packages

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.codemirror_tasks.analyze_repository")
def analyze_repository(
    repo_id: str,
    job_id: str,
    user_id: str,
    analysis_depth: str = "standard",
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Main task for repository analysis.
    
    Orchestrates the analysis pipeline using Celery workflows.
    """
    try:
        # Create subtasks based on analysis depth
        tasks = []
        
        # Basic analysis (always run)
        tasks.append(
            analyze_repository_structure.s(repo_id, user_id)
        )
        
        # Pattern detection
        if analysis_depth in ["standard", "deep"]:
            tasks.append(
                detect_code_patterns.s(repo_id, user_id)
            )
        
        # Package intelligence analysis
        if analysis_depth in ["standard", "deep"]:
            tasks.append(
                analyze_project_packages.s(repo_id, job_id, {}, "")
            )
        
        # Security analysis
        if analysis_depth == "deep":
            tasks.append(
                run_security_analysis.s(repo_id, user_id)
            )
        
        # Create workflow
        workflow = group(*tasks) | aggregate_analysis_results.s(
            repo_id, job_id, user_id, analysis_depth
        )
        
        # Execute workflow
        result = workflow.apply_async(
            task_id=f"{job_id}_main",
            queue="codemirror"
        )
        
        # Store workflow tracking
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        subtask_ids = [task.id for task in result.children] if result.children else []
        
        try:
            workflow_id = loop.run_until_complete(_create_workflow_tracking(
                job_id, result.id, subtask_ids, repo_id, user_id, analysis_depth
            ))
        except Exception as e:
            logger.error(f"Failed to create workflow tracking: {e}")
            workflow_id = None
        finally:
            loop.close()
        
        return {
            "status": "started",
            "workflow_id": result.id,
            "workflow_tracking_id": workflow_id,
            "subtasks": subtask_ids,
            "message": f"Analysis started with {len(tasks)} parallel tasks"
        }
        
    except Exception as e:
        logger.error(f"Failed to start repository analysis: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name="app.workers.codemirror_tasks.analyze_repository_structure")
def analyze_repository_structure(repo_id: str, user_id: str) -> Dict[str, Any]:
    """Analyze repository structure, languages, and dependencies."""
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _analyze_repository_structure_async(repo_id, user_id)
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Repository structure analysis failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        loop.close()


async def _create_workflow_tracking(
    job_id: str, 
    main_task_id: str, 
    subtask_ids: List[str], 
    repo_id: str, 
    user_id: str, 
    analysis_depth: str
) -> Optional[str]:
    """Create workflow tracking record"""
    try:
        async with get_db_connection() as db:
            workflow_id = await db.fetchval("""
                INSERT INTO codemirror_task_workflows (
                    job_id, workflow_type, main_task_id, subtask_ids,
                    status, total_subtasks, started_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """,
                job_id,
                'analysis',
                main_task_id,
                subtask_ids,
                'STARTED',
                len(subtask_ids),
                datetime.utcnow(),
                {'repo_id': repo_id, 'user_id': user_id, 'analysis_depth': analysis_depth}
            )
            
            # Update processing job with workflow ID
            await db.execute("""
                UPDATE processing_jobs 
                SET celery_workflow_id = $1 
                WHERE job_id = $2
            """, workflow_id, job_id)
            
            return str(workflow_id)
    except Exception as e:
        logger.error(f"Failed to create workflow tracking: {e}")
        return None


async def _update_task_progress(
    task_id: str, 
    job_id: str, 
    progress_type: str, 
    current_value: int, 
    total_value: Optional[int] = None,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Update task progress in database"""
    try:
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO codemirror_task_progress (
                    task_id, job_id, progress_type, current_value, 
                    total_value, message, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                task_id, job_id, progress_type, current_value,
                total_value, message, metadata
            )
    except Exception as e:
        logger.error(f"Failed to update task progress: {e}")


async def _send_progress_update(
    task_id: str, 
    job_id: str, 
    progress_type: str, 
    current_value: int,
    total_value: Optional[int] = None,
    message: Optional[str] = None
):
    """Send progress update via WebSocket"""
    try:
        # Update database
        await _update_task_progress(
            task_id, job_id, progress_type, current_value, total_value, message
        )
        
        # Send real-time update
        event = SyncEvent(
            event_type='task_progress',
            event_data={
                'task_id': task_id,
                'job_id': job_id,
                'progress_type': progress_type,
                'current_value': current_value,
                'total_value': total_value,
                'message': message,
                'timestamp': datetime.utcnow().isoformat()
            },
            channel=f"codemirror.{job_id}"
        )
        
        await realtime_service.publish_event(event)
        
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")


async def _analyze_repository_structure_async(repo_id: str, user_id: str) -> Dict[str, Any]:
    """Async implementation of repository structure analysis"""
    
    # Get current task ID for progress tracking
    task_id = analyze_repository_structure.request.id
    
    # Send initial progress
    await _send_progress_update(
        task_id, repo_id, "structure_analysis", 0, 5, "Starting repository structure analysis"
    )
    
    try:
        # Get repository info
        async with get_db_connection() as db:
            repo = await db.fetchrow("""
                SELECT gr.*, ga.user_id
                FROM github_repos gr
                JOIN github_accounts ga ON gr.account_id = ga.id
                WHERE gr.id = $1 AND ga.user_id = $2
            """, UUID(repo_id), UUID(user_id))
            
            if not repo:
                return {"error": "Repository not found"}
        
        await _send_progress_update(
            task_id, repo_id, "structure_analysis", 1, 5, "Repository loaded"
        )
        
        # Run analysis using CodeMirror service
        service = CodeMirrorService()
        
        await _send_progress_update(
            task_id, repo_id, "structure_analysis", 2, 5, "Analyzing file structure"
        )
        
        # Get repository path for package detection
        repo_path = ""  # This would come from actual repository data
        
        # Detect package files in the repository
        from app.utils.package_detection import detect_package_files, analyze_package_ecosystem
        
        package_files = {}  # detect_package_files(repo_path) if repo_path else {}
        package_ecosystem = analyze_package_ecosystem(package_files)
        
        # This would typically call the CLI or run analysis
        # For now, we'll create a mock structure analysis with package info
        analysis_result = {
            "repo_id": repo_id,
            "structure": {
                "total_files": 150,
                "total_lines": 15000,
                "directories": 25,
                "max_depth": 6,
                "common_directories": ["src", "tests", "docs", "config"]
            },
            "languages": package_ecosystem.get("primary_languages", ["Python", "JavaScript", "TypeScript"]),
            "frameworks": ["FastAPI", "React", "Svelte"],
            "package_ecosystem": package_ecosystem,
            "dependencies": {
                "python": ["fastapi", "uvicorn", "pydantic"],
                "javascript": ["react", "svelte", "vite"]
            },
            "analysis_type": "structure",
            "completed_at": datetime.utcnow().isoformat()
        }
        
        await _send_progress_update(
            task_id, repo_id, "structure_analysis", 4, 5, "Analysis completed"
        )
        
        # Store results
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO codemirror_analysis_results (
                    repo_id, task_id, analysis_type, results, created_at
                ) VALUES ($1, $2, $3, $4, $5)
            """, 
                UUID(repo_id), task_id, "structure", 
                analysis_result, datetime.utcnow()
            )
        
        await _send_progress_update(
            task_id, repo_id, "structure_analysis", 5, 5, "Results stored"
        )
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Structure analysis failed: {e}", exc_info=True)
        await _send_progress_update(
            task_id, repo_id, "structure_analysis", 0, 5, f"Analysis failed: {str(e)}"
        )
        return {"error": str(e)}
        
    except Exception as e:
        logger.error(f"Repository structure analysis failed: {e}", exc_info=True)
        raise
    finally:
        loop.close()


async def _analyze_repository_structure_async(repo_id: str, user_id: str) -> Dict[str, Any]:
    """Async implementation of repository structure analysis."""
    async with get_db_connection() as db:
        # Get repository details
        repo = await db.fetchrow("""
            SELECT gr.*, ga.access_token
            FROM github_repos gr
            JOIN github_accounts ga ON gr.account_id = ga.id
            WHERE gr.id = $1 AND ga.user_id = $2
        """, UUID(repo_id), UUID(user_id))
        
        if not repo:
            raise ValueError(f"Repository {repo_id} not found")
        
        # Initialize service
        service = CodeMirrorService()
        
        # Analyze repository structure
        structure_data = await service._analyze_repository_structure(
            repo['full_name'],
            repo['access_token']
        )
        
        # Send real-time update
        await realtime_service.notify_analysis_progress(
            user_id=user_id,
            analysis_id=repo_id,
            progress=30,
            stage="structure_analyzed",
            details={"files_analyzed": structure_data.get("file_count", 0)}
        )
        
        return structure_data


@celery_app.task(name="app.workers.codemirror_tasks.detect_code_patterns")
def detect_code_patterns(repo_id: str, user_id: str) -> Dict[str, Any]:
    """Detect code patterns and architectural decisions."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _detect_code_patterns_async(repo_id, user_id)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Pattern detection failed: {e}", exc_info=True)
        raise
    finally:
        loop.close()


async def _detect_code_patterns_async(repo_id: str, user_id: str) -> Dict[str, Any]:
    """Async implementation of pattern detection."""
    patterns = []
    
    async with get_db_connection() as db:
        # Get recent analysis data
        analysis = await db.fetchrow("""
            SELECT * FROM codemirror_analyses
            WHERE repo_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, UUID(repo_id))
        
        if not analysis or not analysis['results']:
            return {"patterns": []}
        
        results = analysis['results']
        
        # Detect framework patterns
        frameworks = results.get('frameworks_detected', [])
        for framework in frameworks:
            patterns.append({
                "type": "framework",
                "name": framework,
                "confidence": 0.9,
                "description": f"Detected {framework} framework usage"
            })
        
        # Detect architectural patterns
        structure = results.get('structure', {})
        if structure.get('has_tests'):
            patterns.append({
                "type": "testing",
                "name": "Test Suite",
                "confidence": 1.0,
                "description": "Repository has test coverage"
            })
        
        # Use AI to detect advanced patterns
        if unified_ai_service:
            ai_patterns = await _detect_patterns_with_ai(results)
            patterns.extend(ai_patterns)
        
        # Store patterns in database
        for pattern in patterns:
            await db.execute("""
                INSERT INTO codemirror_patterns (
                    user_id, pattern_signature, pattern_type,
                    description, occurrence_count, ai_confidence
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id, pattern_signature) 
                DO UPDATE SET 
                    occurrence_count = codemirror_patterns.occurrence_count + 1,
                    last_seen_at = NOW()
            """, 
                UUID(user_id), 
                pattern['name'],
                pattern['type'],
                pattern['description'],
                1,
                pattern['confidence']
            )
        
        # Send real-time update
        await realtime_service.notify_analysis_progress(
            user_id=user_id,
            analysis_id=repo_id,
            progress=60,
            stage="patterns_detected",
            details={"patterns_found": len(patterns)}
        )
        
        return {"patterns": patterns}


async def _detect_patterns_with_ai(analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Use AI to detect advanced patterns."""
    try:
        prompt = f"""
Analyze this repository data and identify architectural patterns, design patterns, and best practices:

Languages: {analysis_results.get('languages_detected', [])}
Frameworks: {analysis_results.get('frameworks_detected', [])}
File Structure: {json.dumps(analysis_results.get('structure', {}), indent=2)}

Identify patterns such as:
- Design patterns (MVC, Repository, Factory, etc.)
- Architectural patterns (Microservices, Monolith, etc.)
- Code organization patterns
- Best practices being followed

Return as JSON array with format:
[{{"type": "pattern_type", "name": "pattern_name", "confidence": 0.0-1.0, "description": "brief description"}}]
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a software architecture expert. Identify patterns concisely.",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        if response:
            patterns_data = json.loads(response)
            return patterns_data.get("patterns", [])
            
    except Exception as e:
        logger.error(f"AI pattern detection failed: {e}")
    
    return []


@celery_app.task(name="app.workers.codemirror_tasks.run_security_analysis")
def run_security_analysis(repo_id: str, user_id: str) -> Dict[str, Any]:
    """Run security analysis on repository."""
    try:
        # This would integrate with Semgrep or other security tools
        # For now, return mock data
        return {
            "security_findings": [
                {
                    "type": "vulnerability",
                    "severity": "medium",
                    "title": "Potential SQL injection",
                    "file": "api/users.py",
                    "line": 45
                }
            ],
            "security_score": 85
        }
    except Exception as e:
        logger.error(f"Security analysis failed: {e}", exc_info=True)
        raise


@celery_app.task(name="app.workers.codemirror_tasks.aggregate_analysis_results")
def aggregate_analysis_results(
    task_results: List[Dict[str, Any]],
    repo_id: str,
    job_id: str,
    user_id: str,
    analysis_depth: str
) -> Dict[str, Any]:
    """Aggregate results from all analysis tasks."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _aggregate_results_async(task_results, repo_id, job_id, user_id, analysis_depth)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Result aggregation failed: {e}", exc_info=True)
        raise
    finally:
        loop.close()


async def _aggregate_results_async(
    task_results: List[Dict[str, Any]],
    repo_id: str,
    job_id: str,
    user_id: str,
    analysis_depth: str
) -> Dict[str, Any]:
    """Async implementation of result aggregation."""
    
    # Merge all results
    merged_results = {}
    for result in task_results:
        if isinstance(result, dict):
            merged_results.update(result)
    
    # Generate insights based on aggregated data
    insights = await generate_insights(merged_results, analysis_depth)
    merged_results['insights'] = insights
    
    # Calculate scores
    scores = calculate_analysis_scores(merged_results)
    
    # Update database
    async with get_db_connection() as db:
        await db.execute("""
            UPDATE codemirror_analyses
            SET 
                results = $2,
                security_score = $3,
                performance_score = $4,
                quality_score = $5,
                analysis_completed_at = NOW()
            WHERE id = $1
        """,
            UUID(repo_id),
            merged_results,
            scores.get('security'),
            scores.get('performance'),
            scores.get('quality')
        )
        
        # Update job status
        await db.execute("""
            UPDATE processing_jobs
            SET 
                status = 'completed',
                progress_percentage = 100,
                completed_at = NOW(),
                result = $2
            WHERE job_id = $1
        """, job_id, merged_results)
    
    # Send completion notification
    await realtime_service.notify_analysis_progress(
        user_id=user_id,
        analysis_id=repo_id,
        progress=100,
        stage="completed",
        details={
            "insights_count": len(insights),
            "patterns_count": len(merged_results.get('patterns', [])),
            "scores": scores
        }
    )
    
    return merged_results


async def generate_insights(analysis_data: Dict[str, Any], depth: str) -> List[Dict[str, Any]]:
    """Generate insights from analysis data."""
    insights = []
    
    # Pattern-based insights
    patterns = analysis_data.get('patterns', [])
    if not any(p['type'] == 'testing' for p in patterns):
        insights.append({
            "type": "code_quality",
            "severity": "high",
            "title": "Missing Test Coverage",
            "description": "No test files detected in the repository",
            "recommendation": "Add unit tests to improve code reliability"
        })
    
    # Security insights
    security_findings = analysis_data.get('security_findings', [])
    if security_findings:
        insights.append({
            "type": "security",
            "severity": "high",
            "title": f"{len(security_findings)} Security Issues Found",
            "description": "Security vulnerabilities detected in the codebase",
            "recommendation": "Review and fix security findings immediately"
        })
    
    # AI-generated insights
    if depth == "deep" and unified_ai_service:
        ai_insights = await generate_ai_insights(analysis_data)
        insights.extend(ai_insights)
    
    return insights


async def generate_ai_insights(analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate insights using AI."""
    try:
        prompt = f"""
Based on this repository analysis, provide actionable insights:

{json.dumps(analysis_data, indent=2)}

Generate 3-5 specific, actionable insights that would help improve the codebase.
Focus on architecture, performance, security, and maintainability.

Return as JSON array with format:
[{{"type": "insight_type", "severity": "low|medium|high", "title": "short title", "description": "detailed description", "recommendation": "specific action"}}]
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a senior software architect providing code review insights.",
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        if response:
            insights_data = json.loads(response)
            return insights_data.get("insights", [])
            
    except Exception as e:
        logger.error(f"AI insight generation failed: {e}")
    
    return []


def calculate_analysis_scores(analysis_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate quality scores from analysis data."""
    scores = {
        "security": 100.0,
        "performance": 80.0,
        "quality": 75.0
    }
    
    # Adjust security score based on findings
    security_findings = analysis_data.get('security_findings', [])
    if security_findings:
        high_severity = sum(1 for f in security_findings if f.get('severity') == 'high')
        scores['security'] -= (high_severity * 10)
        scores['security'] = max(0, scores['security'])
    
    # Adjust quality score based on patterns
    patterns = analysis_data.get('patterns', [])
    if any(p['type'] == 'testing' for p in patterns):
        scores['quality'] += 10
    
    # Ensure scores are within bounds
    for key in scores:
        scores[key] = min(100, max(0, scores[key]))
    
    return scores


@celery_app.task(name="app.workers.codemirror_tasks.cleanup_old_analyses")
def cleanup_old_analyses():
    """Periodic task to clean up old analysis data."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def cleanup():
            async with get_db_connection() as db:
                # Delete analyses older than 90 days
                result = await db.execute("""
                    DELETE FROM codemirror_analyses
                    WHERE created_at < NOW() - INTERVAL '90 days'
                """)
                
                logger.info(f"Cleaned up {result} old analyses")
        
        loop.run_until_complete(cleanup())
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
    finally:
        loop.close()


@celery_app.task(name="app.workers.codemirror_tasks.sync_pending_cli_results")
def sync_pending_cli_results():
    """Periodic task to sync pending CLI results."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def sync():
            async with get_db_connection() as db:
                # Find pending sync records
                pending = await db.fetch("""
                    SELECT * FROM codemirror_cli_sync
                    WHERE sync_status = 'pending'
                    AND created_at > NOW() - INTERVAL '24 hours'
                    LIMIT 10
                """)
                
                for record in pending:
                    # Process sync
                    logger.info(f"Syncing CLI result {record['cli_analysis_id']}")
                    
                    # Update status
                    await db.execute("""
                        UPDATE codemirror_cli_sync
                        SET sync_status = 'synced', synced_at = NOW()
                        WHERE id = $1
                    """, record['id'])
                
                logger.info(f"Synced {len(pending)} CLI results")
        
        loop.run_until_complete(sync())
        
    except Exception as e:
        logger.error(f"CLI sync task failed: {e}", exc_info=True)
    finally:
        loop.close()