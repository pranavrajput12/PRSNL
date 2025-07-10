#!/usr/bin/env python3
"""
Comprehensive Capture System Test Suite
Tests all combinations of content types, AI settings, and input methods
"""

import asyncio
import asyncpg
import httpx
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import tempfile
import os

# Test configuration
API_BASE_URL = "http://localhost:8000/api"
DATABASE_URL = "postgresql://prsnl:prsnl123@127.0.0.1:5433/prsnl"

class CaptureTestSuite:
    def __init__(self):
        self.results = []
        self.db_conn = None
        self.http_client = None
        
    async def setup(self):
        """Initialize database connection and HTTP client"""
        self.db_conn = await asyncpg.connect(DATABASE_URL)
        self.http_client = httpx.AsyncClient(timeout=30.0)
        print("🔧 Test suite initialized")
        
    async def cleanup(self):
        """Clean up connections"""
        if self.db_conn:
            await self.db_conn.close()
        if self.http_client:
            await self.http_client.aclose()
        print("🧹 Test suite cleaned up")

    async def test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single capture scenario"""
        print(f"\n🧪 Testing: {scenario['name']}")
        
        result = {
            "scenario": scenario,
            "timestamp": datetime.now().isoformat(),
            "api_response": None,
            "database_record": None,
            "processing_status": None,
            "ai_analysis": None,
            "errors": [],
            "success": False
        }
        
        try:
            # 1. Make API request
            print(f"   📤 Sending API request...")
            api_response = await self.make_api_request(scenario["payload"])
            result["api_response"] = api_response
            
            if not api_response.get("id"):
                result["errors"].append("No item ID returned from API")
                return result
                
            item_id = api_response["id"]
            
            # 2. Wait for processing
            await asyncio.sleep(2)
            
            # 3. Check database record
            print(f"   🗄️  Checking database record...")
            db_record = await self.get_database_record(item_id)
            result["database_record"] = db_record
            
            if not db_record:
                result["errors"].append("Item not found in database")
                return result
            
            # 4. Verify database fields
            self.verify_database_fields(scenario, db_record, result)
            
            # 5. Check processing status
            await asyncio.sleep(3)  # Wait for async processing
            final_record = await self.get_database_record(item_id)
            result["processing_status"] = final_record
            
            # 6. Analyze AI processing
            self.analyze_ai_processing(scenario, final_record, result)
            
            # 7. Mark as successful if no errors
            result["success"] = len(result["errors"]) == 0
            
            status = "✅" if result["success"] else "❌"
            print(f"   {status} Test result: {'PASS' if result['success'] else 'FAIL'}")
            
            if result["errors"]:
                for error in result["errors"]:
                    print(f"       ⚠️  {error}")
                    
        except Exception as e:
            result["errors"].append(f"Test execution error: {str(e)}")
            print(f"   ❌ Test failed with exception: {e}")
            
        return result

    async def make_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request to capture endpoint"""
        url = f"{API_BASE_URL}/capture"
        
        if payload.get("file_upload"):
            # Handle file upload scenario
            files = {"files": ("test_document.txt", "This is test document content", "text/plain")}
            data = {k: v for k, v in payload.items() if k != "file_upload"}
            # Convert boolean to string for form data
            for key, value in data.items():
                if isinstance(value, bool):
                    data[key] = str(value).lower()
            
            response = await self.http_client.post(f"{API_BASE_URL}/file/upload", files=files, data=data)
        else:
            # Regular JSON request
            response = await self.http_client.post(url, json=payload)
        
        response.raise_for_status()
        return response.json()

    async def get_database_record(self, item_id: str) -> Dict[str, Any]:
        """Get item record from database"""
        query = """
        SELECT id, url, title, summary, content, raw_content, type, status,
               content_type, enable_summarization, metadata, created_at, updated_at
        FROM items WHERE id = $1
        """
        record = await self.db_conn.fetchrow(query, item_id)
        
        if record:
            return dict(record)
        return None

    def verify_database_fields(self, scenario: Dict, db_record: Dict, result: Dict):
        """Verify database fields match expectations"""
        expected = scenario.get("expected_db", {})
        
        # Check content_type
        if "content_type" in expected:
            actual = db_record.get("content_type")
            expected_ct = expected["content_type"]
            if actual != expected_ct:
                result["errors"].append(f"content_type mismatch: expected '{expected_ct}', got '{actual}'")
        
        # Check enable_summarization
        if "enable_summarization" in expected:
            actual = db_record.get("enable_summarization")
            expected_ai = expected["enable_summarization"]
            if actual != expected_ai:
                result["errors"].append(f"enable_summarization mismatch: expected {expected_ai}, got {actual}")
        
        # Check content storage
        if scenario["input_type"] == "text":
            if not db_record.get("raw_content") and not db_record.get("content"):
                result["errors"].append("Text content not stored in database")
        elif scenario["input_type"] == "url":
            if not db_record.get("url"):
                result["errors"].append("URL not stored in database")

    def analyze_ai_processing(self, scenario: Dict, db_record: Dict, result: Dict):
        """Analyze whether AI processing was applied correctly"""
        if not db_record:
            return
            
        expected_ai = scenario["payload"].get("enable_summarization", False)
        content_type = scenario["payload"].get("content_type", "auto")
        
        # Check if AI should have been used
        should_use_ai = expected_ai and content_type != "link"  # Current buggy behavior
        
        # Look for AI indicators in the record
        has_ai_summary = bool(db_record.get("summary") and len(db_record["summary"]) > 50)
        has_ai_metadata = False
        
        metadata = db_record.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
                
        if isinstance(metadata, dict):
            has_ai_metadata = bool(metadata.get("ai_analysis") or metadata.get("video_metadata", {}).get("ai_analysis"))
        
        has_ai_processing = has_ai_summary or has_ai_metadata
        
        # Verify AI usage matches expectations
        if should_use_ai and not has_ai_processing:
            result["errors"].append(f"Expected AI processing but none found (enable_summarization={expected_ai}, content_type={content_type})")
        elif not should_use_ai and has_ai_processing and content_type == "link":
            result["errors"].append(f"Unexpected AI processing for link type")
            
        result["ai_analysis"] = {
            "expected_ai": expected_ai,
            "should_use_ai": should_use_ai,
            "has_ai_processing": has_ai_processing,
            "has_ai_summary": has_ai_summary,
            "has_ai_metadata": has_ai_metadata
        }

    def generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate comprehensive test scenarios"""
        scenarios = []
        
        # URL-based scenarios
        url_tests = [
            {
                "name": "URL + Auto Detection + AI On (GitHub)",
                "input_type": "url",
                "payload": {
                    "url": "https://github.com/microsoft/vscode",
                    "content_type": "auto",
                    "enable_summarization": True,
                    "title": "VS Code Repository"
                },
                "expected_db": {
                    "content_type": "auto",
                    "enable_summarization": True
                }
            },
            {
                "name": "URL + Auto Detection + AI Off (News)",
                "input_type": "url", 
                "payload": {
                    "url": "https://news.ycombinator.com",
                    "content_type": "auto",
                    "enable_summarization": False,
                    "title": "Hacker News"
                },
                "expected_db": {
                    "content_type": "auto",
                    "enable_summarization": False
                }
            },
            {
                "name": "URL + Link Type + AI On",
                "input_type": "url",
                "payload": {
                    "url": "https://stackoverflow.com/questions/tagged/python",
                    "content_type": "link",
                    "enable_summarization": True,
                    "title": "Python Questions"
                },
                "expected_db": {
                    "content_type": "link",
                    "enable_summarization": True
                }
            },
            {
                "name": "URL + Link Type + AI Off",
                "input_type": "url",
                "payload": {
                    "url": "https://docs.python.org/3/",
                    "content_type": "link", 
                    "enable_summarization": False,
                    "title": "Python Docs"
                },
                "expected_db": {
                    "content_type": "link",
                    "enable_summarization": False
                }
            },
            {
                "name": "URL + Article Type + AI On",
                "input_type": "url",
                "payload": {
                    "url": "https://techcrunch.com/2024/01/01/tech-trends/",
                    "content_type": "article",
                    "enable_summarization": True,
                    "title": "Tech Trends Article"
                },
                "expected_db": {
                    "content_type": "article",
                    "enable_summarization": True
                }
            },
            {
                "name": "URL + Article Type + AI Off",
                "input_type": "url",
                "payload": {
                    "url": "https://example.com/article-123",
                    "content_type": "article",
                    "enable_summarization": False,
                    "title": "Sample Article"
                },
                "expected_db": {
                    "content_type": "article", 
                    "enable_summarization": False
                }
            },
            {
                "name": "URL + Video Type + AI On (YouTube)",
                "input_type": "url",
                "payload": {
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "content_type": "video",
                    "enable_summarization": True,
                    "title": "Test Video"
                },
                "expected_db": {
                    "content_type": "video",
                    "enable_summarization": True
                }
            },
            {
                "name": "URL + Video Type + AI Off (YouTube)",
                "input_type": "url",
                "payload": {
                    "url": "https://www.youtube.com/watch?v=test123",
                    "content_type": "video", 
                    "enable_summarization": False,
                    "title": "Test Video No AI"
                },
                "expected_db": {
                    "content_type": "video",
                    "enable_summarization": False
                }
            }
        ]
        scenarios.extend(url_tests)
        
        # Text-based scenarios
        text_tests = [
            {
                "name": "Text + Note Type + AI On",
                "input_type": "text",
                "payload": {
                    "content": "Meeting notes: Discussed project roadmap for Q1 2024. Key priorities include user authentication, data pipeline optimization, and mobile app development.",
                    "content_type": "note",
                    "enable_summarization": True,
                    "title": "Q1 Meeting Notes"
                },
                "expected_db": {
                    "content_type": "note",
                    "enable_summarization": True
                }
            },
            {
                "name": "Text + Note Type + AI Off", 
                "input_type": "text",
                "payload": {
                    "content": "Quick reminder: buy milk, eggs, and bread from the store.",
                    "content_type": "note",
                    "enable_summarization": False,
                    "title": "Shopping List"
                },
                "expected_db": {
                    "content_type": "note",
                    "enable_summarization": False
                }
            },
            {
                "name": "Text + Link Type + AI On",
                "input_type": "text",
                "payload": {
                    "content": "Check out this amazing tool for developers: awesome-tool.dev - it has great features for code analysis.",
                    "content_type": "link",
                    "enable_summarization": True,
                    "title": "Developer Tool Recommendation"
                },
                "expected_db": {
                    "content_type": "link",
                    "enable_summarization": True
                }
            },
            {
                "name": "Text + Link Type + AI Off",
                "input_type": "text", 
                "payload": {
                    "content": "Bookmark: important-site.com - useful resource for later",
                    "content_type": "link",
                    "enable_summarization": False,
                    "title": "Important Site Bookmark"
                },
                "expected_db": {
                    "content_type": "link",
                    "enable_summarization": False
                }
            }
        ]
        scenarios.extend(text_tests)
        
        # File upload scenarios
        file_tests = [
            {
                "name": "File + Document Type + AI On",
                "input_type": "file",
                "payload": {
                    "file_upload": True,
                    "content_type": "document",
                    "enable_summarization": True,
                    "title": "Test Document"
                },
                "expected_db": {
                    "content_type": "document",
                    "enable_summarization": True
                }
            },
            {
                "name": "File + Document Type + AI Off",
                "input_type": "file",
                "payload": {
                    "file_upload": True,
                    "content_type": "document", 
                    "enable_summarization": False,
                    "title": "Test Document No AI"
                },
                "expected_db": {
                    "content_type": "document",
                    "enable_summarization": False
                }
            }
        ]
        scenarios.extend(file_tests)
        
        return scenarios

    async def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Comprehensive Capture System Test Suite")
        print("=" * 60)
        
        await self.setup()
        
        scenarios = self.generate_test_scenarios()
        print(f"📋 Generated {len(scenarios)} test scenarios")
        
        # Run all tests
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n[{i}/{len(scenarios)}]", end=" ")
            result = await self.test_scenario(scenario)
            self.results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Generate summary report
        await self.generate_report()
        
        await self.cleanup()

    async def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group errors by type
        error_categories = {}
        for result in self.results:
            for error in result["errors"]:
                category = self.categorize_error(error)
                if category not in error_categories:
                    error_categories[category] = []
                error_categories[category].append({
                    "scenario": result["scenario"]["name"],
                    "error": error
                })
        
        if error_categories:
            print("\n🐛 ERROR ANALYSIS")
            print("-" * 40)
            for category, errors in error_categories.items():
                print(f"\n{category.upper()} ({len(errors)} issues):")
                for error_info in errors:
                    print(f"  • {error_info['scenario']}: {error_info['error']}")
        
        # AI Processing Analysis
        print("\n🤖 AI PROCESSING ANALYSIS")
        print("-" * 40)
        
        ai_expected = sum(1 for r in self.results if r.get("ai_analysis") and r.get("ai_analysis", {}).get("expected_ai", False))
        ai_actual = sum(1 for r in self.results if r.get("ai_analysis") and r.get("ai_analysis", {}).get("has_ai_processing", False))
        
        print(f"Tests expecting AI processing: {ai_expected}")
        print(f"Tests with actual AI processing: {ai_actual}")
        
        # Content Type Analysis
        print("\n📝 CONTENT TYPE ANALYSIS")
        print("-" * 40)
        
        content_type_issues = 0
        for result in self.results:
            if any("content_type mismatch" in error for error in result["errors"]):
                content_type_issues += 1
        
        print(f"Content type mismatches: {content_type_issues}")
        
        # Save detailed report to file
        report_file = f"capture_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

    def categorize_error(self, error: str) -> str:
        """Categorize error types for analysis"""
        if "content_type mismatch" in error:
            return "content_type_issues"
        elif "enable_summarization mismatch" in error:
            return "ai_flag_issues"
        elif "AI processing" in error:
            return "ai_processing_issues"
        elif "not stored" in error:
            return "storage_issues"
        else:
            return "other_issues"

async def main():
    """Main test runner"""
    test_suite = CaptureTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())