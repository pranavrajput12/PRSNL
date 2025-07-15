"""
Comprehensive tests for Crew.ai system migration

This test suite covers all aspects of the Crew.ai migration including:
- Base agent and crew functionality
- All migrated agent types
- Crew orchestration and execution
- Autonomous system operations
- API endpoints
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from app.agents.base_agent import PRSNLBaseAgent, AgentFactory
from app.crews.base_crew import PRSNLBaseCrew, CrewFactory
from app.services.crew_service import CrewService
from app.crews.autonomous_crew import (
    AutonomousOrchestratorCrew,
    DynamicCrewComposerCrew,
    AutonomousWorkflowManager,
    AutonomousResourceManager
)


class TestPRSNLBaseAgent:
    """Test base agent functionality"""
    
    def test_base_agent_initialization(self):
        """Test base agent initialization"""
        agent = PRSNLBaseAgent(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        assert agent.role == "Test Agent"
        assert agent.goal == "Test goal"
        assert agent.backstory == "Test backstory"
        assert agent.tools == []
        assert agent.memory is True
        assert agent.verbose is True
    
    def test_agent_creation_with_tools(self):
        """Test agent creation with tools"""
        mock_tools = [Mock(), Mock()]
        agent = PRSNLBaseAgent(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory",
            tools=mock_tools
        )
        
        assert agent.tools == mock_tools
    
    def test_get_agent_creates_crew_agent(self):
        """Test that get_agent creates a proper Crew.ai Agent"""
        agent = PRSNLBaseAgent(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        # Mock the Agent import to avoid actual Crew.ai dependency in tests
        with patch('app.agents.base_agent.Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance
            
            crew_agent = agent.get_agent()
            
            assert crew_agent == mock_agent_instance
            mock_agent_class.assert_called_once()
    
    def test_agent_caching(self):
        """Test that agent instances are cached"""
        agent = PRSNLBaseAgent(
            role="Test Agent",
            goal="Test goal",
            backstory="Test backstory"
        )
        
        with patch('app.agents.base_agent.Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance
            
            # First call should create agent
            crew_agent1 = agent.get_agent()
            # Second call should return cached agent
            crew_agent2 = agent.get_agent()
            
            assert crew_agent1 == crew_agent2
            mock_agent_class.assert_called_once()


class TestAgentFactory:
    """Test agent factory functionality"""
    
    def test_agent_factory_create_agent(self):
        """Test agent factory creates correct agent types"""
        with patch('app.agents.AGENT_REGISTRY') as mock_registry:
            mock_agent_class = Mock()
            mock_agent_instance = Mock()
            mock_agent_class.return_value = mock_agent_instance
            mock_registry.get.return_value = mock_agent_class
            
            agent = AgentFactory.create_agent("test_agent", role="Custom Role")
            
            assert agent == mock_agent_instance
            mock_registry.get.assert_called_once_with("test_agent")
            mock_agent_class.assert_called_once_with(role="Custom Role")
    
    def test_agent_factory_unknown_agent(self):
        """Test agent factory with unknown agent type"""
        with patch('app.agents.AGENT_REGISTRY') as mock_registry:
            mock_registry.get.return_value = None
            
            with pytest.raises(ValueError, match="Unknown agent type"):
                AgentFactory.create_agent("unknown_agent")


class TestPRSNLBaseCrew:
    """Test base crew functionality"""
    
    def test_base_crew_initialization(self):
        """Test base crew initialization"""
        crew = PRSNLBaseCrew()
        
        assert crew.agents == []
        assert crew.tasks == []
        assert crew.memory is True
        assert crew.verbose is True
    
    @pytest.mark.asyncio
    async def test_crew_job_creation(self):
        """Test crew job creation"""
        crew = PRSNLBaseCrew()
        
        with patch('app.crews.base_crew.JobPersistenceService') as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.create_job = AsyncMock(return_value="job_123")
            
            with patch('app.crews.base_crew.get_db_pool') as mock_pool:
                mock_connection = Mock()
                mock_pool.return_value.acquire.return_value.__aenter__.return_value = mock_connection
                
                job_id = await crew.create_job("test_job", {"data": "test"})
                
                assert job_id == "job_123"
                mock_service_instance.create_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_crew_job_completion(self):
        """Test crew job completion"""
        crew = PRSNLBaseCrew()
        crew.current_job_id = "job_123"
        
        with patch('app.crews.base_crew.JobPersistenceService') as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.complete_job = AsyncMock()
            
            with patch('app.crews.base_crew.get_db_pool') as mock_pool:
                mock_connection = Mock()
                mock_pool.return_value.acquire.return_value.__aenter__.return_value = mock_connection
                
                await crew.complete_job({"result": "success"})
                
                mock_service_instance.complete_job.assert_called_once_with(
                    "job_123", {"result": "success"}
                )


class TestCrewFactory:
    """Test crew factory functionality"""
    
    def test_crew_factory_create_crew(self):
        """Test crew factory creates correct crew types"""
        with patch('app.crews.CREW_REGISTRY') as mock_registry:
            mock_crew_class = Mock()
            mock_crew_instance = Mock()
            mock_crew_class.return_value = mock_crew_instance
            mock_registry.get.return_value = mock_crew_class
            
            crew = CrewFactory.create_crew("test_crew", param1="value1")
            
            assert crew == mock_crew_instance
            mock_registry.get.assert_called_once_with("test_crew")
            mock_crew_class.assert_called_once_with(param1="value1")
    
    def test_crew_factory_unknown_crew(self):
        """Test crew factory with unknown crew type"""
        with patch('app.crews.CREW_REGISTRY') as mock_registry:
            mock_registry.get.return_value = None
            
            with pytest.raises(ValueError, match="Unknown crew type"):
                CrewFactory.create_crew("unknown_crew")


class TestKnowledgeAgents:
    """Test knowledge agents migration"""
    
    def test_knowledge_curator_agent(self):
        """Test knowledge curator agent initialization"""
        from app.agents.knowledge.knowledge_curator import KnowledgeCuratorAgent
        
        agent = KnowledgeCuratorAgent()
        
        assert agent.role == "Knowledge Curator"
        assert "curate" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_research_synthesizer_agent(self):
        """Test research synthesizer agent initialization"""
        from app.agents.knowledge.research_synthesizer import ResearchSynthesizerAgent
        
        agent = ResearchSynthesizerAgent()
        
        assert agent.role == "Research Synthesizer"
        assert "synthesize" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_content_explorer_agent(self):
        """Test content explorer agent initialization"""
        from app.agents.knowledge.content_explorer import ContentExplorerAgent
        
        agent = ContentExplorerAgent()
        
        assert agent.role == "Content Explorer"
        assert "explore" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_learning_path_agent(self):
        """Test learning path agent initialization"""
        from app.agents.knowledge.learning_path import LearningPathAgent
        
        agent = LearningPathAgent()
        
        assert agent.role == "Learning Path Creator"
        assert "learning" in agent.goal.lower()
        assert len(agent.tools) > 0


class TestCodeAgents:
    """Test code agents migration"""
    
    def test_code_analyst_agent(self):
        """Test code analyst agent initialization"""
        from app.agents.code.code_analyst import CodeAnalystAgent
        
        agent = CodeAnalystAgent()
        
        assert agent.role == "Code Analyst"
        assert "analyze" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_pattern_detector_agent(self):
        """Test pattern detector agent initialization"""
        from app.agents.code.pattern_detector import PatternDetectorAgent
        
        agent = PatternDetectorAgent()
        
        assert agent.role == "Pattern Detector"
        assert "pattern" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_insight_generator_agent(self):
        """Test insight generator agent initialization"""
        from app.agents.code.insight_generator import InsightGeneratorAgent
        
        agent = InsightGeneratorAgent()
        
        assert agent.role == "Insight Generator"
        assert "insight" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_security_analyst_agent(self):
        """Test security analyst agent initialization"""
        from app.agents.code.security_analyst import SecurityAnalystAgent
        
        agent = SecurityAnalystAgent()
        
        assert agent.role == "Security Analyst"
        assert "security" in agent.goal.lower()
        assert len(agent.tools) > 0


class TestConversationAgents:
    """Test conversation agents migration"""
    
    def test_conversation_analyst_agent(self):
        """Test conversation analyst agent initialization"""
        from app.agents.conversation.conversation_analyst import ConversationAnalystAgent
        
        agent = ConversationAnalystAgent()
        
        assert agent.role == "Conversation Analyst"
        assert "conversation" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_learning_analyzer_agent(self):
        """Test learning analyzer agent initialization"""
        from app.agents.conversation.learning_analyzer import LearningAnalyzerAgent
        
        agent = LearningAnalyzerAgent()
        
        assert agent.role == "Learning Pattern Analyzer"
        assert "learning" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_insight_extractor_agent(self):
        """Test insight extractor agent initialization"""
        from app.agents.conversation.insight_extractor import InsightExtractorAgent
        
        agent = InsightExtractorAgent()
        
        assert agent.role == "Actionable Insight Extractor"
        assert "insight" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_knowledge_gap_detector_agent(self):
        """Test knowledge gap detector agent initialization"""
        from app.agents.conversation.knowledge_gap_detector import KnowledgeGapDetectorAgent
        
        agent = KnowledgeGapDetectorAgent()
        
        assert agent.role == "Knowledge Gap Detector"
        assert "gap" in agent.goal.lower()
        assert len(agent.tools) > 0


class TestMediaAgents:
    """Test media agents migration"""
    
    def test_ocr_image_agent(self):
        """Test OCR image agent initialization"""
        from app.agents.media.ocr_image_agent import OCRImageAgent
        
        agent = OCRImageAgent()
        
        assert agent.role == "OCR Image Processor"
        assert "ocr" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_video_processor_agent(self):
        """Test video processor agent initialization"""
        from app.agents.media.video_processor import VideoProcessorAgent
        
        agent = VideoProcessorAgent()
        
        assert agent.role == "Video Processor"
        assert "video" in agent.goal.lower()
        assert len(agent.tools) > 0
    
    def test_audio_journal_agent(self):
        """Test audio journal agent initialization"""
        from app.agents.media.audio_journal import AudioJournalAgent
        
        agent = AudioJournalAgent()
        
        assert agent.role == "Audio Journal Processor"
        assert "audio" in agent.goal.lower()
        assert len(agent.tools) > 0


class TestAutonomousResourceManager:
    """Test autonomous resource manager"""
    
    def test_resource_manager_initialization(self):
        """Test resource manager initialization"""
        manager = AutonomousResourceManager()
        
        assert manager.resource_pool["cpu_usage"] == 0.0
        assert manager.resource_pool["memory_usage"] == 0.0
        assert manager.resource_pool["active_agents"] == 0
        assert manager.resource_pool["concurrent_crews"] == 0
        assert manager.resource_limits["max_cpu"] == 0.8
        assert manager.resource_limits["max_memory"] == 0.8
    
    def test_resource_availability_check(self):
        """Test resource availability checking"""
        manager = AutonomousResourceManager()
        
        # Should have resources available initially
        assert manager.check_resource_availability({"cpu": 0.5, "memory": 0.5}) is True
        
        # Should not have resources if requesting too much
        assert manager.check_resource_availability({"cpu": 0.9, "memory": 0.5}) is False
        assert manager.check_resource_availability({"cpu": 0.5, "memory": 0.9}) is False
    
    def test_resource_allocation(self):
        """Test resource allocation and release"""
        manager = AutonomousResourceManager()
        
        # Allocate resources
        assert manager.allocate_resources("workflow_1", {"cpu": 0.3, "memory": 0.2, "agents": 2}) is True
        
        assert manager.resource_pool["cpu_usage"] == 0.3
        assert manager.resource_pool["memory_usage"] == 0.2
        assert manager.resource_pool["active_agents"] == 2
        
        # Release resources
        manager.release_resources("workflow_1", {"cpu": 0.3, "memory": 0.2, "agents": 2})
        
        assert manager.resource_pool["cpu_usage"] == 0.0
        assert manager.resource_pool["memory_usage"] == 0.0
        assert manager.resource_pool["active_agents"] == 0
    
    def test_resource_allocation_failure(self):
        """Test resource allocation failure when insufficient resources"""
        manager = AutonomousResourceManager()
        
        # Allocate most resources
        assert manager.allocate_resources("workflow_1", {"cpu": 0.7, "memory": 0.7}) is True
        
        # Try to allocate more than available
        assert manager.allocate_resources("workflow_2", {"cpu": 0.2, "memory": 0.2}) is False


class TestAutonomousOrchestratorCrew:
    """Test autonomous orchestrator crew"""
    
    def test_orchestrator_crew_initialization(self):
        """Test orchestrator crew initialization"""
        crew = AutonomousOrchestratorCrew()
        
        assert crew.mode.value in ["reactive", "proactive", "hybrid", "scheduled"]
        assert crew.active_workflows == {}
        assert crew.workflow_queue == []
        assert crew.resource_manager is not None
    
    @pytest.mark.asyncio
    async def test_analyze_request(self):
        """Test request analysis"""
        crew = AutonomousOrchestratorCrew()
        
        request = {
            "goal": "Test goal",
            "context": {"test": "data"},
            "complexity": "medium"
        }
        
        result = await crew.analyze_request(request)
        
        assert "complexity" in result
        assert "required_crews" in result
        assert "estimated_duration" in result
        assert "resource_requirements" in result
    
    @pytest.mark.asyncio
    async def test_plan_workflow(self):
        """Test workflow planning"""
        crew = AutonomousOrchestratorCrew()
        
        analysis = {
            "complexity": "medium",
            "required_crews": ["knowledge_curation"],
            "estimated_duration": "10_minutes"
        }
        
        plan = await crew.plan_workflow(analysis)
        
        assert "steps" in plan
        assert "dependencies" in plan
        assert "resource_allocation" in plan
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self):
        """Test workflow execution"""
        crew = AutonomousOrchestratorCrew()
        
        plan = {
            "steps": [
                {"crew": "knowledge_curation", "task": "curate_knowledge"}
            ],
            "dependencies": [],
            "resource_allocation": {"cpu": 0.3, "memory": 0.2}
        }
        
        result = await crew.execute_workflow(plan)
        
        assert "status" in result
        assert "output" in result


class TestDynamicCrewComposerCrew:
    """Test dynamic crew composer"""
    
    def test_composer_initialization(self):
        """Test composer initialization"""
        composer = DynamicCrewComposerCrew()
        
        assert composer is not None
    
    def test_get_available_agents(self):
        """Test getting available agents"""
        composer = DynamicCrewComposerCrew()
        
        with patch('app.crews.autonomous_crew.AGENT_REGISTRY') as mock_registry:
            mock_registry.items.return_value = [
                ("test_agent", Mock()),
                ("another_agent", Mock())
            ]
            
            agents = composer.get_available_agents()
            
            assert len(agents) == 2
            assert agents[0]["type"] == "test_agent"
            assert agents[1]["type"] == "another_agent"
    
    def test_match_capabilities(self):
        """Test capability matching"""
        composer = DynamicCrewComposerCrew()
        
        requirements = {"capabilities": ["analysis", "synthesis"]}
        agents = [
            {"type": "agent1", "capabilities": ["analysis", "synthesis"]},
            {"type": "agent2", "capabilities": ["analysis"]},
            {"type": "agent3", "capabilities": ["other"]}
        ]
        
        matched = composer.match_capabilities(requirements, agents)
        
        assert len(matched) == 2
        assert matched[0]["type"] == "agent1"
        assert matched[0]["match_score"] == 2
        assert matched[1]["type"] == "agent2"
        assert matched[1]["match_score"] == 1
    
    def test_create_crew_config(self):
        """Test crew configuration creation"""
        composer = DynamicCrewComposerCrew()
        
        agents = [
            {"type": "agent1", "match_score": 2},
            {"type": "agent2", "match_score": 1}
        ]
        requirements = {"task_id": "test_task", "max_crew_size": 3}
        
        config = composer.create_crew_config(agents, requirements)
        
        assert config["crew_id"] == "dynamic_test_task"
        assert len(config["agents"]) == 2
        assert config["process"] == "sequential"
        assert "resource_allocation" in config
        assert "estimated_duration" in config


class TestAutonomousWorkflowManager:
    """Test autonomous workflow manager"""
    
    def test_workflow_manager_initialization(self):
        """Test workflow manager initialization"""
        manager = AutonomousWorkflowManager()
        
        assert manager.orchestrator is not None
        assert manager.composer is not None
        assert manager.improver is not None
        assert manager.resource_manager is not None
        assert manager.active_workflows == {}
        assert manager.workflow_history == []
    
    @pytest.mark.asyncio
    async def test_process_request(self):
        """Test request processing"""
        manager = AutonomousWorkflowManager()
        
        request = {
            "id": "test_request",
            "goal": "Test goal",
            "context": {},
            "resources": {"cpu": 0.3, "memory": 0.3, "agents": 2}
        }
        
        # Mock the orchestrator execution
        with patch.object(manager.orchestrator, 'execute_autonomous_workflow') as mock_execute:
            mock_execute.return_value = {
                "workflow_id": "test_workflow",
                "status": "completed",
                "result": {"output": "success"}
            }
            
            with patch.object(manager, 'execute_workflow') as mock_execute_workflow:
                mock_execute_workflow.return_value = {
                    "workflow_id": "test_workflow",
                    "status": "completed",
                    "results": []
                }
                
                result = await manager.process_request(request)
                
                assert "workflow_id" in result
                assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_process_request_insufficient_resources(self):
        """Test request processing with insufficient resources"""
        manager = AutonomousWorkflowManager()
        
        request = {
            "id": "test_request",
            "goal": "Test goal",
            "context": {},
            "resources": {"cpu": 0.9, "memory": 0.9, "agents": 20}  # Too much
        }
        
        result = await manager.process_request(request)
        
        assert result["status"] == "rejected"
        assert result["reason"] == "insufficient_resources"
    
    def test_collect_performance_data(self):
        """Test performance data collection"""
        manager = AutonomousWorkflowManager()
        
        # Add some mock history
        manager.workflow_history = [
            {"result": {"status": "completed"}, "duration": 10},
            {"result": {"status": "completed"}, "duration": 15},
            {"result": {"status": "failed"}, "duration": 5}
        ]
        
        data = manager.collect_performance_data()
        
        assert data["total_workflows"] == 3
        assert data["success_rate"] == 2/3
        assert data["average_duration"] == 10.0
        assert "resource_utilization" in data
        assert "common_failures" in data
    
    def test_calculate_success_rate(self):
        """Test success rate calculation"""
        manager = AutonomousWorkflowManager()
        
        # Test with empty history
        assert manager.calculate_success_rate() == 0.0
        
        # Test with mixed results
        manager.workflow_history = [
            {"result": {"status": "completed"}},
            {"result": {"status": "completed"}},
            {"result": {"status": "failed"}}
        ]
        
        assert manager.calculate_success_rate() == 2/3
    
    def test_analyze_common_failures(self):
        """Test common failure analysis"""
        manager = AutonomousWorkflowManager()
        
        manager.workflow_history = [
            {"result": {"status": "failed", "error": "timeout"}},
            {"result": {"status": "failed", "error": "timeout"}},
            {"result": {"status": "failed", "error": "memory_error"}},
            {"result": {"status": "completed"}}
        ]
        
        failures = manager.analyze_common_failures()
        
        assert len(failures) == 2
        assert failures[0]["error"] == "timeout"
        assert failures[0]["count"] == 2
        assert failures[1]["error"] == "memory_error"
        assert failures[1]["count"] == 1


class TestCrewService:
    """Test crew service"""
    
    def test_crew_service_initialization(self):
        """Test crew service initialization"""
        service = CrewService()
        
        assert service.monitoring_service is not None
        assert service.active_crews == {}
    
    @pytest.mark.asyncio
    async def test_execute_crew(self):
        """Test crew execution"""
        service = CrewService()
        
        with patch.object(service, '_execute_crew_async') as mock_execute:
            mock_execute.return_value = {"result": "success"}
            
            with patch('app.services.crew_service.CrewFactory') as mock_factory:
                mock_crew = Mock()
                mock_crew.create_job = AsyncMock(return_value="job_123")
                mock_factory.create_crew.return_value = mock_crew
                
                result = await service.execute_crew(
                    crew_type="test_crew",
                    inputs={"test": "data"},
                    async_execution=False
                )
                
                assert result["job_id"] == "job_123"
                assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_create_autonomous_crew(self):
        """Test autonomous crew creation"""
        service = CrewService()
        
        with patch('app.services.crew_service.autonomous_manager') as mock_manager:
            mock_manager.process_request = AsyncMock(return_value={
                "request_id": "req_123",
                "status": "completed",
                "result": {"output": "success"}
            })
            
            result = await service.create_autonomous_crew(
                goal="Test goal",
                context={"test": "data"},
                user_id="user_123"
            )
            
            assert result["request_id"] == "req_123"
            assert result["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_list_available_crews(self):
        """Test listing available crews"""
        service = CrewService()
        
        with patch('app.services.crew_service.list_crews') as mock_list:
            mock_list.return_value = ["crew1", "crew2"]
            
            with patch('app.services.crew_service.get_crew') as mock_get:
                mock_crew_class = Mock()
                mock_crew_class.__name__ = "TestCrew"
                mock_crew_class.__doc__ = "Test crew description"
                mock_get.return_value = mock_crew_class
                
                crews = await service.list_available_crews()
                
                assert len(crews) == 2
                assert crews[0]["type"] == "crew1"
                assert crews[0]["name"] == "TestCrew"
    
    @pytest.mark.asyncio
    async def test_get_autonomous_system_status(self):
        """Test getting autonomous system status"""
        service = CrewService()
        
        with patch('app.services.crew_service.autonomous_manager') as mock_manager:
            mock_manager.collect_performance_data.return_value = {
                "total_workflows": 10,
                "success_rate": 0.8
            }
            mock_manager.resource_manager.resource_pool = {
                "cpu_usage": 0.5,
                "memory_usage": 0.3
            }
            mock_manager.active_workflows = {}
            mock_manager.workflow_history = [1, 2, 3]
            
            status = await service.get_autonomous_system_status()
            
            assert status["system_status"] == "operational"
            assert status["active_workflows"] == 0
            assert status["total_processed"] == 3
            assert "performance_metrics" in status
            assert "resource_utilization" in status


# Integration tests would go here
class TestCrewIntegration:
    """Integration tests for the crew system"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_execution(self):
        """Test full workflow execution (mocked)"""
        # This would be a comprehensive integration test
        # that tests the entire flow from API request to completion
        pass
    
    @pytest.mark.asyncio
    async def test_autonomous_crew_composition(self):
        """Test autonomous crew composition (mocked)"""
        # Test that autonomous crews can be composed and executed
        pass
    
    @pytest.mark.asyncio
    async def test_resource_management_integration(self):
        """Test resource management integration (mocked)"""
        # Test that resource management works across multiple workflows
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])