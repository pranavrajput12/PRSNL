#!/usr/bin/env python3
"""
Simple CodeMirror System Test

Basic test to verify the enterprise-grade CodeMirror system is working.
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any

import aiohttp
import asyncpg

# Configuration
BACKEND_URL = "http://localhost:8000"
DATABASE_URL = "postgresql://pronav@localhost:5432/prsnl"

class SimpleCodeMirrorTest:
    """Simple test suite for CodeMirror system."""
    
    def __init__(self):
        self.session = None
        self.db_pool = None
        self.test_repo_id = "1cbb79ce-8994-490c-87ce-56911ab03807"
        
    async def setup(self):
        """Initialize test environment."""
        print("🚀 CodeMirror Simple Test Suite")
        print("=" * 40)
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        
        # Initialize database connection
        try:
            self.db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2)
            print("✓ Database connection established")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False
        
        return True
    
    async def cleanup(self):
        """Clean up test environment."""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
        print("✓ Test environment cleaned up")
    
    async def test_backend_health(self) -> bool:
        """Test backend API health."""
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Backend health: {data.get('status')}")
                    return True
                else:
                    print(f"✗ Backend health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"✗ Backend health check error: {e}")
            return False
    
    async def test_database_schema(self) -> bool:
        """Test database schema integrity."""
        try:
            required_tables = [
                'codemirror_analyses',
                'codemirror_patterns',
                'codemirror_insights',
                'codemirror_task_workflows',
                'codemirror_task_progress'
            ]
            
            async with self.db_pool.acquire() as conn:
                missing_tables = []
                for table in required_tables:
                    exists = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = $1
                        )
                    """, table)
                    
                    if not exists:
                        missing_tables.append(table)
                
                if missing_tables:
                    print(f"✗ Missing tables: {', '.join(missing_tables)}")
                    return False
                
                print("✓ Database schema integrity verified")
                return True
        except Exception as e:
            print(f"✗ Database schema check error: {e}")
            return False
    
    async def test_task_monitoring_endpoint(self) -> bool:
        """Test task monitoring endpoints."""
        try:
            async with self.session.get(f"{BACKEND_URL}/api/tasks/active") as response:
                if response.status == 200:
                    tasks = await response.json()
                    print(f"✓ Task monitoring: {len(tasks)} active tasks")
                    return True
                else:
                    print(f"✗ Task monitoring failed: {response.status}")
                    return False
        except Exception as e:
            print(f"✗ Task monitoring error: {e}")
            return False
    
    async def test_codemirror_endpoints(self) -> bool:
        """Test basic CodeMirror endpoints."""
        try:
            # Test patterns endpoint
            async with self.session.get(f"{BACKEND_URL}/api/codemirror/patterns") as response:
                if response.status == 200:
                    patterns = await response.json()
                    print(f"✓ Patterns endpoint: {len(patterns)} patterns")
                else:
                    print(f"✗ Patterns endpoint failed: {response.status}")
                    return False
            
            # Test analyses endpoint
            async with self.session.get(f"{BACKEND_URL}/api/codemirror/analyses/{self.test_repo_id}") as response:
                if response.status == 200:
                    analyses = await response.json()
                    print(f"✓ Analyses endpoint: {len(analyses)} analyses")
                elif response.status == 404:
                    print("✓ Analyses endpoint: Repository not found (expected)")
                else:
                    print(f"✗ Analyses endpoint failed: {response.status}")
                    return False
            
            return True
        except Exception as e:
            print(f"✗ CodeMirror endpoints error: {e}")
            return False
    
    async def test_analysis_creation(self) -> bool:
        """Test analysis creation endpoint."""
        try:
            analysis_payload = {
                "repo_id": self.test_repo_id,
                "analysis_depth": "quick",
                "include_patterns": True,
                "include_insights": True
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/api/codemirror/analyze/{self.test_repo_id}",
                json=analysis_payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    job_id = result.get('job_id')
                    print(f"✓ Analysis creation: job_id {job_id}")
                    return True
                elif response.status == 404:
                    print("✓ Analysis creation: Repository not found (expected for test)")
                    return True
                else:
                    print(f"✗ Analysis creation failed: {response.status}")
                    return False
        except Exception as e:
            print(f"✗ Analysis creation error: {e}")
            return False
    
    async def test_database_performance(self) -> bool:
        """Test database performance."""
        try:
            async with self.db_pool.acquire() as conn:
                start_time = time.time()
                
                # Test basic query performance
                result = await conn.fetchrow("""
                    SELECT COUNT(*) as total_analyses
                    FROM codemirror_analyses
                    WHERE created_at > NOW() - INTERVAL '30 days'
                """)
                
                query_time = time.time() - start_time
                
                if query_time < 1.0:
                    print(f"✓ Database performance: {query_time:.3f}s")
                    return True
                else:
                    print(f"⚠ Database performance: {query_time:.3f}s (slow)")
                    return False
        except Exception as e:
            print(f"✗ Database performance error: {e}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all tests and return overall result."""
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Database Schema", self.test_database_schema),
            ("Task Monitoring", self.test_task_monitoring_endpoint),
            ("CodeMirror Endpoints", self.test_codemirror_endpoints),
            ("Analysis Creation", self.test_analysis_creation),
            ("Database Performance", self.test_database_performance),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing: {test_name}")
            
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ {test_name} failed with exception: {e}")
                failed += 1
        
        print("\n" + "=" * 40)
        print(f"Test Results: {passed} passed, {failed} failed")
        
        success_rate = (passed / (passed + failed)) * 100
        if success_rate >= 80:
            print(f"✓ Overall Status: SUCCESS ({success_rate:.1f}%)")
            return True
        else:
            print(f"✗ Overall Status: FAILURE ({success_rate:.1f}%)")
            return False

async def main():
    """Main test runner."""
    tester = SimpleCodeMirrorTest()
    
    # Setup
    if not await tester.setup():
        print("Setup failed. Exiting.")
        return 1
    
    try:
        # Run tests
        success = await tester.run_all_tests()
        return 0 if success else 1
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))