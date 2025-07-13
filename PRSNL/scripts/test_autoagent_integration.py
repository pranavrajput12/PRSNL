#!/usr/bin/env python3
"""
Comprehensive test suite for PRSNL AutoAgent Second Brain Integration.

This script tests all major features of the AutoAgent integration
to ensure the second brain transformation is working correctly.
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class AutoAgentTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/autoagent"
        self.results = []
    
    def log(self, message: str, color: str = NC):
        """Log a colored message."""
        print(f"{color}{message}{NC}")
    
    async def test_health(self) -> bool:
        """Test AutoAgent health endpoint."""
        self.log("\n🔍 Testing AutoAgent Health...", BLUE)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ AutoAgent health check passed", GREEN)
                        self.log(f"   Status: {data.get('status')}")
                        self.log(f"   Memory: {data.get('memory_connected')}")
                        self.log(f"   Agents: {data.get('agent_count')}")
                        return True
                    else:
                        self.log(f"❌ Health check failed: {response.status}", RED)
                        return False
            except Exception as e:
                self.log(f"❌ Health check error: {e}", RED)
                return False
    
    async def test_agent_status(self) -> bool:
        """Test agent status endpoint."""
        self.log("\n🔍 Testing Agent Status...", BLUE)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base}/agent-status") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Agent status retrieved", GREEN)
                        self.log(f"   Total agents: {data.get('total_agents')}")
                        
                        for agent in data.get('agents', []):
                            self.log(f"   - {agent['name']}: {agent['status']}")
                            self.log(f"     Capabilities: {', '.join(agent['capabilities'])}")
                        
                        return True
                    else:
                        self.log(f"❌ Agent status failed: {response.status}", RED)
                        return False
            except Exception as e:
                self.log(f"❌ Agent status error: {e}", RED)
                return False
    
    async def test_content_processing(self) -> bool:
        """Test content processing through multi-agent workflow."""
        self.log("\n🔍 Testing Content Processing...", BLUE)
        
        test_content = {
            "content": "AutoAgent is a powerful framework for creating multi-agent AI systems. It enables natural language agent creation and complex workflow orchestration.",
            "title": "Understanding AutoAgent Framework",
            "tags": ["AI", "agents", "automation"],
            "type": "technical"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_base}/process-content",
                    json=test_content
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Content processing completed", GREEN)
                        self.log(f"   Request ID: {data.get('request_id')}")
                        self.log(f"   Agents involved: {', '.join(data.get('agents_involved', []))}")
                        self.log(f"   Execution time: {data.get('execution_time'):.2f}s")
                        
                        # Check results
                        results = data.get('results', {})
                        if 'agent_outputs' in results:
                            outputs = results['agent_outputs']
                            if 'knowledge_curator' in outputs:
                                self.log("   Knowledge Curator output received ✓")
                            if 'synthesis' in outputs:
                                self.log("   Synthesis output received ✓")
                            if 'insights' in outputs:
                                self.log("   Insights generated ✓")
                        
                        return True
                    else:
                        self.log(f"❌ Content processing failed: {response.status}", RED)
                        return False
            except Exception as e:
                self.log(f"❌ Content processing error: {e}", RED)
                return False
    
    async def test_topic_exploration(self) -> bool:
        """Test topic exploration functionality."""
        self.log("\n🔍 Testing Topic Exploration...", BLUE)
        
        exploration_request = {
            "topic": "machine learning",
            "user_interests": ["deep learning", "neural networks", "transformers"],
            "depth": 2
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_base}/explore-topic",
                    json=exploration_request
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Topic exploration completed", GREEN)
                        self.log(f"   Topic: {exploration_request['topic']}")
                        self.log(f"   Execution time: {data.get('execution_time'):.2f}s")
                        
                        results = data.get('results', {})
                        explorations = results.get('explorations', {})
                        
                        if 'suggested_paths' in explorations:
                            paths = explorations['suggested_paths']
                            self.log(f"   Exploration paths found: {len(paths)}")
                        
                        if 'learning_path' in explorations:
                            self.log("   Learning path created ✓")
                        
                        return True
                    else:
                        self.log(f"❌ Topic exploration failed: {response.status}", RED)
                        return False
            except Exception as e:
                self.log(f"❌ Topic exploration error: {e}", RED)
                return False
    
    async def test_learning_path_creation(self) -> bool:
        """Test learning path creation."""
        self.log("\n🔍 Testing Learning Path Creation...", BLUE)
        
        learning_request = {
            "goal": "Master Python async programming",
            "current_knowledge": ["basic Python", "functions", "classes"],
            "time_commitment": "moderate"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_base}/create-learning-path",
                    json=learning_request
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Learning path created", GREEN)
                        
                        results = data.get('results', {})
                        if 'duration' in results:
                            self.log(f"   Duration: {results['duration']}")
                        if 'milestones' in results:
                            self.log(f"   Milestones: {len(results['milestones'])}")
                        
                        return True
                    else:
                        self.log(f"❌ Learning path creation failed: {response.status}", RED)
                        return False
            except Exception as e:
                self.log(f"❌ Learning path creation error: {e}", RED)
                return False
    
    async def test_insights_report(self) -> bool:
        """Test insights report generation."""
        self.log("\n🔍 Testing Insights Report Generation...", BLUE)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.api_base}/insights-report",
                    params={"time_period": "week"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Insights report generated", GREEN)
                        
                        report = data.get('report', {})
                        sections = report.get('sections', {})
                        
                        if 'patterns' in sections:
                            self.log("   Patterns identified ✓")
                        if 'insights' in sections:
                            self.log("   Insights generated ✓")
                        if 'exploration_suggestions' in sections:
                            self.log("   Exploration suggestions provided ✓")
                        
                        return True
                    else:
                        self.log(f"❌ Insights report failed: {response.status}", RED)
                        return False
            except Exception as e:
                self.log(f"❌ Insights report error: {e}", RED)
                return False
    
    async def test_custom_agent_query(self) -> bool:
        """Test custom agent query functionality."""
        self.log("\n🔍 Testing Custom Agent Query...", BLUE)
        
        query_data = {
            "agent_name": "knowledge_curator",
            "query": "What are the best practices for organizing a personal knowledge base?",
            "context": {"domain": "knowledge management"}
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.api_base}/custom-agent-query",
                    params={"agent_name": query_data["agent_name"], "query": query_data["query"]},
                    json=query_data.get("context")
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Custom agent query successful", GREEN)
                        self.log(f"   Agent: {data.get('agent')}")
                        self.log(f"   Context used: {data.get('context_used')}")
                        
                        response_text = data.get('response', '')
                        if response_text:
                            self.log(f"   Response preview: {response_text[:100]}...")
                        
                        return True
                    else:
                        self.log(f"❌ Custom agent query failed: {response.status}", RED)
                        return False
            except Exception as e:
                self.log(f"❌ Custom agent query error: {e}", RED)
                return False
    
    async def run_all_tests(self) -> None:
        """Run all AutoAgent integration tests."""
        self.log("🧠 PRSNL AutoAgent Integration Test Suite", BLUE)
        self.log("=" * 50)
        self.log(f"Backend URL: {self.base_url}")
        self.log(f"Timestamp: {datetime.now().isoformat()}")
        self.log("=" * 50)
        
        tests = [
            ("Health Check", self.test_health),
            ("Agent Status", self.test_agent_status),
            ("Content Processing", self.test_content_processing),
            ("Topic Exploration", self.test_topic_exploration),
            ("Learning Path Creation", self.test_learning_path_creation),
            ("Insights Report", self.test_insights_report),
            ("Custom Agent Query", self.test_custom_agent_query),
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
            status = f"{GREEN}✅ PASS{NC}" if result else f"{RED}❌ FAIL{NC}"
            self.log(f"{status} {test_name}")
        
        self.log("=" * 50)
        self.log(f"Result: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! AutoAgent second brain is fully operational!", GREEN)
        elif passed >= total - 1:
            self.log("⚠️ Most tests passed. Minor issues detected.", YELLOW)
        else:
            self.log("❌ Multiple issues detected. Check the logs above.", RED)

async def main():
    """Main test execution."""
    # Check if backend is specified
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = AutoAgentTester(backend_url)
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())