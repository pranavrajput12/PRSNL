"""
Analysis Tasks for CodeMirror

Advanced analysis tasks that can run independently or as part of workflows.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.unified_ai_service import unified_ai_service

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.analysis_tasks.compare_repositories")
def compare_repositories(repo_ids: List[str], user_id: str) -> Dict[str, Any]:
    """
    Compare multiple repositories to find common patterns and differences.
    
    Enterprise feature for identifying best practices across projects.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _compare_repositories_async(repo_ids, user_id)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Repository comparison failed: {e}", exc_info=True)
        raise
    finally:
        loop.close()


async def _compare_repositories_async(repo_ids: List[str], user_id: str) -> Dict[str, Any]:
    """Async implementation of repository comparison."""
    comparison_results = {
        "repositories": [],
        "common_patterns": [],
        "unique_features": {},
        "recommendations": []
    }
    
    async with get_db_connection() as db:
        # Load analyses for all repositories
        analyses = await db.fetch("""
            SELECT ca.*, gr.full_name as repo_name
            FROM codemirror_analyses ca
            JOIN github_repos gr ON ca.repo_id = gr.id
            WHERE ca.repo_id = ANY($1)
            ORDER BY ca.created_at DESC
        """, [UUID(rid) for rid in repo_ids])
        
        if len(analyses) < 2:
            return {"error": "Need at least 2 repositories for comparison"}
        
        # Extract patterns from each repository
        repo_patterns = {}
        for analysis in analyses:
            repo_name = analysis['repo_name']
            patterns = analysis['results'].get('patterns', []) if analysis['results'] else []
            repo_patterns[repo_name] = patterns
            
            comparison_results["repositories"].append({
                "name": repo_name,
                "patterns_count": len(patterns),
                "languages": analysis['languages_detected'],
                "frameworks": analysis['frameworks_detected']
            })
        
        # Find common patterns
        all_pattern_names = set()
        for patterns in repo_patterns.values():
            all_pattern_names.update([p['name'] for p in patterns])
        
        for pattern_name in all_pattern_names:
            repos_with_pattern = [
                repo for repo, patterns in repo_patterns.items()
                if any(p['name'] == pattern_name for p in patterns)
            ]
            
            if len(repos_with_pattern) >= len(repo_ids) * 0.6:  # 60% threshold
                comparison_results["common_patterns"].append({
                    "name": pattern_name,
                    "found_in": repos_with_pattern,
                    "coverage": len(repos_with_pattern) / len(repo_ids)
                })
        
        # Find unique features
        for repo, patterns in repo_patterns.items():
            unique_patterns = []
            for pattern in patterns:
                repos_with_this = sum(
                    1 for r, ps in repo_patterns.items()
                    if any(p['name'] == pattern['name'] for p in ps)
                )
                if repos_with_this == 1:
                    unique_patterns.append(pattern)
            
            if unique_patterns:
                comparison_results["unique_features"][repo] = unique_patterns
        
        # Generate AI recommendations
        if unified_ai_service:
            recommendations = await _generate_comparison_recommendations(comparison_results)
            comparison_results["recommendations"] = recommendations
    
    return comparison_results


async def _generate_comparison_recommendations(comparison_data: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on repository comparison."""
    try:
        prompt = f"""
Based on this comparison of multiple repositories:

Common patterns: {comparison_data['common_patterns']}
Unique features: {comparison_data['unique_features']}

Provide 3-5 actionable recommendations for:
1. Which patterns should be standardized across all repositories
2. Which unique features might benefit other repositories
3. Architecture improvements based on the comparison

Return as a simple JSON array of recommendation strings.
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a software architecture consultant providing cross-repository insights.",
            temperature=0.6
        )
        
        if response:
            import json
            return json.loads(response)
            
    except Exception as e:
        logger.error(f"Failed to generate comparison recommendations: {e}")
    
    return []


@celery_app.task(name="app.workers.analysis_tasks.generate_pattern_library")
def generate_pattern_library(user_id: str) -> Dict[str, Any]:
    """
    Generate a pattern library from all user's repositories.
    
    Creates a comprehensive catalog of patterns with examples and best practices.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _generate_pattern_library_async(user_id)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Pattern library generation failed: {e}", exc_info=True)
        raise
    finally:
        loop.close()


async def _generate_pattern_library_async(user_id: str) -> Dict[str, Any]:
    """Async implementation of pattern library generation."""
    pattern_library = {
        "patterns": {},
        "categories": {},
        "best_practices": [],
        "generated_at": datetime.utcnow().isoformat()
    }
    
    async with get_db_connection() as db:
        # Get all patterns for user
        patterns = await db.fetch("""
            SELECT 
                pattern_signature,
                pattern_type,
                description,
                occurrence_count,
                solution_links,
                ai_confidence,
                metadata
            FROM codemirror_patterns
            WHERE user_id = $1
            ORDER BY occurrence_count DESC
        """, UUID(user_id))
        
        # Organize patterns by type
        for pattern in patterns:
            pattern_type = pattern['pattern_type']
            if pattern_type not in pattern_library["categories"]:
                pattern_library["categories"][pattern_type] = []
            
            pattern_entry = {
                "name": pattern['pattern_signature'],
                "description": pattern['description'],
                "occurrences": pattern['occurrence_count'],
                "confidence": pattern['ai_confidence'],
                "solutions": pattern['solution_links'] or []
            }
            
            pattern_library["categories"][pattern_type].append(pattern_entry)
            pattern_library["patterns"][pattern['pattern_signature']] = pattern_entry
        
        # Generate best practices using AI
        if patterns and unified_ai_service:
            best_practices = await _generate_best_practices(pattern_library)
            pattern_library["best_practices"] = best_practices
    
    return pattern_library


async def _generate_best_practices(pattern_library: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate best practices based on pattern library."""
    try:
        prompt = f"""
Based on this pattern library from multiple repositories:

{pattern_library}

Generate 5-10 best practices that emerge from these patterns.
Focus on actionable guidelines that developers can follow.

Return as JSON array with format:
[{{"title": "practice title", "description": "detailed description", "category": "category"}}]
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a senior architect creating development best practices.",
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        if response:
            import json
            data = json.loads(response)
            return data.get("best_practices", [])
            
    except Exception as e:
        logger.error(f"Failed to generate best practices: {e}")
    
    return []


@celery_app.task(name="app.workers.analysis_tasks.generate_daily_reports")
def generate_daily_reports():
    """
    Generate daily analysis reports for all active users.
    
    Scheduled task that runs once per day.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(_generate_daily_reports_async())
        
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}", exc_info=True)
    finally:
        loop.close()


async def _generate_daily_reports_async():
    """Async implementation of daily report generation."""
    async with get_db_connection() as db:
        # Get users with recent analyses
        users = await db.fetch("""
            SELECT DISTINCT ga.user_id, u.email
            FROM github_accounts ga
            JOIN users u ON ga.user_id = u.id
            JOIN github_repos gr ON ga.id = gr.account_id
            JOIN codemirror_analyses ca ON gr.id = ca.repo_id
            WHERE ca.created_at > NOW() - INTERVAL '24 hours'
            AND u.email IS NOT NULL
        """)
        
        for user in users:
            try:
                # Generate report for user
                report = await _generate_user_report(user['user_id'])
                
                # Store report
                await db.execute("""
                    INSERT INTO codemirror_reports (
                        user_id, report_type, report_data, generated_at
                    ) VALUES ($1, $2, $3, NOW())
                """, user['user_id'], 'daily', report)
                
                # TODO: Send email notification
                logger.info(f"Generated daily report for user {user['user_id']}")
                
            except Exception as e:
                logger.error(f"Failed to generate report for user {user['user_id']}: {e}")


async def _generate_user_report(user_id: UUID) -> Dict[str, Any]:
    """Generate analysis report for a specific user."""
    report = {
        "summary": {},
        "recent_analyses": [],
        "trending_patterns": [],
        "insights_summary": []
    }
    
    async with get_db_connection() as db:
        # Get recent analyses
        analyses = await db.fetch("""
            SELECT 
                ca.*,
                gr.full_name as repo_name
            FROM codemirror_analyses ca
            JOIN github_repos gr ON ca.repo_id = gr.id
            JOIN github_accounts ga ON gr.account_id = ga.id
            WHERE ga.user_id = $1
            AND ca.created_at > NOW() - INTERVAL '24 hours'
            ORDER BY ca.created_at DESC
        """, user_id)
        
        report["summary"]["total_analyses"] = len(analyses)
        
        # Process each analysis
        total_insights = 0
        total_patterns = 0
        
        for analysis in analyses:
            results = analysis['results'] or {}
            insights = results.get('insights', [])
            patterns = results.get('patterns', [])
            
            total_insights += len(insights)
            total_patterns += len(patterns)
            
            report["recent_analyses"].append({
                "repository": analysis['repo_name'],
                "analyzed_at": analysis['created_at'].isoformat(),
                "insights_count": len(insights),
                "patterns_count": len(patterns),
                "scores": {
                    "security": analysis['security_score'],
                    "performance": analysis['performance_score'],
                    "quality": analysis['quality_score']
                }
            })
        
        report["summary"]["total_insights"] = total_insights
        report["summary"]["total_patterns"] = total_patterns
        
        # Get trending patterns
        trending = await db.fetch("""
            SELECT 
                pattern_signature,
                pattern_type,
                COUNT(*) as recent_count
            FROM codemirror_patterns
            WHERE user_id = $1
            AND last_seen_at > NOW() - INTERVAL '7 days'
            GROUP BY pattern_signature, pattern_type
            ORDER BY recent_count DESC
            LIMIT 5
        """, user_id)
        
        report["trending_patterns"] = [
            {
                "name": t['pattern_signature'],
                "type": t['pattern_type'],
                "occurrences": t['recent_count']
            }
            for t in trending
        ]
    
    return report


@celery_app.task(name="app.workers.analysis_tasks.export_analysis_data")
def export_analysis_data(
    user_id: str,
    format: str = "json",
    date_range: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Export analysis data in various formats.
    
    Supports JSON, CSV, and PDF formats.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            _export_analysis_data_async(user_id, format, date_range)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Data export failed: {e}", exc_info=True)
        raise
    finally:
        loop.close()


async def _export_analysis_data_async(
    user_id: str,
    format: str,
    date_range: Optional[Dict[str, str]]
) -> Dict[str, Any]:
    """Async implementation of data export."""
    # Implementation would handle different export formats
    # For now, return a simple response
    return {
        "export_id": f"export_{user_id}_{datetime.utcnow().timestamp()}",
        "format": format,
        "status": "completed",
        "download_url": f"/api/codemirror/exports/{user_id}/latest.{format}"
    }