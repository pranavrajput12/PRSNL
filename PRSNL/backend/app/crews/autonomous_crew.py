"""
Autonomous Crew System - Dynamic Agent Orchestration

This is the core system that enables autonomous agent workflows,
dynamic crew composition, and self-directed task execution.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Type, Union
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task
from enum import Enum

from app.crews.base_crew import PRSNLBaseCrew
from app.crews import register_crew, CREW_REGISTRY
from app.agents import AGENT_REGISTRY
from app.core.config import settings

logger = logging.getLogger(__name__)


class AutonomousMode(Enum):
    """Autonomous operation modes"""
    REACTIVE = "reactive"  # React to user inputs
    PROACTIVE = "proactive"  # Self-initiated workflows
    HYBRID = "hybrid"  # Both reactive and proactive
    SCHEDULED = "scheduled"  # Time-based execution


class WorkflowPriority(Enum):
    """Workflow priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@register_crew("autonomous_orchestrator")
class AutonomousOrchestratorCrew(PRSNLBaseCrew):
    """
    Master orchestrator for autonomous agent operations
    
    This crew manages the entire autonomous system, making decisions
    about which crews to activate, when to execute workflows, and
    how to coordinate between different agent systems.
    """
    
    def __init__(self, mode: AutonomousMode = AutonomousMode.HYBRID, **kwargs):
        super().__init__(**kwargs)
        self.mode = mode
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_queue: List[Dict[str, Any]] = []
        self.resource_manager = AutonomousResourceManager()
        
    @agent
    def orchestrator_agent(self) -> Agent:
        """Master orchestrator agent"""
        return Agent(
            role="Autonomous System Orchestrator",
            goal=(
                "Orchestrate autonomous agent workflows, optimize resource "
                "allocation, and ensure efficient execution of complex tasks"
            ),
            backstory=(
                "You are the master orchestrator of an autonomous agent system. "
                "Your responsibility is to coordinate multiple specialized crews, "
                "manage resources efficiently, and ensure that complex workflows "
                "are executed optimally. You have deep understanding of agent "
                "capabilities, system constraints, and optimization strategies."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=True,
            memory=True
        )
    
    @agent
    def workflow_planner(self) -> Agent:
        """Workflow planning and optimization agent"""
        return Agent(
            role="Workflow Planner",
            goal="Plan and optimize autonomous workflows for maximum efficiency",
            backstory=(
                "You are a workflow optimization expert who specializes in "
                "breaking down complex tasks into efficient agent workflows. "
                "Your expertise lies in understanding task dependencies, "
                "resource requirements, and optimal execution strategies."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=True,
            memory=True
        )
    
    @agent
    def resource_manager(self) -> Agent:
        """Resource management and allocation agent"""
        return Agent(
            role="Resource Manager",
            goal="Manage and allocate system resources for optimal performance",
            backstory=(
                "You are a resource management specialist who ensures optimal "
                "allocation of computational resources, agent availability, "
                "and system performance. Your role is critical for maintaining "
                "efficient autonomous operations."
            ),
            tools=[],
            llm=self.get_llm_config(),
            verbose=True,
            memory=True
        )
    
    @task
    def analyze_request_task(self) -> Task:
        """Task for analyzing incoming requests and determining optimal approach"""
        return Task(
            description=(
                "Analyze the incoming request to determine the optimal "
                "autonomous approach. Consider task complexity, required "
                "capabilities, resource availability, and execution strategy. "
                "Request details: {request_details}"
            ),
            expected_output=(
                "Request analysis including:\n"
                "1. Task complexity assessment\n"
                "2. Required agent capabilities\n"
                "3. Resource requirements\n"
                "4. Recommended execution strategy\n"
                "5. Risk assessment and mitigation\n"
                "6. Success criteria and metrics\n"
                "7. Proposed crew composition\n"
                "8. Estimated timeline and milestones"
            ),
            agent=self.orchestrator_agent()
        )
    
    @task
    def plan_workflow_task(self) -> Task:
        """Task for planning detailed workflow execution"""
        return Task(
            description=(
                "Plan detailed workflow execution based on request analysis. "
                "Create step-by-step execution plan with proper task "
                "dependencies and resource allocation."
            ),
            expected_output=(
                "Workflow execution plan including:\n"
                "1. Step-by-step task breakdown\n"
                "2. Agent assignment and responsibilities\n"
                "3. Task dependencies and sequencing\n"
                "4. Resource allocation and scheduling\n"
                "5. Checkpoint and validation points\n"
                "6. Error handling and recovery strategies\n"
                "7. Performance monitoring and optimization\n"
                "8. Final deliverables and success metrics"
            ),
            agent=self.workflow_planner()
        )
    
    @task
    def manage_resources_task(self) -> Task:
        """Task for managing resources during workflow execution"""
        return Task(
            description=(
                "Manage system resources during workflow execution. "
                "Monitor resource usage, optimize allocation, and ensure "
                "efficient operation of all autonomous workflows."
            ),
            expected_output=(
                "Resource management report including:\n"
                "1. Current resource utilization\n"
                "2. Resource allocation optimization\n"
                "3. Performance bottleneck identification\n"
                "4. Scaling recommendations\n"
                "5. Resource conflict resolution\n"
                "6. Efficiency metrics and improvements\n"
                "7. Capacity planning recommendations"
            ),
            agent=self.resource_manager()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Autonomous Orchestrator crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm=self.get_llm_config(),
            verbose=True,
            memory=True,
            embedder={
                "provider": "azure_openai",
                "config": {
                    "model": settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                    "api_key": settings.AZURE_OPENAI_API_KEY,
                    "api_base": settings.AZURE_OPENAI_ENDPOINT,
                    "api_version": settings.AZURE_OPENAI_API_VERSION
                }
            }
        )
    
    async def execute_autonomous_workflow(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute autonomous workflow based on request"""
        workflow_id = f"autonomous_{request.get('id', 'unknown')}"
        
        try:
            # Analyze request
            analysis_result = await self.analyze_request(request)
            
            # Plan workflow
            workflow_plan = await self.plan_workflow(analysis_result)
            
            # Execute workflow
            execution_result = await self.execute_workflow(workflow_plan)
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "analysis": analysis_result,
                "plan": workflow_plan,
                "result": execution_result
            }
            
        except Exception as e:
            logger.error(f"Autonomous workflow execution failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def analyze_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze incoming request for autonomous processing"""
        # Implementation would analyze request complexity, 
        # determine required capabilities, and recommend approach
        return {
            "complexity": "medium",
            "required_crews": ["knowledge_curation", "code_analysis"],
            "estimated_duration": "15_minutes",
            "resource_requirements": "medium"
        }
    
    async def plan_workflow(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Plan workflow execution based on analysis"""
        # Implementation would create detailed execution plan
        return {
            "steps": [
                {"crew": "knowledge_curation", "task": "curate_knowledge"},
                {"crew": "code_analysis", "task": "analyze_code"}
            ],
            "dependencies": [],
            "resource_allocation": {"cpu": 0.8, "memory": 0.6}
        }
    
    async def execute_workflow(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the planned workflow"""
        # Implementation would execute the planned workflow
        return {"status": "completed", "output": "Workflow executed successfully"}


class AutonomousResourceManager:
    """Manages resources for autonomous operations"""
    
    def __init__(self):
        self.resource_pool = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "active_agents": 0,
            "concurrent_crews": 0
        }
        self.resource_limits = {
            "max_cpu": 0.8,
            "max_memory": 0.8,
            "max_agents": 10,
            "max_crews": 5
        }
    
    def check_resource_availability(self, requirements: Dict[str, Any]) -> bool:
        """Check if resources are available for new workflow"""
        cpu_needed = requirements.get("cpu", 0.1)
        memory_needed = requirements.get("memory", 0.1)
        
        return (
            self.resource_pool["cpu_usage"] + cpu_needed <= self.resource_limits["max_cpu"] and
            self.resource_pool["memory_usage"] + memory_needed <= self.resource_limits["max_memory"]
        )
    
    def allocate_resources(self, workflow_id: str, requirements: Dict[str, Any]) -> bool:
        """Allocate resources for a workflow"""
        if self.check_resource_availability(requirements):
            self.resource_pool["cpu_usage"] += requirements.get("cpu", 0.1)
            self.resource_pool["memory_usage"] += requirements.get("memory", 0.1)
            self.resource_pool["active_agents"] += requirements.get("agents", 1)
            return True
        return False
    
    def release_resources(self, workflow_id: str, requirements: Dict[str, Any]) -> None:
        """Release resources after workflow completion"""
        self.resource_pool["cpu_usage"] -= requirements.get("cpu", 0.1)
        self.resource_pool["memory_usage"] -= requirements.get("memory", 0.1)
        self.resource_pool["active_agents"] -= requirements.get("agents", 1)
        
        # Ensure we don't go below zero
        self.resource_pool["cpu_usage"] = max(0, self.resource_pool["cpu_usage"])
        self.resource_pool["memory_usage"] = max(0, self.resource_pool["memory_usage"])
        self.resource_pool["active_agents"] = max(0, self.resource_pool["active_agents"])


@register_crew("dynamic_crew_composer")
class DynamicCrewComposerCrew(PRSNLBaseCrew):
    """
    Dynamic crew composition system
    
    This crew dynamically composes new crews based on task requirements,
    combining agents from different domains to solve complex problems.
    """
    
    @agent
    def crew_composer(self) -> Agent:
        """Dynamic crew composition agent"""
        return Agent(
            role="Dynamic Crew Composer",
            goal="Dynamically compose optimal crew configurations for complex tasks",
            backstory=(
                "You are a crew composition expert who specializes in creating "
                "optimal team configurations for complex tasks. Your expertise "
                "lies in understanding agent capabilities, task requirements, "
                "and team dynamics to create highly effective crews."
            ),
            tools=[],
            llm=self.get_llm_config()
        )
    
    @agent
    def capability_matcher(self) -> Agent:
        """Agent capability matching specialist"""
        return Agent(
            role="Capability Matcher",
            goal="Match agent capabilities to task requirements optimally",
            backstory=(
                "You are a capability matching specialist who excels at "
                "analyzing task requirements and matching them to available "
                "agent capabilities. Your role is crucial for ensuring "
                "optimal crew composition."
            ),
            tools=[],
            llm=self.get_llm_config()
        )
    
    @task
    def analyze_task_requirements_task(self) -> Task:
        """Task for analyzing task requirements for crew composition"""
        return Task(
            description=(
                "Analyze task requirements to determine optimal crew composition. "
                "Consider task complexity, domain expertise needed, and "
                "collaboration requirements. Task details: {task_details}"
            ),
            expected_output=(
                "Task analysis for crew composition including:\n"
                "1. Required expertise domains\n"
                "2. Skill level requirements\n"
                "3. Collaboration patterns needed\n"
                "4. Resource and tool requirements\n"
                "5. Communication and coordination needs\n"
                "6. Success criteria and metrics\n"
                "7. Recommended crew size and structure"
            ),
            agent=self.capability_matcher()
        )
    
    @task
    def compose_crew_task(self) -> Task:
        """Task for composing optimal crew configuration"""
        return Task(
            description=(
                "Compose optimal crew configuration based on task analysis. "
                "Select agents, define roles, and establish collaboration patterns."
            ),
            expected_output=(
                "Crew composition including:\n"
                "1. Selected agents with role assignments\n"
                "2. Crew hierarchy and communication structure\n"
                "3. Task distribution and responsibilities\n"
                "4. Collaboration workflows and patterns\n"
                "5. Resource allocation and sharing\n"
                "6. Performance monitoring and optimization\n"
                "7. Quality assurance and validation processes"
            ),
            agent=self.crew_composer()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Dynamic Crew Composer crew"""
        return Crew(
            agents=[self.crew_composer(), self.capability_matcher()],
            tasks=[self.analyze_task_requirements_task(), self.compose_crew_task()],
            process=Process.sequential,
            verbose=True,
            memory=True
        )
    
    def compose_dynamic_crew(self, task_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Compose a dynamic crew based on task requirements"""
        # Analyze available agents
        available_agents = self.get_available_agents()
        
        # Match capabilities to requirements
        matched_agents = self.match_capabilities(task_requirements, available_agents)
        
        # Create crew configuration
        crew_config = self.create_crew_config(matched_agents, task_requirements)
        
        return crew_config
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents with their capabilities"""
        agents = []
        for agent_type, agent_class in AGENT_REGISTRY.items():
            agents.append({
                "type": agent_type,
                "class": agent_class,
                "capabilities": getattr(agent_class, "capabilities", []),
                "specializations": getattr(agent_class, "specializations", [])
            })
        return agents
    
    def match_capabilities(self, requirements: Dict[str, Any], agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Match agent capabilities to task requirements"""
        matched = []
        required_capabilities = requirements.get("capabilities", [])
        
        for agent in agents:
            agent_capabilities = agent.get("capabilities", [])
            match_score = len(set(required_capabilities) & set(agent_capabilities))
            
            if match_score > 0:
                matched.append({
                    **agent,
                    "match_score": match_score
                })
        
        # Sort by match score
        matched.sort(key=lambda x: x["match_score"], reverse=True)
        return matched
    
    def create_crew_config(self, agents: List[Dict[str, Any]], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create crew configuration from matched agents"""
        crew_size = min(len(agents), requirements.get("max_crew_size", 5))
        selected_agents = agents[:crew_size]
        
        return {
            "crew_id": f"dynamic_{requirements.get('task_id', 'unknown')}",
            "agents": selected_agents,
            "process": requirements.get("process", "sequential"),
            "collaboration_mode": requirements.get("collaboration_mode", "coordinated"),
            "resource_allocation": self.calculate_resource_allocation(selected_agents),
            "estimated_duration": self.estimate_duration(selected_agents, requirements)
        }
    
    def calculate_resource_allocation(self, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate resource allocation for the crew"""
        return {
            "cpu_per_agent": 0.1,
            "memory_per_agent": 0.1,
            "total_cpu": len(agents) * 0.1,
            "total_memory": len(agents) * 0.1
        }
    
    def estimate_duration(self, agents: List[Dict[str, Any]], requirements: Dict[str, Any]) -> str:
        """Estimate crew execution duration"""
        base_time = 10  # minutes
        complexity_factor = requirements.get("complexity", 1.0)
        agent_factor = len(agents) * 0.8  # More agents can be faster but with coordination overhead
        
        estimated_minutes = base_time * complexity_factor * agent_factor
        return f"{int(estimated_minutes)}_minutes"


@register_crew("self_improving_crew")
class SelfImprovingCrew(PRSNLBaseCrew):
    """
    Self-improving autonomous crew
    
    This crew learns from its own performance and continuously
    improves its capabilities and decision-making.
    """
    
    @agent
    def performance_analyzer(self) -> Agent:
        """Performance analysis agent"""
        return Agent(
            role="Performance Analyzer",
            goal="Analyze crew performance and identify improvement opportunities",
            backstory=(
                "You are a performance analysis expert who specializes in "
                "evaluating autonomous system performance and identifying "
                "areas for improvement. Your insights drive continuous "
                "enhancement of autonomous capabilities."
            ),
            tools=[],
            llm=self.get_llm_config()
        )
    
    @agent
    def learning_optimizer(self) -> Agent:
        """Learning and optimization agent"""
        return Agent(
            role="Learning Optimizer",
            goal="Optimize system learning and implement performance improvements",
            backstory=(
                "You are a learning optimization specialist who focuses on "
                "implementing performance improvements and optimizing "
                "autonomous system learning capabilities."
            ),
            tools=[],
            llm=self.get_llm_config()
        )
    
    @task
    def analyze_performance_task(self) -> Task:
        """Task for analyzing system performance"""
        return Task(
            description=(
                "Analyze autonomous system performance across all workflows. "
                "Identify patterns, bottlenecks, and improvement opportunities. "
                "Performance data: {performance_data}"
            ),
            expected_output=(
                "Performance analysis including:\n"
                "1. Overall system performance metrics\n"
                "2. Workflow efficiency analysis\n"
                "3. Resource utilization patterns\n"
                "4. Bottleneck identification\n"
                "5. Success rate and quality metrics\n"
                "6. Error patterns and failure analysis\n"
                "7. Improvement recommendations\n"
                "8. Optimization strategies"
            ),
            agent=self.performance_analyzer()
        )
    
    @task
    def optimize_learning_task(self) -> Task:
        """Task for optimizing learning and performance"""
        return Task(
            description=(
                "Optimize system learning based on performance analysis. "
                "Implement improvements and enhance autonomous capabilities."
            ),
            expected_output=(
                "Learning optimization including:\n"
                "1. Learning algorithm improvements\n"
                "2. Knowledge base enhancements\n"
                "3. Decision-making optimizations\n"
                "4. Workflow efficiency improvements\n"
                "5. Resource allocation optimizations\n"
                "6. Error reduction strategies\n"
                "7. Performance monitoring enhancements\n"
                "8. Continuous improvement framework"
            ),
            agent=self.learning_optimizer()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Self-Improving crew"""
        return Crew(
            agents=[self.performance_analyzer(), self.learning_optimizer()],
            tasks=[self.analyze_performance_task(), self.optimize_learning_task()],
            process=Process.sequential,
            verbose=True,
            memory=True
        )


class AutonomousWorkflowManager:
    """
    Central manager for autonomous workflows
    
    This class coordinates all autonomous operations and provides
    the main interface for autonomous system management.
    """
    
    def __init__(self):
        self.orchestrator = AutonomousOrchestratorCrew()
        self.composer = DynamicCrewComposerCrew()
        self.improver = SelfImprovingCrew()
        self.resource_manager = AutonomousResourceManager()
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming request through autonomous system"""
        request_id = request.get("id", f"req_{len(self.workflow_history)}")
        
        # Check resource availability
        if not self.resource_manager.check_resource_availability(request.get("resources", {})):
            return {
                "request_id": request_id,
                "status": "rejected",
                "reason": "insufficient_resources"
            }
        
        # Analyze request and plan workflow
        workflow_plan = await self.orchestrator.execute_autonomous_workflow(request)
        
        # Execute workflow
        if workflow_plan["status"] == "completed":
            result = await self.execute_workflow(workflow_plan)
            self.workflow_history.append({
                "request_id": request_id,
                "plan": workflow_plan,
                "result": result,
                "timestamp": asyncio.get_event_loop().time()
            })
            return result
        else:
            return workflow_plan
    
    async def execute_workflow(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planned workflow"""
        workflow_id = plan.get("workflow_id")
        
        try:
            # Dynamic crew composition if needed
            if plan.get("requires_dynamic_crew", False):
                crew_config = self.composer.compose_dynamic_crew(plan.get("requirements", {}))
                plan["crew_config"] = crew_config
            
            # Execute workflow steps
            results = []
            for step in plan.get("plan", {}).get("steps", []):
                step_result = await self.execute_step(step, plan)
                results.append(step_result)
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def execute_step(self, step: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual workflow step"""
        crew_type = step.get("crew")
        task_type = step.get("task")
        
        if crew_type in CREW_REGISTRY:
            crew_class = CREW_REGISTRY[crew_type]
            crew_instance = crew_class()
            
            # Execute crew task
            result = await crew_instance.execute_task(task_type, step.get("inputs", {}))
            
            return {
                "step": step,
                "status": "completed",
                "result": result
            }
        else:
            return {
                "step": step,
                "status": "failed",
                "error": f"Unknown crew type: {crew_type}"
            }
    
    async def optimize_system(self) -> Dict[str, Any]:
        """Run system optimization and improvement"""
        performance_data = self.collect_performance_data()
        
        optimization_result = await self.improver.crew().kickoff({
            "performance_data": performance_data
        })
        
        return {
            "optimization_status": "completed",
            "improvements": optimization_result
        }
    
    def collect_performance_data(self) -> Dict[str, Any]:
        """Collect system performance data"""
        return {
            "total_workflows": len(self.workflow_history),
            "success_rate": self.calculate_success_rate(),
            "average_duration": self.calculate_average_duration(),
            "resource_utilization": self.resource_manager.resource_pool,
            "common_failures": self.analyze_common_failures()
        }
    
    def calculate_success_rate(self) -> float:
        """Calculate workflow success rate"""
        if not self.workflow_history:
            return 0.0
        
        successful = sum(1 for w in self.workflow_history if w["result"]["status"] == "completed")
        return successful / len(self.workflow_history)
    
    def calculate_average_duration(self) -> float:
        """Calculate average workflow duration"""
        if not self.workflow_history:
            return 0.0
        
        durations = [w.get("duration", 0) for w in self.workflow_history]
        return sum(durations) / len(durations)
    
    def analyze_common_failures(self) -> List[Dict[str, Any]]:
        """Analyze common failure patterns"""
        failures = [w for w in self.workflow_history if w["result"]["status"] == "failed"]
        
        # Group by error type
        error_counts = {}
        for failure in failures:
            error = failure["result"].get("error", "unknown")
            error_counts[error] = error_counts.get(error, 0) + 1
        
        return [
            {"error": error, "count": count}
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        ]


# Global autonomous workflow manager instance
autonomous_manager = AutonomousWorkflowManager()