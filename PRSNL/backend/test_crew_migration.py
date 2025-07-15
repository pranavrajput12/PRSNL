#!/usr/bin/env python3
"""
Simple test runner for Crew.ai migration

This script runs basic tests to verify the migration is working correctly.
"""

import asyncio
import sys
import traceback
from typing import Dict, Any, List

# Add the backend directory to the path
sys.path.insert(0, '/Users/pronav/Personal Knowledge Base/PRSNL/backend')

def test_imports():
    """Test that all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        # Test base classes
        from app.agents.base_agent import PRSNLBaseAgent, AgentFactory
        from app.crews.base_crew import PRSNLBaseCrew, CrewFactory
        print("✅ Base classes imported successfully")
        
        # Test knowledge agents
        from app.agents.knowledge import (
            KnowledgeCuratorAgent,
            ResearchSynthesizerAgent,
            ContentExplorerAgent,
            LearningPathAgent
        )
        print("✅ Knowledge agents imported successfully")
        
        # Test code agents
        from app.agents.code import (
            CodeAnalystAgent,
            PatternDetectorAgent,
            InsightGeneratorAgent,
            SecurityAnalystAgent
        )
        print("✅ Code agents imported successfully")
        
        # Test conversation agents
        from app.agents.conversation import (
            ConversationAnalystAgent,
            LearningAnalyzerAgent,
            InsightExtractorAgent,
            KnowledgeGapDetectorAgent
        )
        print("✅ Conversation agents imported successfully")
        
        # Test media agents
        from app.agents.media import (
            OCRImageAgent,
            VideoProcessorAgent,
            AudioJournalAgent
        )
        print("✅ Media agents imported successfully")
        
        # Test crews
        from app.crews.knowledge_crew import KnowledgeCurationCrew
        from app.crews.code_crew import CodeAnalysisCrew
        from app.crews.conversation_crew import ConversationIntelligenceCrew
        from app.crews.media_crew import MediaProcessingCrew
        from app.crews.autonomous_crew import AutonomousOrchestratorCrew
        print("✅ Crews imported successfully")
        
        # Test services
        from app.services.crew_service import CrewService
        print("✅ Crew service imported successfully")
        
        # Test API
        from app.api.crew_api import router
        print("✅ Crew API imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False


def test_agent_creation():
    """Test agent creation"""
    print("\n🔍 Testing agent creation...")
    
    try:
        from app.agents.base_agent import PRSNLBaseAgent
        
        # Test basic agent creation
        agent = PRSNLBaseAgent(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        assert agent.role == "Test Agent"
        assert agent.goal == "Test goal"
        assert agent.backstory == "Test backstory"
        print("✅ Basic agent creation works")
        
        # Test knowledge agent creation
        from app.agents.knowledge.knowledge_curator import KnowledgeCuratorAgent
        
        curator = KnowledgeCuratorAgent()
        assert curator.role == "Knowledge Curator"
        assert len(curator.tools) > 0
        print("✅ Knowledge curator agent creation works")
        
        # Test code agent creation
        from app.agents.code.code_analyst import CodeAnalystAgent
        
        analyst = CodeAnalystAgent()
        assert analyst.role == "Code Analyst"
        assert len(analyst.tools) > 0
        print("✅ Code analyst agent creation works")
        
        # Test conversation agent creation
        from app.agents.conversation.conversation_analyst import ConversationAnalystAgent
        
        conv_analyst = ConversationAnalystAgent()
        assert conv_analyst.role == "Conversation Analyst"
        assert len(conv_analyst.tools) > 0
        print("✅ Conversation analyst agent creation works")
        
        # Test media agent creation
        from app.agents.media.ocr_image_agent import OCRImageAgent
        
        ocr_agent = OCRImageAgent()
        assert ocr_agent.role == "OCR Image Processor"
        assert len(ocr_agent.tools) > 0
        print("✅ OCR image agent creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        traceback.print_exc()
        return False


def test_crew_creation():
    """Test crew creation"""
    print("\n🔍 Testing crew creation...")
    
    try:
        from app.crews.base_crew import PRSNLBaseCrew
        
        # Test basic crew creation
        crew = PRSNLBaseCrew()
        assert crew.agents == []
        assert crew.tasks == []
        assert crew.memory is True
        assert crew.verbose is True
        print("✅ Basic crew creation works")
        
        # Test knowledge crew creation
        from app.crews.knowledge_crew import KnowledgeCurationCrew
        
        knowledge_crew = KnowledgeCurationCrew()
        assert knowledge_crew is not None
        print("✅ Knowledge crew creation works")
        
        # Test code crew creation
        from app.crews.code_crew import CodeAnalysisCrew
        
        code_crew = CodeAnalysisCrew()
        assert code_crew is not None
        print("✅ Code crew creation works")
        
        # Test conversation crew creation
        from app.crews.conversation_crew import ConversationIntelligenceCrew
        
        conv_crew = ConversationIntelligenceCrew()
        assert conv_crew is not None
        print("✅ Conversation crew creation works")
        
        # Test media crew creation
        from app.crews.media_crew import MediaProcessingCrew
        
        media_crew = MediaProcessingCrew()
        assert media_crew is not None
        print("✅ Media crew creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Crew creation failed: {e}")
        traceback.print_exc()
        return False


def test_autonomous_system():
    """Test autonomous system components"""
    print("\n🔍 Testing autonomous system...")
    
    try:
        from app.crews.autonomous_crew import (
            AutonomousOrchestratorCrew,
            DynamicCrewComposerCrew,
            AutonomousWorkflowManager,
            AutonomousResourceManager
        )
        
        # Test resource manager
        resource_manager = AutonomousResourceManager()
        assert resource_manager.resource_pool["cpu_usage"] == 0.0
        assert resource_manager.check_resource_availability({"cpu": 0.5, "memory": 0.5}) is True
        print("✅ Resource manager works")
        
        # Test orchestrator crew
        orchestrator = AutonomousOrchestratorCrew()
        assert orchestrator.active_workflows == {}
        assert orchestrator.workflow_queue == []
        print("✅ Orchestrator crew works")
        
        # Test dynamic crew composer
        composer = DynamicCrewComposerCrew()
        assert composer is not None
        print("✅ Dynamic crew composer works")
        
        # Test workflow manager
        workflow_manager = AutonomousWorkflowManager()
        assert workflow_manager.active_workflows == {}
        assert workflow_manager.workflow_history == []
        print("✅ Workflow manager works")
        
        return True
        
    except Exception as e:
        print(f"❌ Autonomous system failed: {e}")
        traceback.print_exc()
        return False


def test_registries():
    """Test agent and crew registries"""
    print("\n🔍 Testing registries...")
    
    try:
        from app.agents import AGENT_REGISTRY, list_agents
        from app.crews import CREW_REGISTRY, list_crews
        
        # Test agent registry
        agents = list_agents()
        assert len(agents) > 0
        print(f"✅ Agent registry has {len(agents)} agents")
        
        # Test crew registry
        crews = list_crews()
        assert len(crews) > 0
        print(f"✅ Crew registry has {len(crews)} crews")
        
        # Print registered agents and crews
        print(f"📋 Registered agents: {', '.join(agents)}")
        print(f"📋 Registered crews: {', '.join(crews)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Registry test failed: {e}")
        traceback.print_exc()
        return False


def test_service_integration():
    """Test service integration"""
    print("\n🔍 Testing service integration...")
    
    try:
        from app.services.crew_service import CrewService
        
        # Test service creation
        service = CrewService()
        assert service.monitoring_service is not None
        assert service.active_crews == {}
        print("✅ Crew service creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Service integration failed: {e}")
        traceback.print_exc()
        return False


async def test_async_operations():
    """Test async operations"""
    print("\n🔍 Testing async operations...")
    
    try:
        from app.crews.autonomous_crew import AutonomousOrchestratorCrew
        
        orchestrator = AutonomousOrchestratorCrew()
        
        # Test async request analysis
        request = {
            "goal": "Test goal",
            "context": {"test": "data"}
        }
        
        result = await orchestrator.analyze_request(request)
        assert "complexity" in result
        assert "required_crews" in result
        print("✅ Async request analysis works")
        
        # Test async workflow planning
        analysis = {
            "complexity": "medium",
            "required_crews": ["knowledge_curation"]
        }
        
        plan = await orchestrator.plan_workflow(analysis)
        assert "steps" in plan
        assert "dependencies" in plan
        print("✅ Async workflow planning works")
        
        return True
        
    except Exception as e:
        print(f"❌ Async operations failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Crew.ai Migration Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_agent_creation,
        test_crew_creation,
        test_autonomous_system,
        test_registries,
        test_service_integration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    # Run async test
    try:
        if asyncio.run(test_async_operations()):
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print(f"❌ Async test failed with exception: {e}")
        failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Crew.ai migration is working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())