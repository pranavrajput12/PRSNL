"""
Enhanced AI Router with LangChain ReAct Agent
Intelligent routing based on task content and complexity analysis
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

try:
    from langchain.agents import AgentExecutor, AgentType, initialize_agent
    from langchain.tools import Tool
    from langchain_openai import AzureChatOpenAI
    from langchain.memory import ConversationBufferMemory
    from langchain.schema import AgentAction, AgentFinish
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    AgentExecutor = None
    Tool = None
    initialize_agent = None

from app.config import settings
from app.services.ai_router_types import (
    AIProvider, TaskType, AITask, ProviderConfig, RoutingDecision, TaskComplexity
)

logger = logging.getLogger(__name__)


class EnhancedAIRouter:
    """
    Enhanced AI Router using LangChain ReAct agent for intelligent routing
    
    Features:
    - Content-based complexity analysis
    - Cost-performance optimization
    - Intelligent model selection
    - Reasoning transparency
    - Learning from routing decisions
    """
    
    def __init__(self):
        self.enabled = LANGCHAIN_AVAILABLE and bool(settings.AZURE_OPENAI_API_KEY)
        self.base_router = None  # Will be set via dependency injection
        self.routing_agent = None
        self.routing_history = []
        self.performance_metrics = {}
        
        if self.enabled:
            self._initialize_agent()
        else:
            logger.warning("Enhanced AI Router disabled. Using base router.")
    
    def set_base_router(self, base_router):
        """Set the base router instance to avoid circular imports"""
        self.base_router = base_router
    
    def _initialize_agent(self):
        """Initialize the ReAct agent for routing decisions"""
        try:
            # Initialize LLM for agent
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.1  # Low temperature for consistent routing
            )
            
            # Create tools for the agent
            tools = self._create_routing_tools()
            
            # Create the agent - using initialize_agent which is more compatible with LangChain 0.3.0+
            self.routing_agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True
            )
            
            logger.info("Enhanced AI Router with ReAct agent initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize ReAct agent: {e}")
            self.enabled = False
    
    def _create_routing_tools(self) -> List[Tool]:
        """Create tools for the routing agent"""
        tools = []
        
        # Tool to analyze task complexity
        tools.append(Tool(
            name="analyze_complexity",
            func=self._analyze_task_complexity,
            description="Analyze the complexity of an AI task based on content length, structure, and requirements"
        ))
        
        # Tool to estimate token usage
        tools.append(Tool(
            name="estimate_tokens",
            func=self._estimate_token_usage,
            description="Estimate the number of tokens required for a task"
        ))
        
        # Tool to check provider capabilities
        tools.append(Tool(
            name="check_capabilities",
            func=self._check_provider_capabilities,
            description="Check which providers can handle specific task requirements"
        ))
        
        # Tool to calculate cost estimates
        tools.append(Tool(
            name="calculate_cost",
            func=self._calculate_cost_estimate,
            description="Calculate estimated cost for different provider options"
        ))
        
        # Tool to check provider health
        tools.append(Tool(
            name="check_health",
            func=self._check_provider_health,
            description="Check current health status of providers"
        ))
        
        return tools
    
    async def route_task_enhanced(self, task: AITask) -> RoutingDecision:
        """
        Enhanced routing with ReAct agent reasoning
        
        Args:
            task: The AI task to route
            
        Returns:
            Enhanced routing decision with reasoning
        """
        if not self.enabled:
            # Fallback to base router if available
            if self.base_router:
                provider = await self.base_router.route_task(task)
            else:
                provider = AIProvider.AZURE_OPENAI  # Default fallback
            return RoutingDecision(
                provider=provider,
                complexity=TaskComplexity.MODERATE,
                reasoning="Using base router (enhanced routing not available)",
                confidence=0.7,
                estimated_tokens=1000,
                recommended_model=settings.AZURE_OPENAI_DEPLOYMENT,
                fallback_options=[AIProvider.FALLBACK],
                optimization_notes=[]
            )
        
        try:
            # Prepare task information
            task_info = self._prepare_task_info(task)
            
            # Run the agent - initialize_agent expects a single input string
            result = await asyncio.to_thread(
                self.routing_agent.run,
                task_info
            )
            
            # Parse the agent's decision
            decision = self._parse_agent_decision(result)
            
            # Record the routing decision
            self._record_routing_decision(task, decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"Enhanced routing failed: {e}")
            # Fallback to base router if available
            if self.base_router:
                provider = await self.base_router.route_task(task)
            else:
                provider = AIProvider.AZURE_OPENAI  # Default fallback
            return RoutingDecision(
                provider=provider,
                complexity=TaskComplexity.MODERATE,
                reasoning=f"Enhanced routing failed: {str(e)}",
                confidence=0.5,
                estimated_tokens=1000,
                recommended_model=settings.AZURE_OPENAI_DEPLOYMENT,
                fallback_options=[AIProvider.FALLBACK],
                optimization_notes=["Consider investigating routing failure"]
            )
    
    def _prepare_task_info(self, task: AITask) -> str:
        """Prepare task information for the agent"""
        content_preview = ""
        if isinstance(task.content, str):
            content_preview = task.content[:500] + "..." if len(task.content) > 500 else task.content
        elif isinstance(task.content, list):
            content_preview = f"List with {len(task.content)} items"
        elif isinstance(task.content, dict):
            content_preview = f"Dictionary with keys: {list(task.content.keys())}"
        
        task_info = {
            "task_type": task.type.value,
            "content_preview": content_preview,
            "content_length": len(str(task.content)),
            "priority": task.priority,
            "options": task.options or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Format as a natural language prompt for the agent
        prompt = f"""
Analyze this AI task and recommend the best routing decision:

Task Type: {task_info['task_type']}
Content Length: {task_info['content_length']} characters
Priority: {task_info['priority']}
Content Preview: {task_info['content_preview']}
Options: {task_info['options']}

Available Providers:
- AZURE_OPENAI: Premium provider with GPT-4, supports all features, higher cost
- FALLBACK: Basic provider, limited features, free

Please analyze the task complexity and recommend the best provider. Consider:
1. Task complexity (simple/moderate/complex/expert)
2. Cost vs performance trade-offs
3. Provider capabilities
4. Estimated token usage

Provide your recommendation in a clear, structured format.
"""
        return prompt.strip()
    
    def _parse_agent_decision(self, agent_output: str) -> RoutingDecision:
        """Parse the agent's routing decision"""
        try:
            # Extract JSON from agent output
            import re
            json_match = re.search(r'\{[^{}]*\}', agent_output, re.DOTALL)
            if json_match:
                decision_data = json.loads(json_match.group())
            else:
                # Try to parse the entire output as JSON
                decision_data = json.loads(agent_output)
            
            # Map provider string to enum
            provider_map = {
                "AZURE_OPENAI": AIProvider.AZURE_OPENAI,
                "FALLBACK": AIProvider.FALLBACK
            }
            provider = provider_map.get(
                decision_data.get("provider", "AZURE_OPENAI"),
                AIProvider.AZURE_OPENAI
            )
            
            # Map complexity string to enum
            complexity_map = {
                "simple": TaskComplexity.SIMPLE,
                "moderate": TaskComplexity.MODERATE,
                "complex": TaskComplexity.COMPLEX,
                "expert": TaskComplexity.EXPERT
            }
            complexity = complexity_map.get(
                decision_data.get("complexity", "moderate"),
                TaskComplexity.MODERATE
            )
            
            return RoutingDecision(
                provider=provider,
                complexity=complexity,
                reasoning=decision_data.get("reasoning", "No reasoning provided"),
                confidence=float(decision_data.get("confidence", 0.8)),
                estimated_tokens=int(decision_data.get("estimated_tokens", 1000)),
                recommended_model=decision_data.get("recommended_model", settings.AZURE_OPENAI_DEPLOYMENT),
                fallback_options=[AIProvider.FALLBACK],
                optimization_notes=decision_data.get("optimization_notes", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse agent decision: {e}")
            # Return a default decision
            return RoutingDecision(
                provider=AIProvider.AZURE_OPENAI,
                complexity=TaskComplexity.MODERATE,
                reasoning="Failed to parse agent decision, using default",
                confidence=0.5,
                estimated_tokens=1000,
                recommended_model=settings.AZURE_OPENAI_DEPLOYMENT,
                fallback_options=[AIProvider.FALLBACK],
                optimization_notes=["Agent decision parsing failed"]
            )
    
    # Tool implementations
    def _analyze_task_complexity(self, task_info: str) -> str:
        """Analyze task complexity based on various factors"""
        try:
            info = json.loads(task_info)
            content_length = info.get("content_length", 0)
            task_type = info.get("task_type", "")
            
            # Simple heuristics for complexity
            if content_length < 500 and task_type in ["text_generation", "embedding"]:
                complexity = "simple"
                score = 0.2
            elif content_length < 2000:
                complexity = "moderate"
                score = 0.5
            elif content_length < 5000 or task_type == "vision":
                complexity = "complex"
                score = 0.8
            else:
                complexity = "expert"
                score = 1.0
            
            return json.dumps({
                "complexity": complexity,
                "score": score,
                "factors": {
                    "content_length": content_length,
                    "task_type": task_type,
                    "requires_reasoning": task_type in ["text_generation", "vision"],
                    "requires_context": content_length > 1000
                }
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "complexity": "moderate", "score": 0.5})
    
    def _estimate_token_usage(self, task_info: str) -> str:
        """Estimate token usage for the task"""
        try:
            info = json.loads(task_info)
            content_length = info.get("content_length", 0)
            
            # Rough estimation: ~4 characters per token
            estimated_tokens = content_length // 4
            
            # Add overhead for system prompts and responses
            overhead = 200
            response_tokens = 500  # Estimated response size
            
            total_tokens = estimated_tokens + overhead + response_tokens
            
            return json.dumps({
                "input_tokens": estimated_tokens,
                "overhead_tokens": overhead,
                "response_tokens": response_tokens,
                "total_tokens": total_tokens,
                "requires_chunking": total_tokens > 4000
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "total_tokens": 1000})
    
    def _check_provider_capabilities(self, requirements: str) -> str:
        """Check which providers meet the requirements"""
        try:
            reqs = json.loads(requirements)
            
            capabilities = {
                "AZURE_OPENAI": {
                    "supports_streaming": True,
                    "supports_vision": True,
                    "supports_embeddings": True,
                    "supports_functions": True,
                    "max_tokens": 8192,
                    "quality": "high",
                    "speed": "moderate"
                },
                "FALLBACK": {
                    "supports_streaming": False,
                    "supports_vision": False,
                    "supports_embeddings": False,
                    "supports_functions": False,
                    "max_tokens": 1000,
                    "quality": "basic",
                    "speed": "fast"
                }
            }
            
            suitable_providers = []
            for provider, caps in capabilities.items():
                suitable = True
                for req_key, req_value in reqs.items():
                    if req_key in caps and caps[req_key] != req_value:
                        suitable = False
                        break
                
                if suitable:
                    suitable_providers.append({
                        "provider": provider,
                        "capabilities": caps
                    })
            
            return json.dumps({
                "suitable_providers": suitable_providers,
                "recommendation": suitable_providers[0]["provider"] if suitable_providers else "AZURE_OPENAI"
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "suitable_providers": ["AZURE_OPENAI"]})
    
    def _calculate_cost_estimate(self, provider_tokens: str) -> str:
        """Calculate cost estimates for different providers"""
        try:
            data = json.loads(provider_tokens)
            provider = data.get("provider", "AZURE_OPENAI")
            tokens = data.get("tokens", 1000)
            
            # Cost per 1k tokens (example rates)
            costs = {
                "AZURE_OPENAI": 0.03,  # GPT-4 rate
                "FALLBACK": 0.0        # Free
            }
            
            cost = (tokens / 1000) * costs.get(provider, 0.03)
            
            return json.dumps({
                "provider": provider,
                "tokens": tokens,
                "cost_usd": round(cost, 4),
                "cost_per_1k_tokens": costs.get(provider, 0.03)
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "cost_usd": 0.03})
    
    def _check_provider_health(self, provider_name: str) -> str:
        """Check provider health status"""
        try:
            provider_enum = AIProvider[provider_name]
            
            # Check if base router is available
            if self.base_router is None:
                return json.dumps({
                    "provider": provider_name,
                    "healthy": True,
                    "total_requests": 0,
                    "total_errors": 0,
                    "error_rate": 0,
                    "recommendation": "use",
                    "note": "Base router not available"
                })
            
            health = self.base_router.provider_health.get(provider_enum, False)
            stats = self.base_router.usage_stats.get(provider_enum, {})
            
            error_rate = 0
            if stats.get("requests", 0) > 0:
                error_rate = stats.get("errors", 0) / stats["requests"]
            
            return json.dumps({
                "provider": provider_name,
                "healthy": health,
                "total_requests": stats.get("requests", 0),
                "total_errors": stats.get("errors", 0),
                "error_rate": round(error_rate, 3),
                "recommendation": "use" if health and error_rate < 0.1 else "avoid"
            })
            
        except Exception as e:
            return json.dumps({"error": str(e), "healthy": True, "recommendation": "use"})
    
    def _record_routing_decision(self, task: AITask, decision: RoutingDecision):
        """Record routing decision for learning"""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_type": task.type.value,
            "task_priority": task.priority,
            "content_size": len(str(task.content)),
            "provider": decision.provider.value,
            "complexity": decision.complexity.value,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning
        }
        
        self.routing_history.append(record)
        
        # Keep only recent history
        if len(self.routing_history) > 1000:
            self.routing_history = self.routing_history[-1000:]
    
    async def get_routing_insights(self) -> Dict[str, Any]:
        """Get insights from routing history"""
        if not self.routing_history:
            return {"message": "No routing history available"}
        
        # Analyze routing patterns
        provider_distribution = {}
        complexity_distribution = {}
        avg_confidence = 0
        
        for record in self.routing_history:
            provider = record["provider"]
            complexity = record["complexity"]
            
            provider_distribution[provider] = provider_distribution.get(provider, 0) + 1
            complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
            avg_confidence += record["confidence"]
        
        avg_confidence /= len(self.routing_history)
        
        return {
            "total_routings": len(self.routing_history),
            "provider_distribution": provider_distribution,
            "complexity_distribution": complexity_distribution,
            "average_confidence": round(avg_confidence, 3),
            "recent_decisions": self.routing_history[-10:],
            "recommendations": self._generate_routing_recommendations()
        }
    
    def _generate_routing_recommendations(self) -> List[str]:
        """Generate recommendations based on routing patterns"""
        recommendations = []
        
        if not self.routing_history:
            return ["Insufficient data for recommendations"]
        
        # Analyze recent errors
        recent_errors = sum(1 for r in self.routing_history[-100:] if r["confidence"] < 0.5)
        if recent_errors > 10:
            recommendations.append("High number of low-confidence routings detected. Consider reviewing task preprocessing.")
        
        # Analyze provider usage
        azure_usage = sum(1 for r in self.routing_history[-100:] if r["provider"] == "AZURE_OPENAI")
        if azure_usage > 90:
            recommendations.append("Heavy Azure OpenAI usage. Consider implementing caching for repeated queries.")
        
        # Analyze complexity patterns
        expert_tasks = sum(1 for r in self.routing_history[-100:] if r["complexity"] == "expert")
        if expert_tasks > 30:
            recommendations.append("Many expert-level tasks. Consider breaking down complex tasks into smaller subtasks.")
        
        return recommendations if recommendations else ["Routing patterns appear optimal"]
    
    async def execute_with_enhanced_routing(self, task: AITask, execute_fn) -> Any:
        """Execute task with enhanced routing and fallback"""
        # Get enhanced routing decision
        decision = await self.route_task_enhanced(task)
        
        logger.info(f"Enhanced routing decision: {decision.provider.value} "
                   f"(complexity: {decision.complexity.value}, confidence: {decision.confidence})")
        logger.info(f"Reasoning: {decision.reasoning}")
        
        # Add routing metadata to task options
        if not task.options:
            task.options = {}
        task.options["routing_decision"] = {
            "complexity": decision.complexity.value,
            "estimated_tokens": decision.estimated_tokens,
            "recommended_model": decision.recommended_model
        }
        
        # Execute with the selected provider
        providers = [decision.provider] + decision.fallback_options
        
        last_error = None
        for provider in providers:
            try:
                start_time = time.time()
                result = await execute_fn(provider, task)
                
                # Update success metrics
                self._update_performance_metrics(
                    provider, 
                    decision.complexity,
                    success=True,
                    response_time=time.time() - start_time
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Provider {provider.value} failed: {e}")
                last_error = e
                
                # Update failure metrics
                self._update_performance_metrics(
                    provider,
                    decision.complexity,
                    success=False
                )
        
        # All providers failed
        raise last_error or Exception("All providers failed")
    
    def _update_performance_metrics(
        self, 
        provider: AIProvider,
        complexity: TaskComplexity,
        success: bool,
        response_time: float = 0
    ):
        """Update performance metrics for learning"""
        key = f"{provider.value}_{complexity.value}"
        
        if key not in self.performance_metrics:
            self.performance_metrics[key] = {
                "successes": 0,
                "failures": 0,
                "total_response_time": 0,
                "avg_response_time": 0
            }
        
        metrics = self.performance_metrics[key]
        
        if success:
            metrics["successes"] += 1
            metrics["total_response_time"] += response_time
            metrics["avg_response_time"] = (
                metrics["total_response_time"] / 
                (metrics["successes"] + metrics["failures"])
            )
        else:
            metrics["failures"] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        report = {
            "routing_insights": asyncio.run(self.get_routing_insights()),
            "performance_by_complexity": {},
            "provider_reliability": {},
            "optimization_opportunities": []
        }
        
        # Aggregate performance by complexity
        for key, metrics in self.performance_metrics.items():
            provider, complexity = key.split("_")
            
            if complexity not in report["performance_by_complexity"]:
                report["performance_by_complexity"][complexity] = {}
            
            total = metrics["successes"] + metrics["failures"]
            success_rate = metrics["successes"] / total if total > 0 else 0
            
            report["performance_by_complexity"][complexity][provider] = {
                "success_rate": round(success_rate, 3),
                "avg_response_time": round(metrics["avg_response_time"], 2),
                "total_requests": total
            }
        
        # Calculate provider reliability
        for provider in AIProvider:
            total_successes = 0
            total_requests = 0
            
            for key, metrics in self.performance_metrics.items():
                if key.startswith(provider.value):
                    total_successes += metrics["successes"]
                    total_requests += metrics["successes"] + metrics["failures"]
            
            if total_requests > 0:
                report["provider_reliability"][provider.value] = round(
                    total_successes / total_requests, 3
                )
        
        # Generate optimization opportunities
        report["optimization_opportunities"] = self._identify_optimizations()
        
        return report
    
    def _identify_optimizations(self) -> List[str]:
        """Identify optimization opportunities from metrics"""
        optimizations = []
        
        # Check for complexity mismatches
        for key, metrics in self.performance_metrics.items():
            provider, complexity = key.split("_")
            total = metrics["successes"] + metrics["failures"]
            
            if total > 10:
                success_rate = metrics["successes"] / total
                
                # Azure OpenAI for simple tasks
                if provider == "AZURE_OPENAI" and complexity == "simple" and success_rate > 0.9:
                    optimizations.append(
                        f"Consider using cheaper providers for simple tasks "
                        f"(currently {total} simple tasks sent to Azure OpenAI)"
                    )
                
                # Fallback struggling with complex tasks
                if provider == "FALLBACK" and complexity in ["complex", "expert"] and success_rate < 0.5:
                    optimizations.append(
                        f"Fallback provider struggling with {complexity} tasks "
                        f"(success rate: {success_rate:.1%})"
                    )
        
        return optimizations if optimizations else ["No significant optimizations identified"]


# Singleton instance
enhanced_ai_router = EnhancedAIRouter()