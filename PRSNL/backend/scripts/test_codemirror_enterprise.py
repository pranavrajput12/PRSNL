#!/usr/bin/env python3
"""
Enterprise CodeMirror System Test

Comprehensive test suite for the enterprise-grade CodeMirror system including:
- Celery task processing and monitoring
- Real-time WebSocket synchronization
- CLI integration with progress tracking
- Multi-agent knowledge system
- Database integrity and performance
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, List, Optional
from uuid import uuid4

import aiohttp
import asyncpg
import websockets
from celery import Celery
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

# Configuration
BACKEND_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000"
DATABASE_URL = "postgresql://pronav@localhost:5433/prsnl"
CELERY_BROKER_URL = "redis://localhost:6379/0"

console = Console()

class CodeMirrorEnterpriseTest:
    """Comprehensive test suite for enterprise CodeMirror system."""
    
    def __init__(self):
        self.session = None
        self.db_pool = None
        self.celery_app = None
        self.test_results = {}
        self.test_repo_id = "1cbb79ce-8994-490c-87ce-56911ab03807"  # Known test repo
        
    async def setup(self):
        """Initialize test environment."""
        console.print(Panel.fit("[bold blue]🚀 CodeMirror Enterprise Test Suite[/bold blue]"))
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Initialize database connection
        try:
            self.db_pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10
            )
            console.print("[green]✓[/green] Database connection established")
        except Exception as e:
            console.print(f"[red]✗[/red] Database connection failed: {e}")
            return False
        
        # Initialize Celery app
        try:
            self.celery_app = Celery(
                'test_celery',
                broker=CELERY_BROKER_URL,
                backend=CELERY_BROKER_URL
            )
            console.print("[green]✓[/green] Celery connection established")
        except Exception as e:
            console.print(f"[red]✗[/red] Celery connection failed: {e}")
            return False
        
        return True
    
    async def cleanup(self):
        """Clean up test environment."""
        if self.session:
            await self.session.close()
        if self.db_pool:
            await self.db_pool.close()
        console.print("[green]✓[/green] Test environment cleaned up")
    
    async def test_backend_health(self) -> bool:
        """Test backend API health."""
        try:
            async with self.session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    console.print(f"[green]✓[/green] Backend health: {data.get('status')}")
                    return True
                else:
                    console.print(f"[red]✗[/red] Backend health check failed: {response.status}")
                    return False
        except Exception as e:
            console.print(f"[red]✗[/red] Backend health check error: {e}")
            return False
    
    async def test_celery_health(self) -> bool:
        """Test Celery worker health."""
        try:
            async with self.session.get(f"{BACKEND_URL}/api/tasks/health") as response:
                if response.status == 200:
                    data = await response.json()
                    worker_count = len(data.get('workers', []))
                    console.print(f"[green]✓[/green] Celery health: {worker_count} workers active")
                    return True
                else:
                    console.print(f"[red]✗[/red] Celery health check failed: {response.status}")
                    return False
        except Exception as e:
            console.print(f"[red]✗[/red] Celery health check error: {e}")
            return False
    
    async def test_database_schema(self) -> bool:
        """Test database schema integrity."""
        try:
            required_tables = [
                'celery_task_meta',
                'celery_task_result',
                'codemirror_task_workflows',
                'codemirror_task_progress',
                'codemirror_analysis_results',
                'codemirror_analyses',
                'codemirror_patterns',
                'codemirror_insights'
            ]
            
            async with self.db_pool.acquire() as conn:
                for table in required_tables:
                    exists = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_name = $1
                        )
                    """, table)
                    
                    if not exists:
                        console.print(f"[red]✗[/red] Missing table: {table}")
                        return False
                
                console.print("[green]✓[/green] Database schema integrity verified")
                return True
        except Exception as e:
            console.print(f"[red]✗[/red] Database schema check error: {e}")
            return False
    
    async def test_analysis_workflow(self) -> bool:
        """Test complete analysis workflow."""
        try:
            # Start analysis
            analysis_payload = {
                "repo_id": self.test_repo_id,
                "analysis_depth": "standard",
                "include_patterns": True,
                "include_insights": True
            }
            
            async with self.session.post(
                f"{BACKEND_URL}/api/codemirror/analyze/{self.test_repo_id}",
                json=analysis_payload
            ) as response:
                if response.status != 200:
                    console.print(f"[red]✗[/red] Analysis start failed: {response.status}")
                    return False
                
                result = await response.json()
                job_id = result.get('job_id')
                
                if not job_id:
                    console.print("[red]✗[/red] No job_id returned from analysis")
                    return False
                
                console.print(f"[green]✓[/green] Analysis started with job_id: {job_id}")
                
                # Monitor progress
                return await self._monitor_analysis_progress(job_id)
        
        except Exception as e:
            console.print(f"[red]✗[/red] Analysis workflow error: {e}")
            return False
    
    async def _monitor_analysis_progress(self, job_id: str) -> bool:
        """Monitor analysis progress through various channels."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                
                task = progress.add_task("Monitoring analysis progress...", total=None)
                
                max_wait = 120  # 2 minutes
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    # Check job status
                    async with self.session.get(
                        f"{BACKEND_URL}/api/persistence/status/{job_id}"
                    ) as response:
                        if response.status == 200:
                            status_data = await response.json()
                            status = status_data.get('status')
                            progress_pct = status_data.get('progress_percentage', 0)
                            
                            progress.update(
                                task, 
                                description=f"Analysis {status} - {progress_pct}%",
                                completed=progress_pct
                            )
                            
                            if status == 'completed':
                                console.print(f"[green]✓[/green] Analysis completed: {progress_pct}%")
                                return True
                            elif status == 'failed':
                                console.print(f"[red]✗[/red] Analysis failed: {status_data.get('error', 'Unknown error')}")
                                return False
                    
                    await asyncio.sleep(2)
                
                console.print(f"[yellow]⚠[/yellow] Analysis monitoring timed out after {max_wait}s")
                return False
        
        except Exception as e:
            console.print(f"[red]✗[/red] Progress monitoring error: {e}")
            return False
    
    async def test_websocket_synchronization(self) -> bool:
        """Test WebSocket real-time synchronization."""
        try:
            test_channel = f"codemirror.test_{uuid4().hex[:8]}"
            
            async with websockets.connect(
                f"{WEBSOCKET_URL}/ws/codemirror/sync"
            ) as websocket:
                
                # Send subscription message
                await websocket.send(json.dumps({
                    "action": "subscribe",
                    "channel": test_channel
                }))
                
                # Wait for subscription confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get('status') == 'subscribed':
                    console.print(f"[green]✓[/green] WebSocket subscription successful: {test_channel}")
                    return True
                else:
                    console.print(f"[red]✗[/red] WebSocket subscription failed: {data}")
                    return False
        
        except Exception as e:
            console.print(f"[red]✗[/red] WebSocket test error: {e}")
            return False
    
    async def test_knowledge_base_integration(self) -> bool:
        """Test knowledge base integration."""
        try:
            # Create test analysis to get knowledge correlations
            async with self.db_pool.acquire() as conn:
                # Check if we have any analyses
                analysis = await conn.fetchrow("""
                    SELECT id FROM codemirror_analyses 
                    WHERE repo_id = $1 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """, self.test_repo_id)
                
                if not analysis:
                    console.print("[yellow]⚠[/yellow] No analyses found for knowledge base test")
                    return True  # Skip test if no analyses
                
                analysis_id = str(analysis['id'])
                
                # Test knowledge endpoint
                async with self.session.get(
                    f"{BACKEND_URL}/api/codemirror/analysis/{analysis_id}/knowledge"
                ) as response:
                    if response.status == 200:
                        knowledge_data = await response.json()
                        console.print(f"[green]✓[/green] Knowledge base integration: {len(knowledge_data)} items found")
                        return True
                    else:
                        console.print(f"[red]✗[/red] Knowledge base test failed: {response.status}")
                        return False
        
        except Exception as e:
            console.print(f"[red]✗[/red] Knowledge base test error: {e}")
            return False
    
    async def test_task_monitoring(self) -> bool:
        """Test task monitoring endpoints."""
        try:
            # Get active tasks
            async with self.session.get(
                f"{BACKEND_URL}/api/tasks/active"
            ) as response:
                if response.status == 200:
                    tasks = await response.json()
                    console.print(f"[green]✓[/green] Task monitoring: {len(tasks)} active tasks")
                    return True
                else:
                    console.print(f"[red]✗[/red] Task monitoring failed: {response.status}")
                    return False
        
        except Exception as e:
            console.print(f"[red]✗[/red] Task monitoring error: {e}")
            return False
    
    async def test_patterns_and_insights(self) -> bool:
        """Test patterns and insights generation."""
        try:
            # Test patterns endpoint
            async with self.session.get(
                f"{BACKEND_URL}/api/codemirror/patterns"
            ) as response:
                if response.status == 200:
                    patterns = await response.json()
                    console.print(f"[green]✓[/green] Patterns endpoint: {len(patterns)} patterns")
                else:
                    console.print(f"[red]✗[/red] Patterns endpoint failed: {response.status}")
                    return False
            
            # Test insights endpoint (if we have analyses)
            async with self.db_pool.acquire() as conn:
                analysis = await conn.fetchrow("""
                    SELECT id FROM codemirror_analyses 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                
                if analysis:
                    analysis_id = str(analysis['id'])
                    async with self.session.get(
                        f"{BACKEND_URL}/api/codemirror/insights/{analysis_id}"
                    ) as response:
                        if response.status == 200:
                            insights = await response.json()
                            console.print(f"[green]✓[/green] Insights endpoint: {len(insights)} insights")
                        else:
                            console.print(f"[yellow]⚠[/yellow] Insights endpoint returned {response.status}")
                
                return True
        
        except Exception as e:
            console.print(f"[red]✗[/red] Patterns/Insights test error: {e}")
            return False
    
    async def test_performance_metrics(self) -> bool:
        """Test system performance metrics."""
        try:
            # Database performance
            async with self.db_pool.acquire() as conn:
                start_time = time.time()
                
                # Test complex query performance
                result = await conn.fetchrow("""
                    SELECT COUNT(*) as total_analyses,
                           COUNT(CASE WHEN analysis_completed_at IS NOT NULL THEN 1 END) as completed,
                           AVG(EXTRACT(EPOCH FROM (analysis_completed_at - created_at))) as avg_duration
                    FROM codemirror_analyses
                    WHERE created_at > NOW() - INTERVAL '7 days'
                """)
                
                query_time = time.time() - start_time
                
                if query_time < 1.0:  # Should complete in under 1 second
                    console.print(f"[green]✓[/green] Database performance: {query_time:.3f}s")
                    return True
                else:
                    console.print(f"[yellow]⚠[/yellow] Database performance: {query_time:.3f}s (slow)")
                    return False
        
        except Exception as e:
            console.print(f"[red]✗[/red] Performance test error: {e}")
            return False
    
    async def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Celery Health", self.test_celery_health),
            ("Database Schema", self.test_database_schema),
            ("Analysis Workflow", self.test_analysis_workflow),
            ("WebSocket Sync", self.test_websocket_synchronization),
            ("Knowledge Base", self.test_knowledge_base_integration),
            ("Task Monitoring", self.test_task_monitoring),
            ("Patterns & Insights", self.test_patterns_and_insights),
            ("Performance Metrics", self.test_performance_metrics),
        ]
        
        report = {
            "timestamp": time.time(),
            "total_tests": len(tests),
            "passed": 0,
            "failed": 0,
            "results": {}
        }
        
        console.print(Panel.fit("[bold yellow]🧪 Running Enterprise Test Suite[/bold yellow]"))
        
        for test_name, test_func in tests:
            console.print(f"\n[blue]Testing: {test_name}[/blue]")
            
            try:
                result = await test_func()
                report["results"][test_name] = {
                    "passed": result,
                    "error": None
                }
                
                if result:
                    report["passed"] += 1
                else:
                    report["failed"] += 1
                    
            except Exception as e:
                report["results"][test_name] = {
                    "passed": False,
                    "error": str(e)
                }
                report["failed"] += 1
                console.print(f"[red]✗[/red] {test_name} failed with exception: {e}")
        
        return report
    
    def print_final_report(self, report: Dict[str, Any]):
        """Print final test report."""
        console.print("\n" + "="*60)
        
        # Summary table
        table = Table(title="Enterprise CodeMirror Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="dim")
        
        for test_name, result in report["results"].items():
            status = "[green]✓ PASSED[/green]" if result["passed"] else "[red]✗ FAILED[/red]"
            details = result["error"] if result["error"] else "OK"
            table.add_row(test_name, status, details)
        
        console.print(table)
        
        # Overall summary
        total = report["total_tests"]
        passed = report["passed"]
        failed = report["failed"]
        success_rate = (passed / total) * 100
        
        if success_rate >= 90:
            status_color = "green"
            status_text = "EXCELLENT"
        elif success_rate >= 80:
            status_color = "yellow"
            status_text = "GOOD"
        else:
            status_color = "red"
            status_text = "NEEDS IMPROVEMENT"
        
        console.print(f"\n[bold]Overall Results:[/bold]")
        console.print(f"Passed: {passed}/{total} ({success_rate:.1f}%)")
        console.print(f"Status: [{status_color}]{status_text}[/{status_color}]")
        
        return success_rate >= 80  # Return True if 80% or more tests pass

async def main():
    """Main test runner."""
    tester = CodeMirrorEnterpriseTest()
    
    # Setup
    if not await tester.setup():
        console.print("[red]Setup failed. Exiting.[/red]")
        return 1
    
    try:
        # Run tests
        report = await tester.generate_test_report()
        
        # Print report
        success = tester.print_final_report(report)
        
        return 0 if success else 1
        
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))