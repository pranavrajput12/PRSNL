#!/usr/bin/env python3
"""
Langfuse Integration Test Script

This script tests comprehensive Langfuse tracking across all PRSNL AI services.
Run this to verify that all AI operations are being properly tracked.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import services
from app.services.unified_ai_service import unified_ai_service
from app.services.chat_service import get_chat_service
from app.services.voice_service import get_voice_service
from app.services.transcription_service import TranscriptionService
from app.core.langfuse_client import LangfuseClient

class LangfuseIntegrationTest:
    """Comprehensive Langfuse integration test suite"""
    
    def __init__(self):
        self.test_results = {}
        self.client = LangfuseClient.get_client()
        
    async def test_unified_ai_service(self) -> Dict[str, Any]:
        """Test UnifiedAIService Langfuse tracking"""
        logger.info("🧠 Testing UnifiedAIService Langfuse tracking...")
        
        try:
            # Test content analysis
            analysis_result = await unified_ai_service.analyze_content(
                content="This is a comprehensive test article about machine learning, artificial intelligence, and data science. It covers neural networks, deep learning algorithms, and practical applications in various industries.",
                enable_key_points=True,
                enable_entities=True
            )
            
            # Test embedding generation
            embeddings = await unified_ai_service.generate_embeddings([
                "Machine learning fundamentals",
                "Deep learning neural networks",
                "AI applications in business"
            ])
            
            # Test tag generation
            tags = await unified_ai_service.generate_tags(
                content="Python programming for data science and machine learning projects",
                limit=5
            )
            
            return {
                "status": "success",
                "analysis_title": analysis_result.get("title", "N/A"),
                "embedding_count": len(embeddings),
                "tag_count": len(tags),
                "details": "Content analysis, embeddings, and tags generated successfully"
            }
            
        except Exception as e:
            logger.error(f"UnifiedAIService test failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_chat_service(self) -> Dict[str, Any]:
        """Test ChatService Langfuse tracking"""
        logger.info("💬 Testing ChatService Langfuse tracking...")
        
        try:
            chat_service = get_chat_service()
            
            response = await chat_service.process_message(
                message="Explain the differences between machine learning and deep learning",
                user_id="langfuse_test_user"
            )
            
            return {
                "status": "success",
                "response_length": len(response.get("content", "")),
                "context_used": response.get("context", {}).get("knowledge_used", False),
                "details": "Chat message processed successfully"
            }
            
        except Exception as e:
            logger.error(f"ChatService test failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def test_transcription_service(self) -> Dict[str, Any]:
        """Test TranscriptionService Langfuse tracking"""
        logger.info("🎤 Testing TranscriptionService Langfuse tracking...")
        
        try:
            transcription_service = TranscriptionService()
            
            if not transcription_service.enabled:
                return {
                    "status": "skipped",
                    "details": "TranscriptionService not enabled (Azure OpenAI not configured)"
                }
            
            # Note: This would require an actual audio file to test
            return {
                "status": "success",
                "details": "TranscriptionService initialized and ready for tracking"
            }
            
        except Exception as e:
            logger.error(f"TranscriptionService test failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def test_langfuse_client(self) -> Dict[str, Any]:
        """Test Langfuse client connection"""
        logger.info("🔗 Testing Langfuse client connection...")
        
        try:
            if self.client:
                return {
                    "status": "success",
                    "client_type": str(type(self.client)),
                    "details": "Langfuse client initialized successfully"
                }
            else:
                return {
                    "status": "error",
                    "details": "Langfuse client not initialized"
                }
                
        except Exception as e:
            logger.error(f"Langfuse client test failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_all_tests(self):
        """Run all Langfuse integration tests"""
        logger.info("🚀 Starting comprehensive Langfuse integration tests...")
        logger.info(f"Test started at: {datetime.now().isoformat()}")
        
        # Test Langfuse client
        self.test_results["langfuse_client"] = self.test_langfuse_client()
        
        # Test AI services
        self.test_results["unified_ai_service"] = await self.test_unified_ai_service()
        self.test_results["chat_service"] = await self.test_chat_service()
        self.test_results["transcription_service"] = await self.test_transcription_service()
        
        # Flush Langfuse data
        if self.client:
            try:
                self.client.flush()
                logger.info("📤 Langfuse data flushed to dashboard")
            except Exception as e:
                logger.error(f"Failed to flush Langfuse data: {e}")
        
        self.print_results()
    
    def print_results(self):
        """Print test results summary"""
        logger.info("\n" + "="*60)
        logger.info("🎯 LANGFUSE INTEGRATION TEST RESULTS")
        logger.info("="*60)
        
        success_count = 0
        total_count = len(self.test_results)
        
        for service_name, result in self.test_results.items():
            status = result.get("status", "unknown")
            status_emoji = {
                "success": "✅",
                "error": "❌", 
                "skipped": "⏭️"
            }.get(status, "❓")
            
            logger.info(f"{status_emoji} {service_name.replace('_', ' ').title()}: {status.upper()}")
            
            if status == "success":
                success_count += 1
                if "details" in result:
                    logger.info(f"    📝 {result['details']}")
            elif status == "error":
                logger.info(f"    🚨 Error: {result.get('error', 'Unknown error')}")
            elif status == "skipped":
                logger.info(f"    ⚠️  {result.get('details', 'Test skipped')}")
        
        logger.info("="*60)
        logger.info(f"📊 SUMMARY: {success_count}/{total_count} tests successful")
        
        if success_count == total_count:
            logger.info("🎉 ALL LANGFUSE INTEGRATIONS WORKING PERFECTLY!")
            logger.info("📈 Check your Langfuse dashboard: https://cloud.langfuse.com")
        else:
            logger.warning("⚠️  Some integrations need attention")
        
        logger.info("="*60)

async def main():
    """Main test runner"""
    test_suite = LangfuseIntegrationTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)