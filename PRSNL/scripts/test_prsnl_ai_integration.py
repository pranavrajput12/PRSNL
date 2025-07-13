#!/usr/bin/env python3
"""
Comprehensive Test Suite for PRSNL AI Integration
Tests both LibreChat and AutoAgent with real AI responses
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import os

# ANSI color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
RESET = '\033[0m'

class PRSNLAIIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        self.azure_api_key = os.getenv('AZURE_OPENAI_API_KEY', '')
        
    def log(self, message: str, color: str = RESET) -> None:
        """Print colored log message."""
        print(f"{color}{message}{RESET}")
        
    async def test_librechat_chat_completion(self) -> bool:
        """Test LibreChat Bridge with actual chat completion."""
        self.log("\n🔍 Testing LibreChat Chat Completion...", BLUE)
        
        # Test message
        chat_request = {
            "model": "prsnl-gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant integrated with PRSNL knowledge base."
                },
                {
                    "role": "user",
                    "content": "What is PRSNL and how does it help with personal knowledge management?"
                }
            ],
            "temperature": 0.7,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                # Test non-streaming response
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/ai/chat/completions",
                    json=chat_request,
                    headers={
                        "Content-Type": "application/json",
                        "X-PRSNL-Integration": "test-suite"
                    }
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ LibreChat chat completion successful (non-streaming)", GREEN)
                        self.log(f"   Response time: {elapsed:.2f}s")
                        
                        # Validate response structure
                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0]['message']['content']
                            self.log(f"   Model: {data.get('model')}")
                            self.log(f"   Tokens used: {data.get('usage', {}).get('total_tokens', 'N/A')}")
                            self.log(f"   Response preview: {content[:150]}...")
                            
                            # Check if response is AI-generated (not an error)
                            if len(content) > 50 and not content.startswith("Error"):
                                self.log("   ✓ Response contains AI-generated content")
                                
                                # Test streaming
                                return await self.test_librechat_streaming(chat_request)
                            else:
                                self.log(f"   ❌ Response seems invalid: {content}", RED)
                                return False
                        else:
                            self.log("   ❌ Invalid response structure", RED)
                            return False
                    else:
                        error_text = await response.text()
                        self.log(f"❌ LibreChat chat completion failed: {response.status}", RED)
                        self.log(f"   Error: {error_text[:200]}")
                        return False
                        
            except Exception as e:
                self.log(f"❌ LibreChat error: {e}", RED)
                return False
                
    async def test_librechat_streaming(self, chat_request: Dict) -> bool:
        """Test LibreChat streaming response."""
        self.log("\n🔍 Testing LibreChat Streaming...", BLUE)
        
        chat_request['stream'] = True
        
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/ai/chat/completions",
                    json=chat_request,
                    headers={
                        "Content-Type": "application/json",
                        "X-PRSNL-Integration": "test-suite"
                    }
                ) as response:
                    if response.status == 200:
                        chunks_received = 0
                        full_response = ""
                        
                        async for line in response.content:
                            if line:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    chunk_data = line_str[6:]
                                    if chunk_data == '[DONE]':
                                        break
                                    
                                    try:
                                        chunk = json.loads(chunk_data)
                                        if 'choices' in chunk and chunk['choices']:
                                            delta = chunk['choices'][0].get('delta', {})
                                            content = delta.get('content', '')
                                            full_response += content
                                            chunks_received += 1
                                    except json.JSONDecodeError:
                                        pass
                        
                        elapsed = time.time() - start_time
                        self.log(f"✅ LibreChat streaming successful", GREEN)
                        self.log(f"   Response time: {elapsed:.2f}s")
                        self.log(f"   Chunks received: {chunks_received}")
                        self.log(f"   Total response length: {len(full_response)} chars")
                        
                        if len(full_response) > 50:
                            self.log("   ✓ Streaming response contains AI content")
                            return True
                        else:
                            self.log("   ❌ Streaming response too short", RED)
                            return False
                    else:
                        self.log(f"❌ Streaming failed: {response.status}", RED)
                        return False
                        
            except Exception as e:
                self.log(f"❌ Streaming error: {e}", RED)
                return False
                
    async def test_autoagent_content_processing(self) -> bool:
        """Test AutoAgent content processing with real data."""
        self.log("\n🔍 Testing AutoAgent Content Processing...", BLUE)
        
        content_data = {
            "content": """
            Personal Knowledge Management Best Practices:
            1. Organize information hierarchically
            2. Use consistent tagging and categorization
            3. Regular review and maintenance
            4. Cross-reference related concepts
            5. Create summaries for quick reference
            """,
            "title": "Knowledge Management Guide",
            "tags": ["productivity", "organization", "learning"],
            "type": "guide"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/autoagent/process-content",
                    json=content_data
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Content processing successful", GREEN)
                        self.log(f"   Response time: {elapsed:.2f}s")
                        self.log(f"   Content ID: {data.get('content_id')}")
                        
                        processing_result = data.get('processing_result', {})
                        if 'enrichments' in processing_result:
                            enrichments = processing_result['enrichments']
                            self.log(f"   Categories: {enrichments.get('categories', [])}")
                            self.log(f"   Key concepts: {enrichments.get('key_concepts', [])[:3]}")
                            self.log(f"   Summary preview: {enrichments.get('summary', '')[:100]}...")
                            
                            if enrichments.get('summary') and len(enrichments.get('summary', '')) > 50:
                                self.log("   ✓ AI-generated enrichments received")
                                return True
                            else:
                                self.log("   ❌ Enrichments seem incomplete", RED)
                                return False
                        else:
                            self.log("   ❌ No enrichments in response", RED)
                            return False
                    else:
                        error_text = await response.text()
                        self.log(f"❌ Content processing failed: {response.status}", RED)
                        self.log(f"   Error: {error_text[:200]}")
                        return False
                        
            except Exception as e:
                self.log(f"❌ Content processing error: {e}", RED)
                return False
                
    async def test_autoagent_topic_exploration(self) -> bool:
        """Test AutoAgent topic exploration."""
        self.log("\n🔍 Testing AutoAgent Topic Exploration...", BLUE)
        
        exploration_data = {
            "topic": "Personal AI assistants for knowledge work",
            "user_interests": ["productivity", "AI", "learning"],
            "depth": 3
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/autoagent/explore-topic",
                    json=exploration_data
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Topic exploration successful", GREEN)
                        self.log(f"   Response time: {elapsed:.2f}s")
                        
                        exploration = data.get('exploration', {})
                        if 'discovered_concepts' in exploration:
                            concepts = exploration['discovered_concepts']
                            self.log(f"   Discovered concepts: {len(concepts)}")
                            self.log(f"   Related topics: {exploration.get('related_topics', [])[:3]}")
                            
                            insights = exploration.get('insights', [])
                            if insights:
                                self.log(f"   Key insight: {insights[0][:100]}...")
                                
                            if len(concepts) > 0 and insights:
                                self.log("   ✓ AI-generated exploration received")
                                return True
                            else:
                                self.log("   ❌ Exploration seems incomplete", RED)
                                return False
                        else:
                            self.log("   ❌ No exploration data in response", RED)
                            return False
                    else:
                        self.log(f"❌ Topic exploration failed: {response.status}", RED)
                        return False
                        
            except Exception as e:
                self.log(f"❌ Topic exploration error: {e}", RED)
                return False
                
    async def test_autoagent_learning_path(self) -> bool:
        """Test AutoAgent learning path creation."""
        self.log("\n🔍 Testing AutoAgent Learning Path Creation...", BLUE)
        
        path_data = {
            "goal": "Master personal knowledge management with AI tools",
            "current_knowledge": ["Basic note-taking", "File organization"],
            "time_commitment": "moderate"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/autoagent/create-learning-path",
                    json=path_data
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Learning path creation successful", GREEN)
                        self.log(f"   Response time: {elapsed:.2f}s")
                        self.log(f"   Path ID: {data.get('path_id')}")
                        
                        path = data.get('learning_path', {})
                        milestones = path.get('milestones', [])
                        
                        if milestones:
                            self.log(f"   Total milestones: {len(milestones)}")
                            self.log(f"   First milestone: {milestones[0].get('title', 'N/A')}")
                            self.log(f"   Estimated duration: {path.get('estimated_duration', 'N/A')}")
                            
                            if len(milestones) >= 3:
                                self.log("   ✓ AI-generated learning path received")
                                return True
                            else:
                                self.log("   ❌ Learning path seems too short", RED)
                                return False
                        else:
                            self.log("   ❌ No milestones in learning path", RED)
                            return False
                    else:
                        self.log(f"❌ Learning path creation failed: {response.status}", RED)
                        return False
                        
            except Exception as e:
                self.log(f"❌ Learning path error: {e}", RED)
                return False
                
    async def test_autoagent_custom_query(self) -> bool:
        """Test AutoAgent custom agent query."""
        self.log("\n🔍 Testing AutoAgent Custom Query...", BLUE)
        
        query_params = {
            "agent_name": "knowledge_curator",
            "query": "How can I improve my personal knowledge management system using AI?",
            "context": {"focus": "practical tips", "experience_level": "intermediate"}
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/autoagent/custom-agent-query",
                    params={"agent_name": query_params["agent_name"], "query": query_params["query"]},
                    json=query_params.get("context")
                ) as response:
                    elapsed = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Custom agent query successful", GREEN)
                        self.log(f"   Response time: {elapsed:.2f}s")
                        self.log(f"   Agent: {data.get('agent')}")
                        
                        response_text = data.get('response', '')
                        if response_text and len(response_text) > 100:
                            self.log(f"   Response length: {len(response_text)} chars")
                            self.log(f"   Response preview: {response_text[:150]}...")
                            self.log("   ✓ AI-generated response received")
                            return True
                        else:
                            self.log("   ❌ Response too short or empty", RED)
                            return False
                    else:
                        self.log(f"❌ Custom query failed: {response.status}", RED)
                        return False
                        
            except Exception as e:
                self.log(f"❌ Custom query error: {e}", RED)
                return False
                
    async def run_all_tests(self) -> None:
        """Run all integration tests."""
        self.log("🧠 PRSNL AI Integration Test Suite", BLUE)
        self.log("=" * 50)
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Timestamp: {datetime.now().isoformat()}")
        self.log("=" * 50)
        
        # Check Azure API key
        if not self.azure_api_key:
            self.log("⚠️ AZURE_OPENAI_API_KEY not set", YELLOW)
            self.log("Some tests may fail without proper API configuration")
        
        tests = [
            ("LibreChat Chat Completion", self.test_librechat_chat_completion),
            ("AutoAgent Content Processing", self.test_autoagent_content_processing),
            ("AutoAgent Topic Exploration", self.test_autoagent_topic_exploration),
            ("AutoAgent Learning Path", self.test_autoagent_learning_path),
            ("AutoAgent Custom Query", self.test_autoagent_custom_query),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                self.results.append((test_name, result))
                if result:
                    passed += 1
            except Exception as e:
                self.log(f"❌ {test_name} crashed: {e}", RED)
                self.results.append((test_name, False))
        
        # Summary
        self.log("\n" + "=" * 50)
        self.log("🎯 Test Results Summary", BLUE)
        self.log("=" * 50)
        
        for test_name, result in self.results:
            status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
            self.log(f"{status} {test_name}")
        
        self.log("=" * 50)
        self.log(f"Result: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("✅ All AI integrations working correctly!", GREEN)
        else:
            self.log("❌ Some AI integrations need attention.", RED)

# Main execution
if __name__ == "__main__":
    tester = PRSNLAIIntegrationTester()
    asyncio.run(tester.run_all_tests())