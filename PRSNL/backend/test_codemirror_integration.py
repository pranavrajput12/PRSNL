#!/usr/bin/env python3
"""
Comprehensive Integration Tests for CodeMirror LangGraph & Enhanced AI Router Migration

This script tests all the enhanced features integrated into CodeMirror:
- LangGraph workflows
- Enhanced AI Router
- LangChain prompt templates
- HTTP Client Factory
- Fallback mechanisms
"""

import asyncio
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, List

# Add the backend directory to the path
sys.path.insert(0, '/Users/pronav/Personal Knowledge Base/PRSNL/backend')

def test_imports():
    """Test that all new imports work correctly"""
    print("🔍 Testing CodeMirror enhanced imports...")
    
    try:
        # Test LangGraph imports
        from app.services.langgraph_workflows import langgraph_workflow_service, ContentType
        print("✅ LangGraph workflows imported successfully")
        
        # Test Enhanced AI Router imports
        from app.services.ai_router import ai_router
        from app.services.ai_router_types import AITask, TaskType, TaskComplexity
        print("✅ Enhanced AI Router imported successfully")
        
        # Test LangChain prompts
        from app.services.langchain_prompts import prompt_template_manager
        print("✅ LangChain prompts imported successfully")
        
        # Test HTTP Client Factory
        from app.services.http_client_factory import http_client_factory, ClientType
        print("✅ HTTP Client Factory imported successfully")
        
        # Test updated CodeMirror services
        from app.services.codemirror_service import codemirror_service
        from app.services.codemirror_agents import (
            CodeRepositoryAnalysisAgent,
            CodePatternDetectionAgent,
            CodeInsightGeneratorAgent
        )
        print("✅ Updated CodeMirror services imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_service_initialization():
    """Test that all services initialize correctly"""
    print("\n🔍 Testing service initialization...")
    
    try:
        from app.services.codemirror_service import codemirror_service
        from app.services.codemirror_agents import CodeRepositoryAnalysisAgent
        from app.services.langgraph_workflows import langgraph_workflow_service
        from app.services.ai_router import ai_router
        from app.services.langchain_prompts import prompt_template_manager
        from app.services.http_client_factory import http_client_factory
        
        # Test CodeMirror service initialization
        assert codemirror_service.use_langgraph is not None
        assert codemirror_service.use_enhanced_routing is not None
        assert codemirror_service.use_prompt_templates is not None
        print("✅ CodeMirror service initialized with feature flags")
        
        # Test agent initialization
        agent = CodeRepositoryAnalysisAgent()
        assert agent.use_enhanced_routing is not None
        assert agent.use_prompt_templates is not None
        print("✅ CodeMirror agents initialized with enhanced features")
        
        # Test service availability
        print(f"✅ LangGraph enabled: {langgraph_workflow_service.enabled}")
        print(f"✅ Enhanced AI Router available: {hasattr(ai_router, 'execute_with_fallback')}")
        print(f"✅ Prompt templates enabled: {prompt_template_manager.enabled}")
        print(f"✅ HTTP Client Factory available: {hasattr(http_client_factory, 'client_session')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        traceback.print_exc()
        return False


async def test_langgraph_integration():
    """Test LangGraph workflow integration"""
    print("\n🔍 Testing LangGraph workflow integration...")
    
    try:
        from app.services.codemirror_service import codemirror_service
        from app.services.langgraph_workflows import langgraph_workflow_service, ContentType
        
        # Test repository data
        repo_data = {
            "id": "test-repo",
            "name": "test-repository",
            "language": "python",
            "description": "Test repository for integration testing",
            "size": 1000,
            "stargazers_count": 10,
            "forks_count": 5,
            "content": "def hello_world():\n    return 'Hello, World!'"
        }
        
        # Test LangGraph workflow processing
        if langgraph_workflow_service.enabled:
            result = await codemirror_service._process_with_langgraph_workflow(
                repo_data, "standard", "test-job-123"
            )
            assert result is not None
            print("✅ LangGraph workflow processing works")
        else:
            print("⚠️  LangGraph not available, testing fallback")
            result = await codemirror_service._fallback_analysis(repo_data, "standard")
            assert result is not None
            print("✅ LangGraph fallback works")
        
        # Test enhanced repository analysis
        enhanced_result = await codemirror_service._enhanced_repository_analysis(
            repo_data, "standard", "test-job-123"
        )
        
        assert "workflow_analysis" in enhanced_result
        assert "template_insights" in enhanced_result
        assert "analysis_metadata" in enhanced_result
        print("✅ Enhanced repository analysis works")
        
        return True
        
    except Exception as e:
        print(f"❌ LangGraph integration failed: {e}")
        traceback.print_exc()
        return False


async def test_enhanced_ai_router():
    """Test Enhanced AI Router integration"""
    print("\n🔍 Testing Enhanced AI Router integration...")
    
    try:
        from app.services.codemirror_service import codemirror_service
        from app.services.codemirror_agents import CodeRepositoryAnalysisAgent
        from app.services.ai_router_types import AITask, TaskType
        
        # Test AI task routing
        test_content = "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)"
        
        # Test service-level routing
        result = await codemirror_service._route_analysis_task(
            test_content, "code_analysis", 7, "test-job-123"
        )
        assert result is not None
        print("✅ Service-level AI routing works")
        
        # Test agent-level routing
        agent = CodeRepositoryAnalysisAgent()
        result = await agent._route_analysis_task(test_content, "complex")
        assert result is not None
        print("✅ Agent-level AI routing works")
        
        # Test direct analysis fallback
        result = await agent._execute_direct_analysis(test_content)
        assert result is not None
        print("✅ Direct analysis fallback works")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced AI Router integration failed: {e}")
        traceback.print_exc()
        return False


async def test_prompt_templates():
    """Test LangChain prompt templates integration"""
    print("\n🔍 Testing LangChain prompt templates integration...")
    
    try:
        from app.services.codemirror_service import codemirror_service
        from app.services.codemirror_agents import CodeRepositoryAnalysisAgent
        from app.services.langchain_prompts import prompt_template_manager
        
        # Test service-level template usage
        result = await codemirror_service._generate_code_insights_with_templates(
            "print('Hello, World!')",
            "test_analysis",
            "python"
        )
        assert result is not None
        print("✅ Service-level prompt templates work")
        
        # Test agent-level template usage
        agent = CodeRepositoryAnalysisAgent()
        template_result = agent._get_template_prompt(
            'code_analysis',
            {
                'code': "print('Hello, World!')",
                'analysis_type': 'test',
                'language': 'python',
                'default_prompt': 'fallback prompt'
            }
        )
        assert template_result is not None
        print("✅ Agent-level prompt templates work")
        
        # Test template fallback
        repo_data = {
            "name": "test-repo",
            "language": "python",
            "description": "Test repository",
            "file_samples": "print('Hello, World!')"
        }
        
        prompt = agent._build_analysis_prompt(repo_data, "standard")
        assert prompt is not None
        assert len(prompt) > 0
        print("✅ Template-based prompt building works")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt templates integration failed: {e}")
        traceback.print_exc()
        return False


async def test_http_client_factory():
    """Test HTTP Client Factory integration"""
    print("\n🔍 Testing HTTP Client Factory integration...")
    
    try:
        from app.services.codemirror_realtime_service import realtime_service
        from app.services.http_client_factory import http_client_factory, ClientType
        
        # Test client factory availability
        assert hasattr(http_client_factory, 'client_session')
        print("✅ HTTP Client Factory available")
        
        # Test client session creation
        async with http_client_factory.client_session(ClientType.GENERAL) as client:
            assert client is not None
            print("✅ HTTP client session creation works")
        
        # Test realtime service HTTP integration
        result = await realtime_service._make_http_request(
            "https://httpbin.org/get",
            "GET"
        )
        assert result is not None
        print("✅ Realtime service HTTP integration works")
        
        return True
        
    except Exception as e:
        print(f"❌ HTTP Client Factory integration failed: {e}")
        traceback.print_exc()
        return False


async def test_full_integration():
    """Test full integration with all features"""
    print("\n🔍 Testing full CodeMirror integration...")
    
    try:
        from app.services.codemirror_agents import CodeRepositoryAnalysisAgent
        
        # Test repository data
        repo_data = {
            "id": "test-full-integration",
            "name": "integration-test-repo",
            "language": "python",
            "description": "Full integration test repository",
            "size": 2000,
            "stargazers_count": 25,
            "forks_count": 8,
            "updated_at": "2025-01-15T10:30:00Z",
            "file_samples": """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    def process(self):
        return [x * 2 for x in self.data if x > 0]

# Example usage
processor = DataProcessor([1, -2, 3, -4, 5])
result = processor.process()
print(f"Processed data: {result}")
"""
        }
        
        # Test full agent analysis with all features
        agent = CodeRepositoryAnalysisAgent()
        result = await agent.analyze_repository(repo_data, "standard")
        
        assert result is not None
        assert result.agent_name == "CodeRepositoryAnalysisAgent"
        assert result.status == "completed"
        assert result.results is not None
        assert result.execution_time > 0
        
        print("✅ Full repository analysis works")
        print(f"   - Agent: {result.agent_name}")
        print(f"   - Status: {result.status}")
        print(f"   - Execution time: {result.execution_time:.2f}s")
        print(f"   - Results keys: {list(result.results.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {str(e) if str(e) else type(e).__name__}")
        traceback.print_exc()
        return False


async def test_configuration_flags():
    """Test configuration flag handling"""
    print("\n🔍 Testing configuration flags...")
    
    try:
        from app.services.codemirror_service import codemirror_service
        from app.services.codemirror_agents import CodeRepositoryAnalysisAgent
        from app.config import settings
        
        # Test service configuration
        assert hasattr(codemirror_service, 'use_langgraph')
        assert hasattr(codemirror_service, 'use_enhanced_routing')
        assert hasattr(codemirror_service, 'use_prompt_templates')
        print("✅ Service configuration flags work")
        
        # Test agent configuration
        agent = CodeRepositoryAnalysisAgent()
        assert hasattr(agent, 'use_enhanced_routing')
        assert hasattr(agent, 'use_prompt_templates')
        print("✅ Agent configuration flags work")
        
        # Test feature availability
        print(f"   - LangGraph enabled: {codemirror_service.use_langgraph}")
        print(f"   - Enhanced routing enabled: {codemirror_service.use_enhanced_routing}")
        print(f"   - Prompt templates enabled: {codemirror_service.use_prompt_templates}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration flags test failed: {e}")
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling and fallback mechanisms"""
    print("\n🔍 Testing error handling and fallbacks...")
    
    try:
        from app.services.codemirror_agents import CodeRepositoryAnalysisAgent
        
        # Test agent with invalid data
        agent = CodeRepositoryAnalysisAgent()
        
        # Test fallback prompt generation
        invalid_repo_data = {}
        prompt = agent._get_fallback_prompt(invalid_repo_data, "standard")
        assert prompt is not None
        assert len(prompt) > 0
        print("✅ Error handling in prompt generation works")
        
        # Test template fallback
        template_result = agent._get_template_prompt(
            'nonexistent_template',
            {'default_prompt': 'fallback prompt'}
        )
        assert template_result == 'Process this content.'
        print("✅ Template fallback works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e) if str(e) else type(e).__name__}")
        traceback.print_exc()
        return False


async def main():
    """Run all integration tests"""
    print("🚀 Starting CodeMirror Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Service Initialization", test_service_initialization),
        ("LangGraph Integration", test_langgraph_integration),
        ("Enhanced AI Router", test_enhanced_ai_router),
        ("Prompt Templates", test_prompt_templates),
        ("HTTP Client Factory", test_http_client_factory),
        ("Full Integration", test_full_integration),
        ("Configuration Flags", test_configuration_flags),
        ("Error Handling", test_error_handling)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All CodeMirror integration tests passed!")
        print("✅ LangGraph workflows integrated successfully")
        print("✅ Enhanced AI Router integrated successfully")
        print("✅ LangChain prompt templates integrated successfully")
        print("✅ HTTP Client Factory integrated successfully")
        print("✅ All fallback mechanisms working correctly")
        print("\n🚀 CodeMirror is now running with enhanced AI infrastructure!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)