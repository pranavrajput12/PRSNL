"""
Insight Generation Tasks

Specialized tasks for generating actionable insights from code analysis.
Uses AI and pattern matching to provide enterprise-grade recommendations.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.workers.celery_app import celery_app
from app.db.database import get_db_connection
from app.services.unified_ai_service import unified_ai_service
from app.services.codemirror_knowledge_agent_v2 import CodeMirrorKnowledgeAgentV2

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.insight_tasks.generate_performance_insights")
def generate_performance_insights(
    analysis_id: str,
    repo_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate performance-specific insights.
    
    Analyzes code for performance bottlenecks and optimization opportunities.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        insights = loop.run_until_complete(
            _generate_performance_insights_async(analysis_id, repo_data)
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Performance insight generation failed: {e}", exc_info=True)
        return []
    finally:
        loop.close()


async def _generate_performance_insights_async(
    analysis_id: str,
    repo_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Async implementation of performance insight generation."""
    insights = []
    
    # Analyze for common performance issues
    patterns = repo_data.get('patterns', [])
    structure = repo_data.get('structure', {})
    
    # Check for large files
    if structure.get('max_file_size', 0) > 1000000:  # 1MB
        insights.append({
            "type": "performance_optimization",
            "severity": "medium",
            "title": "Large Files Detected",
            "description": "Some files exceed 1MB, which may impact loading performance",
            "recommendation": "Consider splitting large files into smaller modules",
            "confidence_score": 0.9
        })
    
    # Check for missing caching patterns
    if not any(p['name'].lower().count('cache') for p in patterns):
        insights.append({
            "type": "performance_optimization",
            "severity": "low",
            "title": "No Caching Pattern Detected",
            "description": "The codebase doesn't appear to implement caching",
            "recommendation": "Implement caching for frequently accessed data",
            "confidence_score": 0.7
        })
    
    # Use AI for advanced performance analysis
    if unified_ai_service:
        ai_insights = await _generate_ai_performance_insights(repo_data)
        insights.extend(ai_insights)
    
    # Store insights in database
    async with get_db_connection() as db:
        for insight in insights:
            await db.execute("""
                INSERT INTO codemirror_insights (
                    analysis_id, insight_type, title, description,
                    severity, recommendation, confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                UUID(analysis_id),
                insight['type'],
                insight['title'],
                insight['description'],
                insight['severity'],
                insight['recommendation'],
                insight['confidence_score']
            )
    
    return insights


async def _generate_ai_performance_insights(repo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Use AI to generate performance insights."""
    try:
        prompt = f"""
Analyze this repository data for performance issues and optimization opportunities:

Languages: {repo_data.get('languages', [])}
Frameworks: {repo_data.get('frameworks', [])}
File count: {repo_data.get('file_count', 0)}
Dependencies: {repo_data.get('dependencies', [])}

Identify specific performance concerns such as:
- Inefficient algorithms or data structures
- Missing optimizations (lazy loading, code splitting, etc.)
- Resource-intensive operations
- Scalability issues

Return 2-4 specific performance insights as JSON:
[{{"type": "performance_optimization", "severity": "low|medium|high", "title": "short title", "description": "detailed description", "recommendation": "specific action", "confidence_score": 0.0-1.0}}]
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a performance optimization expert analyzing codebases.",
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        
        if response:
            data = json.loads(response)
            return data.get("insights", [])
            
    except Exception as e:
        logger.error(f"AI performance insight generation failed: {e}")
    
    return []


@celery_app.task(name="app.workers.insight_tasks.generate_security_insights")
def generate_security_insights(
    analysis_id: str,
    repo_data: Dict[str, Any],
    security_scan_results: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Generate security-specific insights.
    
    Combines security scan results with AI analysis for comprehensive security insights.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        insights = loop.run_until_complete(
            _generate_security_insights_async(analysis_id, repo_data, security_scan_results)
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Security insight generation failed: {e}", exc_info=True)
        return []
    finally:
        loop.close()


async def _generate_security_insights_async(
    analysis_id: str,
    repo_data: Dict[str, Any],
    security_scan_results: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Async implementation of security insight generation."""
    insights = []
    
    # Process security scan results if available
    if security_scan_results:
        findings = security_scan_results.get('findings', [])
        
        # Group findings by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for finding in findings:
            severity = finding.get('severity', 'low').lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts['high'] > 0:
            insights.append({
                "type": "security_vulnerability",
                "severity": "high",
                "title": f"{severity_counts['high']} High-Severity Security Issues",
                "description": "Critical security vulnerabilities require immediate attention",
                "recommendation": "Review and fix high-severity issues before deployment",
                "confidence_score": 1.0,
                "metadata": {"findings_count": severity_counts}
            })
    
    # Check for security patterns
    dependencies = repo_data.get('dependencies', {})
    
    # Check for outdated dependencies (would need version checking)
    if dependencies:
        insights.append({
            "type": "dependency_security",
            "severity": "medium",
            "title": "Dependency Security Review Needed",
            "description": f"Project has {sum(len(deps) for deps in dependencies.values())} dependencies",
            "recommendation": "Run dependency vulnerability scan and update outdated packages",
            "confidence_score": 0.8
        })
    
    # Use AI for additional security insights
    if unified_ai_service:
        ai_insights = await _generate_ai_security_insights(repo_data, security_scan_results)
        insights.extend(ai_insights)
    
    # Store insights
    async with get_db_connection() as db:
        for insight in insights:
            await db.execute("""
                INSERT INTO codemirror_insights (
                    analysis_id, insight_type, title, description,
                    severity, recommendation, confidence_score, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                UUID(analysis_id),
                insight['type'],
                insight['title'],
                insight['description'],
                insight['severity'],
                insight['recommendation'],
                insight['confidence_score'],
                insight.get('metadata', {})
            )
    
    return insights


async def _generate_ai_security_insights(
    repo_data: Dict[str, Any],
    security_scan_results: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Use AI to generate security insights."""
    try:
        prompt = f"""
Analyze this repository for security concerns:

Repository data: {json.dumps(repo_data, indent=2)}
Security scan results: {json.dumps(security_scan_results, indent=2) if security_scan_results else "None"}

Identify security issues such as:
- Authentication/authorization weaknesses
- Data exposure risks
- Injection vulnerabilities
- Insecure configurations
- Missing security headers or practices

Return 2-4 specific security insights as JSON:
[{{"type": "security_vulnerability", "severity": "low|medium|high", "title": "short title", "description": "detailed description", "recommendation": "specific action", "confidence_score": 0.0-1.0}}]
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a security expert analyzing code for vulnerabilities.",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        if response:
            data = json.loads(response)
            return data.get("insights", [])
            
    except Exception as e:
        logger.error(f"AI security insight generation failed: {e}")
    
    return []


@celery_app.task(name="app.workers.insight_tasks.generate_architecture_insights")
def generate_architecture_insights(
    analysis_id: str,
    repo_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate architecture and design insights.
    
    Analyzes code structure, patterns, and design decisions.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        insights = loop.run_until_complete(
            _generate_architecture_insights_async(analysis_id, repo_data)
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Architecture insight generation failed: {e}", exc_info=True)
        return []
    finally:
        loop.close()


async def _generate_architecture_insights_async(
    analysis_id: str,
    repo_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Async implementation of architecture insight generation."""
    insights = []
    
    structure = repo_data.get('structure', {})
    patterns = repo_data.get('patterns', [])
    
    # Check for architectural patterns
    has_mvc = any(p['name'].lower() in ['mvc', 'model-view-controller'] for p in patterns)
    has_microservices = any('microservice' in p['name'].lower() for p in patterns)
    
    # File organization insights
    if structure.get('max_depth', 0) > 5:
        insights.append({
            "type": "architecture_improvement",
            "severity": "medium",
            "title": "Deep Directory Nesting Detected",
            "description": f"Directory structure goes {structure['max_depth']} levels deep",
            "recommendation": "Consider flattening directory structure for better maintainability",
            "confidence_score": 0.8
        })
    
    # Missing common directories
    common_dirs = structure.get('common_directories', [])
    if 'tests' not in common_dirs and 'test' not in common_dirs:
        insights.append({
            "type": "architecture_improvement",
            "severity": "high",
            "title": "Missing Test Directory",
            "description": "No dedicated test directory found",
            "recommendation": "Create a tests directory and add unit tests",
            "confidence_score": 0.9
        })
    
    # Use AI for advanced architecture insights
    if unified_ai_service:
        ai_insights = await _generate_ai_architecture_insights(repo_data)
        insights.extend(ai_insights)
    
    # Store insights
    async with get_db_connection() as db:
        for insight in insights:
            await db.execute("""
                INSERT INTO codemirror_insights (
                    analysis_id, insight_type, title, description,
                    severity, recommendation, confidence_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                UUID(analysis_id),
                insight['type'],
                insight['title'],
                insight['description'],
                insight['severity'],
                insight['recommendation'],
                insight['confidence_score']
            )
    
    return insights


async def _generate_ai_architecture_insights(repo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Use AI to generate architecture insights."""
    try:
        prompt = f"""
Analyze this repository's architecture and design:

Structure: {json.dumps(repo_data.get('structure', {}), indent=2)}
Patterns: {json.dumps(repo_data.get('patterns', []), indent=2)}
Languages: {repo_data.get('languages', [])}
Frameworks: {repo_data.get('frameworks', [])}

Provide architectural insights about:
- Design pattern usage and improvements
- Code organization and modularity
- Separation of concerns
- Scalability considerations
- Maintainability improvements

Return 3-5 architecture insights as JSON:
[{{"type": "architecture_improvement", "severity": "low|medium|high", "title": "short title", "description": "detailed description", "recommendation": "specific action", "confidence_score": 0.0-1.0}}]
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a software architect reviewing code structure and design.",
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        if response:
            data = json.loads(response)
            return data.get("insights", [])
            
    except Exception as e:
        logger.error(f"AI architecture insight generation failed: {e}")
    
    return []


@celery_app.task(name="app.workers.insight_tasks.correlate_with_knowledge_base")
def correlate_with_knowledge_base(
    analysis_id: str,
    repo_name: str,
    analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Correlate analysis results with knowledge base content.
    
    Finds relevant videos, documents, and conversations that can help with identified issues.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        correlations = loop.run_until_complete(
            _correlate_with_knowledge_base_async(analysis_id, repo_name, analysis_results)
        )
        
        return correlations
        
    except Exception as e:
        logger.error(f"Knowledge base correlation failed: {e}", exc_info=True)
        return {}
    finally:
        loop.close()


async def _correlate_with_knowledge_base_async(
    analysis_id: str,
    repo_name: str,
    analysis_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Async implementation of knowledge base correlation."""
    
    # Use the V2 knowledge agent for enhanced correlation
    knowledge_agent = CodeMirrorKnowledgeAgentV2()
    
    # Extract key information for correlation
    languages = analysis_results.get('languages_detected', [])
    frameworks = analysis_results.get('frameworks_detected', [])
    
    # Find relevant knowledge base content
    knowledge_results = await knowledge_agent.find_relevant_content(
        repository_name=repo_name,
        analysis_results=analysis_results,
        repo_languages=languages,
        repo_frameworks=frameworks,
        limit=10
    )
    
    # Process and enhance correlations
    correlations = {
        "analysis_id": analysis_id,
        "knowledge_items": knowledge_results,
        "relevance_summary": {}
    }
    
    # Generate relevance summary
    for content_type, items in knowledge_results.items():
        if isinstance(items, list) and items:
            correlations["relevance_summary"][content_type] = {
                "count": len(items),
                "top_relevance": max(
                    (item.get('relevance_score', 0) for item in items),
                    default=0
                )
            }
    
    # Store correlation results
    async with get_db_connection() as db:
        await db.execute("""
            UPDATE codemirror_analyses
            SET knowledge_correlations = $2
            WHERE id = $1
        """, UUID(analysis_id), correlations)
    
    return correlations


@celery_app.task(name="app.workers.insight_tasks.generate_solution_recommendations")
def generate_solution_recommendations(
    insight_id: str,
    insight_data: Dict[str, Any],
    knowledge_correlations: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Generate specific solution recommendations for an insight.
    
    Combines pattern matching, knowledge base, and AI to provide actionable solutions.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        recommendations = loop.run_until_complete(
            _generate_solution_recommendations_async(
                insight_id, insight_data, knowledge_correlations
            )
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Solution recommendation generation failed: {e}", exc_info=True)
        return []
    finally:
        loop.close()


async def _generate_solution_recommendations_async(
    insight_id: str,
    insight_data: Dict[str, Any],
    knowledge_correlations: Optional[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Async implementation of solution recommendation generation."""
    recommendations = []
    
    # Check if we have relevant knowledge base content
    relevant_resources = []
    if knowledge_correlations:
        for content_type, items in knowledge_correlations.get('knowledge_items', {}).items():
            if isinstance(items, list):
                relevant_resources.extend([
                    {
                        "type": content_type,
                        "title": item.get('title', 'Unknown'),
                        "url": item.get('url', ''),
                        "relevance": item.get('relevance_score', 0)
                    }
                    for item in items[:3]  # Top 3 per type
                ])
    
    # Generate AI-powered recommendations
    if unified_ai_service:
        ai_recommendations = await _generate_ai_solution_recommendations(
            insight_data, relevant_resources
        )
        recommendations.extend(ai_recommendations)
    
    # Add knowledge base resources as recommendations
    for resource in relevant_resources[:5]:  # Top 5 overall
        recommendations.append({
            "type": "resource",
            "title": f"Reference: {resource['title']}",
            "description": f"Relevant {resource['type']} from your knowledge base",
            "action": f"Review this resource for solutions",
            "resource_url": resource['url'],
            "relevance_score": resource['relevance']
        })
    
    # Store recommendations
    async with get_db_connection() as db:
        await db.execute("""
            UPDATE codemirror_insights
            SET solution_recommendations = $2
            WHERE id = $1
        """, UUID(insight_id), recommendations)
    
    return recommendations


async def _generate_ai_solution_recommendations(
    insight_data: Dict[str, Any],
    relevant_resources: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Use AI to generate solution recommendations."""
    try:
        prompt = f"""
Based on this code insight and available resources, provide specific solution recommendations:

Insight: {json.dumps(insight_data, indent=2)}
Available Resources: {json.dumps(relevant_resources, indent=2)}

Generate 2-4 specific, actionable recommendations that:
1. Address the root cause of the issue
2. Provide step-by-step implementation guidance
3. Reference relevant resources when applicable
4. Consider best practices and modern approaches

Return as JSON array:
[{{"type": "solution", "title": "recommendation title", "description": "detailed steps", "action": "first action to take", "relevance_score": 0.0-1.0}}]
"""

        response = await unified_ai_service.complete(
            prompt=prompt,
            system_prompt="You are a senior developer providing specific code solutions.",
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        
        if response:
            data = json.loads(response)
            return data.get("recommendations", [])
            
    except Exception as e:
        logger.error(f"AI solution recommendation generation failed: {e}")
    
    return []