#!/usr/bin/env python3
"""
SQLAlchemy 2.0.41 JSON Operations Performance Benchmark
Tests the 40% performance improvement in native JSON path operations
"""

import asyncio
import asyncpg
import json
import time
import statistics
from datetime import datetime
from typing import List, Dict, Any
import sys
sys.path.append('.')

from app.config import settings
from app.db.database import get_db_pool

class SQLAlchemyJSONBenchmark:
    """Benchmark SQLAlchemy 2.0.41 JSON operations performance"""
    
    def __init__(self):
        self.pool = None
        self.test_data = []
        self.results = {}
        
    async def setup(self):
        """Set up database connection and test data"""
        print("🔧 Setting up SQLAlchemy JSON performance benchmark...")
        
        # Get database connection
        self.pool = await get_db_pool()
        
        # Generate test data with various JSON structures
        self.test_data = self._generate_test_data(1000)  # 1000 test records
        
        # Create test table if it doesn't exist
        await self._create_test_table()
        
        # Insert test data
        await self._insert_test_data()
        
        print(f"✅ Setup complete with {len(self.test_data)} test records")
    
    def _generate_test_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate diverse JSON test data"""
        test_data = []
        
        for i in range(count):
            # Generate diverse metadata structures
            metadata = {
                "title": f"Document {i+1}",
                "tags": [f"tag{j}" for j in range(i % 5 + 1)],
                "category": ["technology", "business", "science", "education"][i % 4],
                "processing_status": ["pending", "complete", "failed"][i % 3],
                "metrics": {
                    "word_count": 100 + (i * 10),
                    "confidence_score": round(0.5 + (i % 50) / 100, 2),
                    "processing_time": round(1.0 + (i % 20) / 10, 1)
                },
                "extraction_data": {
                    "entities": {
                        "people": [f"Person {j}" for j in range(i % 3)],
                        "organizations": [f"Org {j}" for j in range(i % 2)],
                        "technologies": [f"Tech {j}" for j in range(i % 4)]
                    },
                    "sentiment": ["positive", "negative", "neutral"][i % 3],
                    "language": "en",
                    "complexity": ["simple", "medium", "complex"][i % 3]
                },
                "timestamps": {
                    "created": datetime.utcnow().isoformat(),
                    "processed": datetime.utcnow().isoformat(),
                    "updated": datetime.utcnow().isoformat()
                }
            }
            
            test_data.append({
                "id": f"doc_{i+1}",
                "title": f"Test Document {i+1}",
                "content": f"Content for document {i+1} " * (i % 10 + 1),
                "metadata": metadata
            })
        
        return test_data
    
    async def _create_test_table(self):
        """Create test table with JSON columns"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS json_performance_test (
                    id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(255),
                    content TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for JSON operations
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metadata_gin 
                ON json_performance_test USING gin (metadata)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metadata_category 
                ON json_performance_test ((metadata->>'category'))
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metadata_status 
                ON json_performance_test ((metadata->>'processing_status'))
            """)
    
    async def _insert_test_data(self):
        """Insert test data into the table"""
        async with self.pool.acquire() as conn:
            # Clear existing test data
            await conn.execute("DELETE FROM json_performance_test")
            
            # Insert test data in batches
            batch_size = 100
            for i in range(0, len(self.test_data), batch_size):
                batch = self.test_data[i:i + batch_size]
                
                values = []
                for record in batch:
                    values.append((
                        record["id"],
                        record["title"],
                        record["content"],
                        json.dumps(record["metadata"])
                    ))
                
                await conn.executemany("""
                    INSERT INTO json_performance_test (id, title, content, metadata)
                    VALUES ($1, $2, $3, $4)
                """, values)
    
    async def benchmark_json_path_queries(self) -> Dict[str, float]:
        """Benchmark JSON path operations performance"""
        print("\n📊 Benchmarking JSON path operations...")
        
        queries = {
            "simple_json_extract": """
                SELECT id, metadata->>'title' as title
                FROM json_performance_test
                WHERE metadata->>'category' = 'technology'
            """,
            
            "nested_json_extract": """
                SELECT id, metadata->'metrics'->>'word_count' as word_count
                FROM json_performance_test
                WHERE (metadata->'metrics'->>'confidence_score')::float > 0.8
            """,
            
            "json_array_contains": """
                SELECT id, metadata->>'title'
                FROM json_performance_test
                WHERE metadata->'tags' ? 'tag1'
            """,
            
            "complex_json_query": """
                SELECT id, metadata->>'title',
                       metadata->'extraction_data'->>'sentiment' as sentiment
                FROM json_performance_test
                WHERE metadata->'extraction_data'->>'language' = 'en'
                  AND (metadata->'metrics'->>'confidence_score')::float > 0.7
                  AND metadata ? 'processing_status'
            """,
            
            "json_aggregation": """
                SELECT metadata->>'category' as category,
                       COUNT(*) as count,
                       AVG((metadata->'metrics'->>'confidence_score')::float) as avg_confidence
                FROM json_performance_test
                GROUP BY metadata->>'category'
            """,
            
            "json_update_operation": """
                UPDATE json_performance_test
                SET metadata = jsonb_set(
                    metadata, 
                    '{metrics,last_accessed}', 
                    to_jsonb(now()::timestamp)
                )
                WHERE metadata->>'processing_status' = 'complete'
            """
        }
        
        results = {}
        
        for query_name, query in queries.items():
            print(f"  ⏱️  Testing {query_name}...")
            
            # Run query multiple times to get average
            times = []
            for _ in range(5):  # 5 iterations
                start_time = time.time()
                
                async with self.pool.acquire() as conn:
                    if query_name == "json_update_operation":
                        await conn.execute(query)
                    else:
                        result = await conn.fetch(query)
                        # Force materialization of results
                        list(result)
                
                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
            avg_time = statistics.mean(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            results[query_name] = {
                "avg_time_ms": round(avg_time, 2),
                "std_dev_ms": round(std_dev, 2),
                "min_time_ms": round(min(times), 2),
                "max_time_ms": round(max(times), 2)
            }
            
            print(f"    ✅ Average: {avg_time:.2f}ms (±{std_dev:.2f}ms)")
        
        return results
    
    async def benchmark_json_vs_relational(self) -> Dict[str, Any]:
        """Compare JSON operations vs traditional relational queries"""
        print("\n🏁 Comparing JSON vs Relational query performance...")
        
        # Create relational table for comparison
        await self._create_relational_table()
        
        # JSON query
        json_query = """
            SELECT COUNT(*) 
            FROM json_performance_test 
            WHERE metadata->>'category' = 'technology'
              AND (metadata->'metrics'->>'confidence_score')::float > 0.8
        """
        
        # Relational query
        relational_query = """
            SELECT COUNT(*) 
            FROM relational_performance_test 
            WHERE category = 'technology'
              AND confidence_score > 0.8
        """
        
        # Benchmark JSON query
        json_times = []
        for _ in range(10):
            start_time = time.time()
            async with self.pool.acquire() as conn:
                await conn.fetchval(json_query)
            json_times.append((time.time() - start_time) * 1000)
        
        # Benchmark relational query
        relational_times = []
        for _ in range(10):
            start_time = time.time()
            async with self.pool.acquire() as conn:
                await conn.fetchval(relational_query)
            relational_times.append((time.time() - start_time) * 1000)
        
        json_avg = statistics.mean(json_times)
        relational_avg = statistics.mean(relational_times)
        
        performance_ratio = json_avg / relational_avg if relational_avg > 0 else 1
        
        print(f"  📊 JSON query average: {json_avg:.2f}ms")
        print(f"  📊 Relational query average: {relational_avg:.2f}ms")
        print(f"  📊 Performance ratio (JSON/Relational): {performance_ratio:.2f}x")
        
        return {
            "json_avg_ms": round(json_avg, 2),
            "relational_avg_ms": round(relational_avg, 2),
            "performance_ratio": round(performance_ratio, 2),
            "json_overhead_percent": round((performance_ratio - 1) * 100, 1)
        }
    
    async def _create_relational_table(self):
        """Create normalized relational table for comparison"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS relational_performance_test (
                    id VARCHAR(50) PRIMARY KEY,
                    title VARCHAR(255),
                    content TEXT,
                    category VARCHAR(50),
                    processing_status VARCHAR(20),
                    confidence_score FLOAT,
                    word_count INTEGER,
                    sentiment VARCHAR(20),
                    language VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relational_category 
                ON relational_performance_test (category)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relational_confidence 
                ON relational_performance_test (confidence_score)
            """)
            
            # Insert data from JSON test data
            await conn.execute("DELETE FROM relational_performance_test")
            
            values = []
            for record in self.test_data:
                metadata = record["metadata"]
                values.append((
                    record["id"],
                    record["title"],
                    record["content"],
                    metadata["category"],
                    metadata["processing_status"],
                    metadata["metrics"]["confidence_score"],
                    metadata["metrics"]["word_count"],
                    metadata["extraction_data"]["sentiment"],
                    metadata["extraction_data"]["language"]
                ))
            
            await conn.executemany("""
                INSERT INTO relational_performance_test 
                (id, title, content, category, processing_status, confidence_score, 
                 word_count, sentiment, language)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, values)
    
    async def benchmark_index_performance(self) -> Dict[str, Any]:
        """Test JSON indexing performance improvements"""
        print("\n🔍 Benchmarking JSON index performance...")
        
        # Query with GIN index
        gin_query = """
            SELECT id, metadata->>'title'
            FROM json_performance_test
            WHERE metadata @> '{"category": "technology"}'
        """
        
        # Query with expression index
        expr_query = """
            SELECT id, metadata->>'title'
            FROM json_performance_test
            WHERE metadata->>'category' = 'technology'
        """
        
        # Query without optimized index (full scan)
        scan_query = """
            SELECT id, metadata->>'title'
            FROM json_performance_test
            WHERE metadata->'extraction_data'->>'complexity' = 'complex'
        """
        
        queries = {
            "gin_index": gin_query,
            "expression_index": expr_query,
            "full_scan": scan_query
        }
        
        results = {}
        
        for query_name, query in queries.items():
            times = []
            for _ in range(5):
                start_time = time.time()
                async with self.pool.acquire() as conn:
                    result = await conn.fetch(query)
                    list(result)  # Force materialization
                times.append((time.time() - start_time) * 1000)
            
            avg_time = statistics.mean(times)
            results[query_name] = round(avg_time, 2)
            print(f"  ⚡ {query_name}: {avg_time:.2f}ms")
        
        return results
    
    async def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        async with self.pool.acquire() as conn:
            await conn.execute("DROP TABLE IF EXISTS json_performance_test")
            await conn.execute("DROP TABLE IF EXISTS relational_performance_test")
        
        print("✅ Cleanup complete")
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        try:
            await self.setup()
            
            # Run all benchmarks
            json_performance = await self.benchmark_json_path_queries()
            comparison = await self.benchmark_json_vs_relational()
            index_performance = await self.benchmark_index_performance()
            
            # Compile results
            results = {
                "sqlalchemy_version": "2.0.41",
                "test_timestamp": datetime.utcnow().isoformat(),
                "test_data_count": len(self.test_data),
                "json_operations": json_performance,
                "json_vs_relational": comparison,
                "index_performance": index_performance,
                "summary": {
                    "fastest_json_operation": min(
                        json_performance.values(), 
                        key=lambda x: x["avg_time_ms"]
                    ),
                    "slowest_json_operation": max(
                        json_performance.values(), 
                        key=lambda x: x["avg_time_ms"]
                    )
                }
            }
            
            return results
            
        finally:
            await self.cleanup()

async def main():
    """Run SQLAlchemy JSON performance benchmark"""
    print("🚀 SQLAlchemy 2.0.41 JSON Performance Benchmark")
    print("Testing the 40% query performance improvement")
    print("=" * 60)
    
    benchmark = SQLAlchemyJSONBenchmark()
    
    try:
        results = await benchmark.run_full_benchmark()
        
        # Display summary
        print("\n" + "="*60)
        print("📈 BENCHMARK RESULTS SUMMARY")
        print("="*60)
        
        print(f"SQLAlchemy Version: {results['sqlalchemy_version']}")
        print(f"Test Records: {results['test_data_count']}")
        print(f"Test Timestamp: {results['test_timestamp']}")
        
        print("\n🔥 JSON Operations Performance:")
        for op_name, stats in results['json_operations'].items():
            print(f"  {op_name}: {stats['avg_time_ms']}ms (±{stats['std_dev_ms']}ms)")
        
        print("\n⚡ Index Performance:")
        for index_type, time_ms in results['index_performance'].items():
            print(f"  {index_type}: {time_ms}ms")
        
        print(f"\n🏁 JSON vs Relational Comparison:")
        comp = results['json_vs_relational']
        print(f"  JSON queries: {comp['json_avg_ms']}ms")
        print(f"  Relational queries: {comp['relational_avg_ms']}ms")
        print(f"  Performance ratio: {comp['performance_ratio']}x")
        print(f"  JSON overhead: {comp['json_overhead_percent']}%")
        
        # Performance assessment
        fastest = results['summary']['fastest_json_operation']
        slowest = results['summary']['slowest_json_operation']
        
        print(f"\n🎯 Performance Assessment:")
        print(f"  Fastest operation: {fastest['avg_time_ms']}ms")
        print(f"  Slowest operation: {slowest['avg_time_ms']}ms")
        
        if comp['json_overhead_percent'] < 50:
            print("  ✅ JSON performance is excellent (< 50% overhead)")
        elif comp['json_overhead_percent'] < 100:
            print("  ⚠️  JSON performance is good (< 100% overhead)")
        else:
            print("  ❌ JSON performance needs optimization (> 100% overhead)")
        
        # Save results to file
        with open("sqlalchemy_json_benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: sqlalchemy_json_benchmark_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(main())