#!/usr/bin/env python3
"""
Performance benchmark script to validate uvloop improvements.

This script tests various async operations to measure the performance 
impact of uvloop vs default asyncio event loop.
"""

import asyncio
import aiohttp
import asyncpg
import time
import statistics
import sys
import os
from typing import List, Dict, Any

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

class PerformanceBenchmark:
    """Benchmark various async operations for uvloop performance testing."""
    
    def __init__(self, database_url: str, api_base_url: str = "http://localhost:8000"):
        self.database_url = database_url
        self.api_base_url = api_base_url
        self.results = {}
    
    async def benchmark_database_operations(self, iterations: int = 50) -> Dict[str, float]:
        """Benchmark PostgreSQL operations with asyncpg."""
        print(f"🔍 Benchmarking database operations ({iterations} iterations)...")
        
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                # Test database connection and simple query
                conn = await asyncpg.connect(self.database_url)
                await conn.fetchval("SELECT COUNT(*) FROM items")
                await conn.close()
                
                end_time = time.time()
                times.append(end_time - start_time)
                
                if (i + 1) % 10 == 0:
                    print(f"  Completed {i + 1}/{iterations} database operations")
                    
            except Exception as e:
                print(f"❌ Database operation failed: {e}")
                continue
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"📊 Database Operations Results:")
            print(f"   Average: {avg_time*1000:.2f}ms")
            print(f"   Median:  {median_time*1000:.2f}ms")
            print(f"   Min:     {min_time*1000:.2f}ms")
            print(f"   Max:     {max_time*1000:.2f}ms")
            
            return {
                "average": avg_time,
                "median": median_time,
                "min": min_time,
                "max": max_time,
                "iterations": len(times)
            }
        
        return {"error": "No successful operations"}
    
    async def benchmark_concurrent_database_operations(self, concurrency: int = 20, 
                                                      operations_per_batch: int = 5) -> Dict[str, float]:
        """Benchmark concurrent database operations."""
        print(f"🔍 Benchmarking concurrent database ops ({concurrency} concurrent, {operations_per_batch} ops each)...")
        
        async def db_operation_batch():
            """Perform a batch of database operations."""
            times = []
            for _ in range(operations_per_batch):
                start_time = time.time()
                try:
                    conn = await asyncpg.connect(self.database_url)
                    await conn.fetchval("SELECT COUNT(*) FROM items")
                    await conn.close()
                    times.append(time.time() - start_time)
                except Exception:
                    continue
            return times
        
        start_time = time.time()
        
        # Run concurrent batches
        tasks = [db_operation_batch() for _ in range(concurrency)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Collect all timing data
        all_times = []
        for result in results:
            if isinstance(result, list):
                all_times.extend(result)
        
        if all_times:
            total_operations = len(all_times)
            ops_per_second = total_operations / total_time
            avg_time = statistics.mean(all_times)
            
            print(f"📊 Concurrent Database Results:")
            print(f"   Total operations: {total_operations}")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Operations/sec: {ops_per_second:.2f}")
            print(f"   Average op time: {avg_time*1000:.2f}ms")
            
            return {
                "total_operations": total_operations,
                "total_time": total_time,
                "ops_per_second": ops_per_second,
                "average_op_time": avg_time
            }
        
        return {"error": "No successful concurrent operations"}
    
    async def benchmark_api_requests(self, iterations: int = 100) -> Dict[str, float]:
        """Benchmark API endpoint performance."""
        print(f"🔍 Benchmarking API requests ({iterations} iterations)...")
        
        times = []
        
        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                start_time = time.time()
                
                try:
                    async with session.get(f"{self.api_base_url}/health") as response:
                        await response.json()
                        
                    end_time = time.time()
                    times.append(end_time - start_time)
                    
                    if (i + 1) % 20 == 0:
                        print(f"  Completed {i + 1}/{iterations} API requests")
                        
                except Exception as e:
                    print(f"❌ API request failed: {e}")
                    continue
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            requests_per_second = 1 / avg_time if avg_time > 0 else 0
            
            print(f"📊 API Requests Results:")
            print(f"   Average: {avg_time*1000:.2f}ms")
            print(f"   Median:  {median_time*1000:.2f}ms")
            print(f"   Requests/sec: {requests_per_second:.2f}")
            
            return {
                "average": avg_time,
                "median": median_time,
                "requests_per_second": requests_per_second,
                "iterations": len(times)
            }
        
        return {"error": "No successful API requests"}
    
    async def benchmark_concurrent_api_requests(self, concurrency: int = 50) -> Dict[str, float]:
        """Benchmark concurrent API requests."""
        print(f"🔍 Benchmarking concurrent API requests ({concurrency} concurrent)...")
        
        async def make_request(session):
            try:
                start_time = time.time()
                async with session.get(f"{self.api_base_url}/health") as response:
                    await response.json()
                return time.time() - start_time
            except Exception:
                return None
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [make_request(session) for _ in range(concurrency)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Filter successful requests
        times = [r for r in results if isinstance(r, float)]
        
        if times:
            success_rate = len(times) / concurrency
            requests_per_second = len(times) / total_time
            avg_time = statistics.mean(times)
            
            print(f"📊 Concurrent API Results:")
            print(f"   Successful requests: {len(times)}/{concurrency}")
            print(f"   Success rate: {success_rate*100:.1f}%")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Requests/sec: {requests_per_second:.2f}")
            print(f"   Average time: {avg_time*1000:.2f}ms")
            
            return {
                "successful_requests": len(times),
                "total_requests": concurrency,
                "success_rate": success_rate,
                "total_time": total_time,
                "requests_per_second": requests_per_second,
                "average_time": avg_time
            }
        
        return {"error": "No successful concurrent requests"}
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run the complete benchmark suite."""
        print("🚀 Starting PRSNL Performance Benchmark Suite")
        print("=" * 60)
        
        # Test 1: Sequential database operations
        db_results = await self.benchmark_database_operations()
        self.results["database_sequential"] = db_results
        
        print()
        
        # Test 2: Concurrent database operations
        concurrent_db_results = await self.benchmark_concurrent_database_operations()
        self.results["database_concurrent"] = concurrent_db_results
        
        print()
        
        # Test 3: Sequential API requests
        api_results = await self.benchmark_api_requests()
        self.results["api_sequential"] = api_results
        
        print()
        
        # Test 4: Concurrent API requests
        concurrent_api_results = await self.benchmark_concurrent_api_requests()
        self.results["api_concurrent"] = concurrent_api_results
        
        print()
        print("=" * 60)
        print("🎯 Benchmark Complete!")
        
        return self.results

async def main():
    """Main benchmark execution."""
    # Load configuration
    try:
        from app.config import settings
        database_url = settings.DATABASE_URL
        api_url = f"http://localhost:{settings.BACKEND_PORT}"
    except ImportError:
        print("❌ Could not import settings. Using defaults.")
        database_url = "postgresql://pronav@localhost:5433/prsnl"
        api_url = "http://localhost:8000"
    
    # Check if uvloop is available
    loop_info = f"Event loop: {type(asyncio.get_event_loop()).__name__}"
    try:
        import uvloop
        if isinstance(asyncio.get_event_loop(), uvloop.Loop):
            loop_info += " (uvloop optimized ✨)"
        else:
            loop_info += " (standard asyncio)"
    except ImportError:
        loop_info += " (uvloop not available)"
    
    print(f"🔧 {loop_info}")
    print(f"🔗 Database: {database_url}")
    print(f"🌐 API: {api_url}")
    print()
    
    # Run benchmark
    benchmark = PerformanceBenchmark(database_url, api_url)
    results = await benchmark.run_full_benchmark()
    
    # Save results
    import json
    timestamp = int(time.time())
    results_file = f"benchmark_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Results saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(main())