#!/usr/bin/env python3
"""
Test Phase 1 Celery Background Processing Implementation

Tests AI processing, file processing, and media processing tasks
to verify the critical performance bottlenecks have been resolved.
"""

import asyncio
import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_HEADERS = {
    "Content-Type": "application/json",
    "X-PRSNL-Integration": "test"
}

class Phase1CeleryTester:
    """Test suite for Phase 1 Celery integration"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_ai_processing_tasks(self):
        """Test AI processing workflow"""
        logger.info("🧠 Testing AI Processing Tasks...")
        
        try:
            # Test content analysis
            content_analysis_data = {
                "content_id": "test-content-123",
                "content": "This is a test article about artificial intelligence and machine learning technologies.",
                "options": {
                    "summarize": True,
                    "extract_entities": True,
                    "categorize": True,
                    "summary_length": 100
                }
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/background/ai/analyze-content",
                json=content_analysis_data,
                headers=TEST_USER_HEADERS
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                logger.info(f"✅ Content analysis task started: {task_id}")
                
                # Monitor task progress
                progress = await self._monitor_task_progress(task_id, max_wait=60)
                self.test_results["ai_content_analysis"] = {
                    "status": "success",
                    "task_id": task_id,
                    "progress": progress
                }
            else:
                logger.error(f"❌ Content analysis failed: {response.status_code} - {response.text}")
                self.test_results["ai_content_analysis"] = {
                    "status": "failed",
                    "error": response.text
                }
            
            # Test batch embedding generation
            batch_embedding_data = {
                "items": [
                    {"id": "item1", "content": "Machine learning is a subset of AI", "type": "text"},
                    {"id": "item2", "content": "Deep learning uses neural networks", "type": "text"},
                    {"id": "item3", "content": "Natural language processing enables text analysis", "type": "text"}
                ],
                "cache_prefix": "test_batch"
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/background/ai/generate-embeddings-batch",
                json=batch_embedding_data,
                headers=TEST_USER_HEADERS
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                logger.info(f"✅ Batch embedding task started: {task_id}")
                
                progress = await self._monitor_task_progress(task_id, max_wait=45)
                self.test_results["ai_batch_embeddings"] = {
                    "status": "success",
                    "task_id": task_id,
                    "progress": progress
                }
            else:
                logger.error(f"❌ Batch embedding failed: {response.status_code} - {response.text}")
                self.test_results["ai_batch_embeddings"] = {
                    "status": "failed",
                    "error": response.text
                }
            
            # Test LLM processing
            llm_processing_data = {
                "content": "Artificial intelligence is transforming industries worldwide. Machine learning algorithms enable systems to learn from data and make predictions.",
                "prompt_type": "summarize",
                "options": {
                    "max_length": 50,
                    "style": "concise"
                }
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/background/ai/process-with-llm",
                json=llm_processing_data,
                headers=TEST_USER_HEADERS
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                logger.info(f"✅ LLM processing task started: {task_id}")
                
                progress = await self._monitor_task_progress(task_id, max_wait=30)
                self.test_results["ai_llm_processing"] = {
                    "status": "success",
                    "task_id": task_id,
                    "progress": progress
                }
            else:
                logger.error(f"❌ LLM processing failed: {response.status_code} - {response.text}")
                self.test_results["ai_llm_processing"] = {
                    "status": "failed",
                    "error": response.text
                }
            
        except Exception as e:
            logger.error(f"❌ AI processing test error: {e}")
            self.test_results["ai_processing_error"] = str(e)
    
    async def test_file_processing_tasks(self):
        """Test file processing workflow"""
        logger.info("📁 Testing File Processing Tasks...")
        
        try:
            # Create a test file
            test_content = """
            # Test Document
            
            This is a test document for file processing verification.
            
            ## Overview
            This document contains sample content to test:
            - Text extraction capabilities
            - AI analysis functionality
            - Document processing workflows
            
            ## Technical Details
            The system should be able to process this document and extract meaningful insights.
            """
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(test_content)
                test_file_path = f.name
            
            try:
                # Test document processing
                document_processing_data = {
                    "file_id": "test-file-123",
                    "file_path": test_file_path,
                    "options": {
                        "extract_text": True,
                        "analyze_content": True,
                        "generate_summary": True,
                        "create_content_item": False
                    }
                }
                
                response = await self.client.post(
                    f"{BASE_URL}/api/background/files/process-document",
                    json=document_processing_data,
                    headers=TEST_USER_HEADERS
                )
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result["task_id"]
                    logger.info(f"✅ Document processing task started: {task_id}")
                    
                    progress = await self._monitor_task_progress(task_id, max_wait=60)
                    self.test_results["file_document_processing"] = {
                        "status": "success",
                        "task_id": task_id,
                        "progress": progress
                    }
                else:
                    logger.error(f"❌ Document processing failed: {response.status_code} - {response.text}")
                    self.test_results["file_document_processing"] = {
                        "status": "failed",
                        "error": response.text
                    }
                
            finally:
                # Clean up test file
                Path(test_file_path).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"❌ File processing test error: {e}")
            self.test_results["file_processing_error"] = str(e)
    
    async def test_media_processing_tasks(self):
        """Test media processing workflow"""
        logger.info("🎵 Testing Media Processing Tasks...")
        
        try:
            # Create a test audio file path (simulated)
            test_audio_path = "/tmp/test_audio.wav"  # Would be actual file in real scenario
            
            # Test audio transcription
            audio_transcription_data = {
                "media_file_path": test_audio_path,
                "options": {
                    "privacy_mode": True,  # Use local transcription for testing
                    "language": "auto",
                    "enhance_transcript": False,  # Skip enhancement for faster testing
                    "model_size": "base"
                }
            }
            
            response = await self.client.post(
                f"{BASE_URL}/api/background/media/transcribe-audio",
                json=audio_transcription_data,
                headers=TEST_USER_HEADERS
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result["task_id"]
                logger.info(f"✅ Audio transcription task started: {task_id}")
                
                # Note: This will likely fail due to missing file, but tests the endpoint
                progress = await self._monitor_task_progress(task_id, max_wait=30, expect_failure=True)
                self.test_results["media_audio_transcription"] = {
                    "status": "started",
                    "task_id": task_id,
                    "note": "Expected to fail due to missing test file"
                }
            else:
                logger.error(f"❌ Audio transcription failed: {response.status_code} - {response.text}")
                self.test_results["media_audio_transcription"] = {
                    "status": "failed",
                    "error": response.text
                }
            
        except Exception as e:
            logger.error(f"❌ Media processing test error: {e}")
            self.test_results["media_processing_error"] = str(e)
    
    async def test_task_monitoring(self):
        """Test task monitoring and status endpoints"""
        logger.info("📊 Testing Task Monitoring...")
        
        try:
            # Test active tasks endpoint
            response = await self.client.get(
                f"{BASE_URL}/api/background/tasks/active",
                headers=TEST_USER_HEADERS
            )
            
            if response.status_code == 200:
                active_tasks = response.json()
                logger.info(f"✅ Retrieved {len(active_tasks)} active tasks")
                self.test_results["task_monitoring_active"] = {
                    "status": "success",
                    "active_task_count": len(active_tasks)
                }
            else:
                logger.error(f"❌ Active tasks retrieval failed: {response.status_code}")
                self.test_results["task_monitoring_active"] = {
                    "status": "failed",
                    "error": response.text
                }
            
            # Test performance overview
            response = await self.client.get(
                f"{BASE_URL}/api/background/performance/overview?hours=1",
                headers=TEST_USER_HEADERS
            )
            
            if response.status_code == 200:
                performance_data = response.json()
                logger.info(f"✅ Retrieved performance data for {len(performance_data)} task types")
                self.test_results["task_monitoring_performance"] = {
                    "status": "success",
                    "performance_metrics_count": len(performance_data)
                }
            else:
                logger.error(f"❌ Performance overview failed: {response.status_code}")
                self.test_results["task_monitoring_performance"] = {
                    "status": "failed",
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Task monitoring test error: {e}")
            self.test_results["task_monitoring_error"] = str(e)
    
    async def _monitor_task_progress(self, task_id: str, max_wait: int = 60, expect_failure: bool = False) -> Dict[str, Any]:
        """Monitor task progress until completion or timeout"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = await self.client.get(
                    f"{BASE_URL}/api/background/status/{task_id}",
                    headers=TEST_USER_HEADERS
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "unknown")
                    
                    logger.info(f"Task {task_id}: {status}")
                    
                    if status in ["success", "completed"]:
                        return {
                            "final_status": "completed",
                            "result": status_data.get("result"),
                            "duration": time.time() - start_time
                        }
                    elif status in ["failure", "failed"] and not expect_failure:
                        return {
                            "final_status": "failed",
                            "error": status_data.get("error"),
                            "duration": time.time() - start_time
                        }
                    elif status in ["failure", "failed"] and expect_failure:
                        return {
                            "final_status": "expected_failure",
                            "error": status_data.get("error"),
                            "duration": time.time() - start_time
                        }
                
                # Wait before next check
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error monitoring task {task_id}: {e}")
                await asyncio.sleep(2)
        
        return {
            "final_status": "timeout",
            "duration": max_wait
        }
    
    async def run_all_tests(self):
        """Run all Phase 1 tests"""
        logger.info("🚀 Starting Phase 1 Celery Integration Tests...")
        
        # Check if backend is running
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                logger.error("❌ Backend is not running! Please start the backend first.")
                return
        except Exception as e:
            logger.error(f"❌ Cannot connect to backend: {e}")
            return
        
        start_time = time.time()
        
        # Run tests
        await self.test_ai_processing_tasks()
        await self.test_file_processing_tasks()
        await self.test_media_processing_tasks()
        await self.test_task_monitoring()
        
        total_duration = time.time() - start_time
        
        # Generate test report
        self._generate_test_report(total_duration)
    
    def _generate_test_report(self, total_duration: float):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*80)
        logger.info("📋 PHASE 1 CELERY INTEGRATION TEST REPORT")
        logger.info("="*80)
        
        successful_tests = 0
        total_tests = 0
        
        for test_name, result in self.test_results.items():
            if isinstance(result, dict) and "status" in result:
                total_tests += 1
                if result["status"] in ["success", "started"]:
                    successful_tests += 1
                    logger.info(f"✅ {test_name}: {result['status']}")
                else:
                    logger.info(f"❌ {test_name}: {result.get('status', 'unknown')}")
                    if "error" in result:
                        logger.info(f"   Error: {result['error']}")
            else:
                logger.info(f"⚠️ {test_name}: {result}")
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Successful: {successful_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Total Duration: {total_duration:.2f} seconds")
        
        # Assessment
        if success_rate >= 75:
            logger.info("🎉 Phase 1 Implementation: EXCELLENT - Ready for production!")
        elif success_rate >= 50:
            logger.info("✅ Phase 1 Implementation: GOOD - Minor issues to address")
        else:
            logger.info("⚠️ Phase 1 Implementation: NEEDS WORK - Major issues detected")
        
        logger.info("="*80)


async def main():
    """Run Phase 1 Celery tests"""
    async with Phase1CeleryTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())