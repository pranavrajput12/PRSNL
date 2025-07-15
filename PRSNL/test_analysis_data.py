#!/usr/bin/env python3
"""
Test script to create sample analysis data for frontend testing
"""
import asyncio
import json
from uuid import uuid4
from datetime import datetime

import asyncpg
from app.db.database import get_db_pool, create_db_pool


async def create_test_analysis_data():
    """Create test analysis data"""
    # Test data
    repo_id = "1cbb79ce-8994-490c-87ce-56911ab03807"
    job_id = f"test_codemirror_{datetime.now().timestamp()}"
    
    analysis_result = {
        "repo_id": repo_id,
        "analysis_depth": "quick",
        "structure": {
            "total_files": 25,
            "total_lines": 1500,
            "directories": 8,
            "languages": ["Python", "JavaScript", "TypeScript"]
        },
        "frameworks": ["FastAPI", "Svelte"],
        "analysis_type": "web",
        "completed_at": datetime.now().isoformat(),
        "insights": [
            {
                "type": "code_quality",
                "severity": "medium",
                "title": "Test Code Quality Insight",
                "description": "This is a test insight for frontend display",
                "recommendation": "Consider adding more test coverage"
            },
            {
                "type": "security_vulnerability",
                "severity": "low",
                "title": "Test Security Insight",
                "description": "Minor security observation",
                "recommendation": "Update dependencies to latest versions"
            }
        ],
        "patterns": [
            {
                "type": "mvc",
                "confidence": 0.8,
                "description": "MVC pattern detected"
            }
        ],
        "security_findings": []
    }
    
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            print("Creating test analysis data...")
            
            # Insert into processing_jobs
            await conn.execute("""
                INSERT INTO processing_jobs (
                    job_id, job_type, status, progress_percentage, 
                    result_data, completed_at
                ) VALUES ($1, $2, $3, $4, $5, NOW())
            """, job_id, "crawl_ai", "completed", 100, json.dumps(analysis_result))
            
            # Insert into codemirror_analyses
            analysis_id = await conn.fetchval("""
                INSERT INTO codemirror_analyses (
                    repo_id, job_id, analysis_type, analysis_depth,
                    results, file_count, total_lines, languages_detected,
                    frameworks_detected, security_score, performance_score,
                    quality_score, analysis_completed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())
                RETURNING id
            """, 
                repo_id, job_id, 'web', 'quick',
                json.dumps(analysis_result), 25, 1500,
                json.dumps(["Python", "JavaScript", "TypeScript"]),
                json.dumps(["FastAPI", "Svelte"]),
                85.0, 78.0, 82.0
            )
            
            # Insert insights
            for insight in analysis_result['insights']:
                await conn.execute("""
                    INSERT INTO codemirror_insights (
                        analysis_id, insight_type, title, description,
                        severity, recommendation, generated_by_agent,
                        confidence_score
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    analysis_id, insight['type'], insight['title'],
                    insight['description'], insight['severity'],
                    insight['recommendation'], 'test_script', 0.8
                )
            
            print(f"✅ Created test analysis with ID: {analysis_id}")
            print(f"✅ Job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")


async def main():
    await create_db_pool()
    await create_test_analysis_data()


if __name__ == "__main__":
    asyncio.run(main())