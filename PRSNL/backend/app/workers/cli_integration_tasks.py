"""
CLI Integration Celery Tasks

Background tasks for running CLI tools (GitPython, Semgrep, Comby, Watchdog)
and processing their results through the enhanced CodeMirror pipeline.
"""

import asyncio
import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from celery import group, chain, chord
from celery.result import AsyncResult
from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.codemirror_service import codemirror_service
from app.services.git_analysis_service import git_analysis_service
from app.services.security_scan_service import security_scan_service
from app.services.code_search_service import code_search_service
from app.services.file_watch_service import file_watch_service, AnalysisRequest
from app.services.realtime_progress_service import realtime_service

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.cli_integration_tasks.run_comprehensive_cli_analysis")
@observe(name="celery_comprehensive_cli_analysis")
def run_comprehensive_cli_analysis(
    repo_path: str,
    analysis_id: str,
    user_id: str,
    analysis_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Main orchestrator task for comprehensive CLI-based repository analysis.
    
    Coordinates GitPython, Semgrep, Comby analysis and processes results.
    """
    try:
        logger.info(f"Starting comprehensive CLI analysis for repo: {repo_path}")
        
        # Send initial progress
        asyncio.run(realtime_service.send_progress_update(
            f"analysis_{analysis_id}",
            {
                "status": "starting_cli_analysis",
                "message": "Initializing CLI tool analysis",
                "progress": 10
            }
        ))
        
        # Record analysis request
        request_id = str(uuid4())
        asyncio.run(_record_analysis_request(
            request_id, repo_path, analysis_id, analysis_config or {}
        ))
        
        # Create task chain for sequential analysis
        analysis_chain = chain(
            # Phase 1: Git Analysis
            run_git_analysis.s(repo_path, analysis_id, user_id, analysis_config),
            # Phase 2: Security Scan (parallel with Code Search)
            group(
                run_security_scan.s(repo_path, analysis_id),
                run_code_search_analysis.s(repo_path, analysis_id)
            ),
            # Phase 3: Process and integrate all results
            integrate_cli_results.s(analysis_id, user_id, request_id)
        )
        
        # Execute the chain
        result = analysis_chain.apply_async()
        
        # Wait for completion (with timeout)
        final_result = result.get(timeout=600)  # 10 minute timeout
        
        # Send completion progress
        asyncio.run(realtime_service.send_progress_update(
            f"analysis_{analysis_id}",
            {
                "status": "cli_analysis_complete",
                "message": "CLI analysis completed successfully",
                "progress": 100,
                "results": final_result
            }
        ))
        
        logger.info(f"Comprehensive CLI analysis completed for {repo_path}")
        return final_result
        
    except Exception as e:
        error_msg = f"Comprehensive CLI analysis failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        # Send error progress
        asyncio.run(realtime_service.send_progress_update(
            f"analysis_{analysis_id}",
            {
                "status": "cli_analysis_error", 
                "message": error_msg,
                "progress": 0,
                "error": str(e)
            }
        ))
        
        # Record error
        asyncio.run(_record_cli_execution(
            request_id if 'request_id' in locals() else str(uuid4()),
            "comprehensive",
            "error",
            error_output=str(e)
        ))
        
        raise


@celery_app.task(name="app.workers.cli_integration_tasks.run_git_analysis")
@observe(name="celery_git_analysis")
def run_git_analysis(
    repo_path: str,
    analysis_id: str,
    user_id: str,
    analysis_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Run GitPython-based repository analysis."""
    
    execution_start = datetime.utcnow()
    request_id = str(uuid4())
    
    try:
        logger.info(f"Starting Git analysis for repo: {repo_path}")
        
        # Send progress update
        asyncio.run(realtime_service.send_progress_update(
            f"analysis_{analysis_id}",
            {
                "status": "running_git_analysis",
                "message": "Analyzing Git repository history",
                "progress": 20
            }
        ))
        
        # Configure analysis
        config = analysis_config or {}
        analysis_depth = config.get('analysis_depth', 'standard')
        max_commits = config.get('max_commits')
        
        # Run git analysis
        git_result = asyncio.run(
            git_analysis_service.analyze_repository(
                repo_path, 
                analysis_depth=analysis_depth,
                max_commits=max_commits
            )
        )
        
        # Convert result to dict for serialization
        git_result_dict = {
            'repository_url': git_result.repository_url,
            'analysis_timestamp': git_result.analysis_timestamp.isoformat(),
            'total_commits': git_result.total_commits,
            'total_authors': git_result.total_authors,
            'repository_age_days': git_result.repository_age_days,
            'primary_language': git_result.primary_language,
            'commits_by_hour': git_result.commits_by_hour,
            'commits_by_day': git_result.commits_by_day,
            'commits_by_month': git_result.commits_by_month,
            'top_authors': [
                {
                    'name': author.name,
                    'email': author.email,
                    'total_commits': author.total_commits,
                    'lines_added': author.lines_added,
                    'lines_deleted': author.lines_deleted,
                    'files_touched': author.files_touched,
                    'first_commit': author.first_commit.isoformat(),
                    'last_commit': author.last_commit.isoformat(),
                    'favorite_extensions': author.favorite_extensions
                }
                for author in git_result.top_authors
            ],
            'author_collaboration': git_result.author_collaboration,
            'most_changed_files': git_result.most_changed_files,
            'file_extensions': git_result.file_extensions,
            'hotspot_files': git_result.hotspot_files,
            'average_commit_size': git_result.average_commit_size,
            'merge_frequency': git_result.merge_frequency,
            'branch_patterns': git_result.branch_patterns,
            'release_patterns': git_result.release_patterns,
            'commit_message_quality': git_result.commit_message_quality,
            'refactoring_patterns': git_result.refactoring_patterns,
            'technical_debt_indicators': git_result.technical_debt_indicators
        }
        
        # Record successful execution
        execution_time = (datetime.utcnow() - execution_start).total_seconds()
        asyncio.run(_record_cli_execution(
            request_id,
            "git",
            "success",
            execution_time=execution_time,
            output_summary=f"Analyzed {git_result.total_commits} commits from {git_result.total_authors} authors"
        ))
        
        logger.info(f"Git analysis completed: {git_result.total_commits} commits, {git_result.total_authors} authors")
        return {"git_analysis": git_result_dict}
        
    except Exception as e:
        error_msg = f"Git analysis failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        # Record failed execution
        execution_time = (datetime.utcnow() - execution_start).total_seconds()
        asyncio.run(_record_cli_execution(
            request_id,
            "git",
            "error",
            execution_time=execution_time,
            error_output=str(e)
        ))
        
        # Return empty result to allow chain to continue
        return {"git_analysis": None, "error": error_msg}


@celery_app.task(name="app.workers.cli_integration_tasks.run_security_scan")
@observe(name="celery_security_scan")
def run_security_scan(
    previous_result: Dict[str, Any],
    repo_path: str,
    analysis_id: str
) -> Dict[str, Any]:
    """Run Semgrep-based security analysis."""
    
    execution_start = datetime.utcnow()
    request_id = str(uuid4())
    
    try:
        logger.info(f"Starting security scan for repo: {repo_path}")
        
        # Send progress update
        asyncio.run(realtime_service.send_progress_update(
            f"analysis_{analysis_id}",
            {
                "status": "running_security_scan",
                "message": "Scanning for security vulnerabilities",
                "progress": 40
            }
        ))
        
        # Run security scan
        security_result = asyncio.run(
            security_scan_service.scan_repository(repo_path)
        )
        
        # Convert result to dict for serialization
        security_result_dict = {
            'repository_path': security_result.repository_path,
            'scan_timestamp': security_result.scan_timestamp.isoformat(),
            'scan_duration_seconds': security_result.scan_duration_seconds,
            'total_findings': security_result.total_findings,
            'findings_by_severity': security_result.findings_by_severity,
            'files_scanned': security_result.files_scanned,
            'rules_executed': security_result.rules_executed,
            'owasp_categories': security_result.owasp_categories,
            'cwe_categories': security_result.cwe_categories,
            'overall_security_score': security_result.overall_security_score,
            'high_risk_files': security_result.high_risk_files,
            'security_hotspots': security_result.security_hotspots,
            'owasp_compliance_score': security_result.owasp_compliance_score,
            'common_vulnerabilities': security_result.common_vulnerabilities,
            'findings': [
                {
                    'rule_id': finding.rule_id,
                    'severity': finding.severity.value,
                    'message': finding.message,
                    'file_path': finding.file_path,
                    'line_number': finding.line_number,
                    'column_number': finding.column_number,
                    'code_snippet': finding.code_snippet,
                    'fix_suggestion': finding.fix_suggestion,
                    'owasp_category': finding.owasp_category,
                    'cwe_id': finding.cwe_id,
                    'confidence': finding.confidence
                }
                for finding in security_result.findings
            ]
        }
        
        # Record successful execution
        execution_time = (datetime.utcnow() - execution_start).total_seconds()
        asyncio.run(_record_cli_execution(
            request_id,
            "semgrep",
            "success",
            execution_time=execution_time,
            output_summary=f"Found {security_result.total_findings} security findings across {security_result.files_scanned} files"
        ))
        
        # Merge with previous result
        result = previous_result.copy()
        result["security_scan"] = security_result_dict
        
        logger.info(f"Security scan completed: {security_result.total_findings} findings, score: {security_result.overall_security_score}/100")
        return result
        
    except Exception as e:
        error_msg = f"Security scan failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        # Record failed execution
        execution_time = (datetime.utcnow() - execution_start).total_seconds()
        asyncio.run(_record_cli_execution(
            request_id,
            "semgrep",
            "error",
            execution_time=execution_time,
            error_output=str(e)
        ))
        
        # Merge with previous result
        result = previous_result.copy()
        result.update({"security_scan": None, "security_error": error_msg})
        return result


@celery_app.task(name="app.workers.cli_integration_tasks.run_code_search_analysis")
@observe(name="celery_code_search")
def run_code_search_analysis(
    previous_result: Dict[str, Any],
    repo_path: str,
    analysis_id: str
) -> Dict[str, Any]:
    """Run Comby-based structural code analysis."""
    
    execution_start = datetime.utcnow()
    request_id = str(uuid4())
    
    try:
        logger.info(f"Starting code search analysis for repo: {repo_path}")
        
        # Send progress update
        asyncio.run(realtime_service.send_progress_update(
            f"analysis_{analysis_id}",
            {
                "status": "running_code_search",
                "message": "Analyzing code patterns and structure",
                "progress": 60
            }
        ))
        
        # Run code search analysis
        search_result = asyncio.run(
            code_search_service.search_repository(repo_path)
        )
        
        # Convert result to dict for serialization
        search_result_dict = {
            'repository_path': search_result.repository_path,
            'search_timestamp': search_result.search_timestamp.isoformat(),
            'search_duration_seconds': search_result.search_duration_seconds,
            'total_matches': search_result.total_matches,
            'matches_by_pattern': search_result.matches_by_pattern,
            'identified_patterns': [
                {
                    'pattern_id': pattern.pattern_id,
                    'pattern_name': pattern.pattern_name,
                    'pattern_type': pattern.pattern_type.value,
                    'description': pattern.description,
                    'template': pattern.template,
                    'replacement_template': pattern.replacement_template,
                    'languages': pattern.languages,
                    'examples': pattern.examples,
                    'benefits': pattern.benefits,
                    'difficulty': pattern.difficulty
                }
                for pattern in search_result.identified_patterns
            ],
            'all_matches': [
                {
                    'file_path': match.file_path,
                    'line_number': match.line_number,
                    'column_number': match.column_number,
                    'matched_text': match.matched_text,
                    'context_before': match.context_before,
                    'context_after': match.context_after,
                    'pattern_name': match.pattern_name,
                    'confidence_score': match.confidence_score
                }
                for match in search_result.all_matches
            ],
            'architecture_insights': search_result.architecture_insights,
            'consistency_violations': search_result.consistency_violations,
            'refactoring_opportunities': [
                {
                    'opportunity_id': opp.opportunity_id,
                    'title': opp.title,
                    'description': opp.description,
                    'pattern_type': opp.pattern_type.value,
                    'file_path': opp.file_path,
                    'line_range': [opp.line_range[0], opp.line_range[1]],
                    'current_code': opp.current_code,
                    'suggested_code': opp.suggested_code,
                    'benefits': opp.benefits,
                    'effort_estimate': opp.effort_estimate,
                    'risk_level': opp.risk_level
                }
                for opp in search_result.refactoring_opportunities
            ],
            'high_impact_refactorings': [
                {
                    'opportunity_id': opp.opportunity_id,
                    'title': opp.title,
                    'description': opp.description,
                    'pattern_type': opp.pattern_type.value,
                    'file_path': opp.file_path,
                    'line_range': [opp.line_range[0], opp.line_range[1]],
                    'current_code': opp.current_code,
                    'suggested_code': opp.suggested_code,
                    'benefits': opp.benefits,
                    'effort_estimate': opp.effort_estimate,
                    'risk_level': opp.risk_level
                }
                for opp in search_result.high_impact_refactorings
            ],
            'pattern_diversity_score': search_result.pattern_diversity_score,
            'consistency_score': search_result.consistency_score,
            'maintainability_score': search_result.maintainability_score,
            'language_patterns': search_result.language_patterns,
            'framework_usage': search_result.framework_usage
        }
        
        # Record successful execution
        execution_time = (datetime.utcnow() - execution_start).total_seconds()
        asyncio.run(_record_cli_execution(
            request_id,
            "comby",
            "success",
            execution_time=execution_time,
            output_summary=f"Found {search_result.total_matches} pattern matches, {len(search_result.refactoring_opportunities)} refactoring opportunities"
        ))
        
        # Merge with previous result
        result = previous_result.copy()
        result["code_search"] = search_result_dict
        
        logger.info(f"Code search completed: {search_result.total_matches} matches, maintainability: {search_result.maintainability_score}/100")
        return result
        
    except Exception as e:
        error_msg = f"Code search analysis failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        # Record failed execution
        execution_time = (datetime.utcnow() - execution_start).total_seconds()
        asyncio.run(_record_cli_execution(
            request_id,
            "comby",
            "error",
            execution_time=execution_time,
            error_output=str(e)
        ))
        
        # Merge with previous result
        result = previous_result.copy()
        result.update({"code_search": None, "code_search_error": error_msg})
        return result


@celery_app.task(name="app.workers.cli_integration_tasks.integrate_cli_results")
@observe(name="celery_integrate_cli_results")
def integrate_cli_results(
    cli_results: List[Dict[str, Any]],
    analysis_id: str,
    user_id: str,
    request_id: str
) -> Dict[str, Any]:
    """Integrate all CLI analysis results and process through CodeMirror service."""
    
    try:
        logger.info(f"Integrating CLI results for analysis: {analysis_id}")
        
        # Send progress update
        asyncio.run(realtime_service.send_progress_update(
            f"analysis_{analysis_id}",
            {
                "status": "integrating_results",
                "message": "Processing and integrating CLI analysis results",
                "progress": 80
            }
        ))
        
        # Merge all results from the parallel tasks
        integrated_results = {}
        for result_set in cli_results:
            if isinstance(result_set, list):
                # Handle results from group task
                for result in result_set:
                    integrated_results.update(result)
            else:
                integrated_results.update(result_set)
        
        # Process through CodeMirror service
        asyncio.run(
            codemirror_service.process_cli_results(
                analysis_id, user_id, integrated_results
            )
        )
        
        # Update analysis request status
        asyncio.run(_update_analysis_request_status(
            request_id, "completed", analysis_id
        ))
        
        # Prepare summary for response
        summary = {
            "analysis_id": analysis_id,
            "cli_tools_executed": [],
            "total_execution_time": 0,
            "results_summary": {}
        }
        
        # Summarize results
        if "git_analysis" in integrated_results and integrated_results["git_analysis"]:
            git_data = integrated_results["git_analysis"]
            summary["cli_tools_executed"].append("git")
            summary["results_summary"]["git"] = {
                "commits_analyzed": git_data.get("total_commits", 0),
                "authors_found": git_data.get("total_authors", 0),
                "primary_language": git_data.get("primary_language", "Unknown")
            }
        
        if "security_scan" in integrated_results and integrated_results["security_scan"]:
            security_data = integrated_results["security_scan"]
            summary["cli_tools_executed"].append("semgrep")
            summary["results_summary"]["security"] = {
                "total_findings": security_data.get("total_findings", 0),
                "security_score": security_data.get("overall_security_score", 0),
                "files_scanned": security_data.get("files_scanned", 0)
            }
        
        if "code_search" in integrated_results and integrated_results["code_search"]:
            search_data = integrated_results["code_search"]
            summary["cli_tools_executed"].append("comby")
            summary["results_summary"]["code_search"] = {
                "pattern_matches": search_data.get("total_matches", 0),
                "maintainability_score": search_data.get("maintainability_score", 0),
                "refactoring_opportunities": len(search_data.get("refactoring_opportunities", []))
            }
        
        logger.info(f"CLI integration completed for analysis {analysis_id}")
        return summary
        
    except Exception as e:
        error_msg = f"CLI results integration failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        # Update analysis request status
        asyncio.run(_update_analysis_request_status(
            request_id, "failed", error_message=str(e)
        ))
        
        raise


@celery_app.task(name="app.workers.cli_integration_tasks.process_file_watch_events")
@observe(name="celery_process_file_events")
def process_file_watch_events(
    analysis_request: Dict[str, Any]
) -> Dict[str, Any]:
    """Process file watch events and trigger appropriate CLI analysis."""
    
    try:
        logger.info(f"Processing file watch events for analysis request: {analysis_request.get('request_id')}")
        
        # Extract request details
        request_id = analysis_request["request_id"]
        repository_path = analysis_request["repository_path"]
        analysis_types = analysis_request.get("analysis_types", [])
        trigger_events = analysis_request.get("trigger_events", [])
        
        # Create analysis record if needed
        analysis_id = str(uuid4())
        
        # Determine which CLI tools to run based on events and config
        tasks_to_run = []
        
        if "git" in analysis_types:
            tasks_to_run.append(
                run_git_analysis.s(repository_path, analysis_id, "file_watch", {})
            )
        
        if "security" in analysis_types:
            # Security scan for relevant files
            security_config = {
                "include_patterns": [event.get("file_path", "") for event in trigger_events if event.get("is_source_file")]
            }
            tasks_to_run.append(
                run_security_scan.s({}, repository_path, analysis_id)
            )
        
        if "structural" in analysis_types:
            tasks_to_run.append(
                run_code_search_analysis.s({}, repository_path, analysis_id)
            )
        
        # Execute tasks
        if tasks_to_run:
            # Run tasks in parallel for file watch events (faster response)
            task_group = group(*tasks_to_run)
            result = task_group.apply_async()
            
            # Wait for completion
            results = result.get(timeout=300)  # 5 minute timeout for file watch
            
            # Merge results and process
            merged_results = {}
            for task_result in results:
                merged_results.update(task_result)
            
            # Add file events to results
            merged_results["file_events"] = trigger_events
            
            # Process through CodeMirror service
            asyncio.run(
                codemirror_service.process_cli_results(
                    analysis_id, "file_watch", merged_results
                )
            )
            
            logger.info(f"File watch event processing completed for {request_id}")
            return {
                "request_id": request_id,
                "analysis_id": analysis_id,
                "events_processed": len(trigger_events),
                "tools_executed": list(merged_results.keys())
            }
        else:
            logger.warning(f"No CLI tools to run for file watch request {request_id}")
            return {
                "request_id": request_id,
                "events_processed": len(trigger_events),
                "tools_executed": []
            }
            
    except Exception as e:
        error_msg = f"File watch event processing failed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise


# Helper functions for database operations

async def _record_analysis_request(
    request_id: str,
    repository_path: str,
    analysis_id: str,
    config: Dict[str, Any]
):
    """Record analysis request in database"""
    
    try:
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO codemirror_analysis_requests (
                    request_id, repository_path, analysis_types,
                    priority, trigger_source, analysis_id,
                    trigger_events, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                request_id,
                repository_path,
                json.dumps(config.get('analysis_types', ['git', 'security', 'structural'])),
                config.get('priority', 'medium'),
                'celery_task',
                UUID(analysis_id),
                json.dumps(config.get('trigger_events', [])),
                'in_progress'
            )
    except Exception as e:
        logger.error(f"Failed to record analysis request: {e}")


async def _update_analysis_request_status(
    request_id: str,
    status: str,
    analysis_id: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Update analysis request status"""
    
    try:
        async with get_db_connection() as db:
            if status == "completed":
                await db.execute("""
                    UPDATE codemirror_analysis_requests 
                    SET status = $1, completed_at = NOW()
                    WHERE request_id = $2
                """, status, request_id)
            elif status == "failed":
                await db.execute("""
                    UPDATE codemirror_analysis_requests 
                    SET status = $1, error_message = $2, completed_at = NOW()
                    WHERE request_id = $3
                """, status, error_message, request_id)
            else:
                await db.execute("""
                    UPDATE codemirror_analysis_requests 
                    SET status = $1, started_at = NOW()
                    WHERE request_id = $2
                """, status, request_id)
    except Exception as e:
        logger.error(f"Failed to update analysis request status: {e}")


async def _record_cli_execution(
    request_id: str,
    tool_name: str,
    status: str,
    execution_time: Optional[float] = None,
    output_summary: Optional[str] = None,
    error_output: Optional[str] = None
):
    """Record CLI tool execution details"""
    
    try:
        async with get_db_connection() as db:
            # Get analysis request ID
            analysis_request_id = await db.fetchval("""
                SELECT id FROM codemirror_analysis_requests WHERE request_id = $1
            """, request_id)
            
            if analysis_request_id:
                await db.execute("""
                    INSERT INTO codemirror_cli_executions (
                        analysis_request_id, tool_name, status,
                        execution_time_seconds, stdout_output, stderr_output
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    analysis_request_id,
                    tool_name,
                    status,
                    execution_time,
                    output_summary,
                    error_output
                )
    except Exception as e:
        logger.error(f"Failed to record CLI execution: {e}")


# Task for starting file watching
@celery_app.task(name="app.workers.cli_integration_tasks.start_file_watching")
def start_file_watching(
    repository_path: str,
    watch_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Start file watching for a repository"""
    
    try:
        from app.services.file_watch_service import WatchConfiguration, AnalysisTrigger
        
        # Create watch configuration
        config = WatchConfiguration(
            repository_path=repository_path,
            watch_patterns=watch_config.get('watch_patterns', ['*.py', '*.js', '*.ts', '*.java', '*.go']),
            ignore_patterns=watch_config.get('ignore_patterns', ['**/.git/**', '**/node_modules/**']),
            analysis_trigger=AnalysisTrigger.BATCHED,
            batch_window_seconds=watch_config.get('batch_window_seconds', 30),
            max_events_per_batch=watch_config.get('max_events_per_batch', 50),
            debounce_seconds=watch_config.get('debounce_seconds', 2.0),
            enable_git_integration=watch_config.get('enable_git_integration', True),
            enable_security_monitoring=watch_config.get('enable_security_monitoring', True)
        )
        
        # Define callback for analysis requests
        def analysis_callback(analysis_request: AnalysisRequest):
            # Convert AnalysisRequest to dict and queue as Celery task
            request_dict = {
                "request_id": analysis_request.request_id,
                "repository_path": analysis_request.repository_path,
                "analysis_types": analysis_request.analysis_types,
                "priority": analysis_request.priority,
                "trigger_events": [
                    {
                        "event_type": event.event_type.value,
                        "file_path": event.file_path,
                        "timestamp": event.timestamp.isoformat(),
                        "file_size": event.file_size,
                        "file_extension": event.file_extension,
                        "is_source_file": event.is_source_file,
                        "batch_id": event.batch_id
                    }
                    for event in analysis_request.trigger_events
                ]
            }
            
            # Queue file watch processing task
            process_file_watch_events.apply_async(args=[request_dict])
        
        # Start watching
        success = asyncio.run(
            file_watch_service.start_watching(config, analysis_callback)
        )
        
        if success:
            logger.info(f"Started file watching for {repository_path}")
            return {
                "status": "success",
                "repository_path": repository_path,
                "watching": True
            }
        else:
            return {
                "status": "error",
                "repository_path": repository_path,
                "watching": False,
                "error": "Failed to start file watching"
            }
            
    except Exception as e:
        logger.error(f"Failed to start file watching: {e}")
        return {
            "status": "error",
            "repository_path": repository_path,
            "watching": False,
            "error": str(e)
        }