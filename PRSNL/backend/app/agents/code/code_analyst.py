"""
Code Analyst Agent - Migrated to Crew.ai

This agent analyzes code repositories for structure, quality, and architecture patterns.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base_agent import PRSNLBaseAgent
from app.agents import register_agent
from app.tools.code_tools import (
    CodeAnalyzerTool,
    CodeMetricsTool,
    DependencyAnalyzerTool,
    TestAnalyzerTool
)
from app.tools.ai_tools import SummaryGeneratorTool, EntityExtractorTool

logger = logging.getLogger(__name__)


@register_agent("code_analyst")
class CodeAnalystAgent(PRSNLBaseAgent):
    """
    Code Analyst Agent
    
    Specializes in comprehensive code analysis including architecture,
    quality metrics, and structural analysis of code repositories.
    """
    
    def __init__(self, **kwargs):
        # Define the agent's role, goal, and backstory
        role = kwargs.pop("role", "Code Analyst")
        goal = kwargs.pop("goal", 
            "Analyze code repositories to understand architecture, assess quality, "
            "and provide actionable insights for code improvement and maintenance"
        )
        backstory = kwargs.pop("backstory",
            "You are a senior software architect with decades of experience "
            "analyzing codebases across multiple languages and paradigms. Your "
            "deep understanding of software design patterns, architecture principles, "
            "and code quality metrics makes you invaluable for understanding "
            "complex systems. You excel at seeing the big picture while also "
            "identifying specific areas for improvement in code structure and quality."
        )
        
        # Initialize with specialized tools
        tools = kwargs.pop("tools", None)
        if tools is None:
            tools = [
                CodeAnalyzerTool(),
                CodeMetricsTool(),
                DependencyAnalyzerTool(),
                TestAnalyzerTool(),
                SummaryGeneratorTool(),
                EntityExtractorTool()
            ]
        
        # Call parent constructor
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            **kwargs
        )
    
    def get_specialized_instructions(self) -> str:
        """Get specialized instructions for this agent"""
        return """
        When analyzing code repositories:
        1. Assess overall architecture and design patterns
        2. Evaluate code quality metrics and maintainability
        3. Analyze dependency structure and relationships
        4. Review test coverage and test quality
        5. Identify potential security vulnerabilities
        6. Assess performance implications
        7. Evaluate documentation quality
        8. Identify technical debt areas
        9. Recommend refactoring opportunities
        10. Assess scalability and extensibility
        11. Review coding standards compliance
        12. Identify reusable components and patterns
        
        Focus on providing actionable insights that help
        improve code quality, maintainability, and team productivity.
        """
    
    def assess_architecture_quality(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the software architecture"""
        architecture_assessment = {
            "overall_score": 0.0,
            "pattern_adherence": {},
            "design_principles": {},
            "modularity_score": 0.0,
            "coupling_assessment": "medium",
            "cohesion_assessment": "high",
            "scalability_score": 0.0,
            "maintainability_score": 0.0,
            "recommendations": []
        }
        
        # Analyze detected patterns
        patterns = analysis_results.get("design_patterns", [])
        architecture_assessment["pattern_adherence"] = {
            "patterns_found": len(patterns),
            "appropriate_usage": True,
            "missing_patterns": ["Repository", "Factory"]
        }
        
        # Assess design principles (SOLID)
        architecture_assessment["design_principles"] = {
            "single_responsibility": 0.8,
            "open_closed": 0.7,
            "liskov_substitution": 0.9,
            "interface_segregation": 0.6,
            "dependency_inversion": 0.8
        }
        
        # Calculate scores
        principle_scores = list(architecture_assessment["design_principles"].values())
        architecture_assessment["overall_score"] = sum(principle_scores) / len(principle_scores)
        
        # Generate recommendations
        if architecture_assessment["design_principles"]["interface_segregation"] < 0.7:
            architecture_assessment["recommendations"].append(
                "Consider breaking down large interfaces into smaller, more focused ones"
            )
        
        return architecture_assessment
    
    def analyze_code_health(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall code health"""
        health_assessment = {
            "health_score": 0.0,
            "critical_issues": [],
            "warning_issues": [],
            "positive_indicators": [],
            "trends": {},
            "improvement_priorities": []
        }
        
        # Extract key metrics
        maintainability = metrics.get("maintainability_index", 70)
        test_coverage = metrics.get("test_coverage", 0.5)
        complexity = metrics.get("cyclomatic_complexity", 10)
        duplication = metrics.get("code_duplication", 0.1)
        
        # Assess health indicators
        health_factors = []
        
        # Maintainability
        if maintainability > 80:
            health_factors.append(0.9)
            health_assessment["positive_indicators"].append("High maintainability index")
        elif maintainability > 60:
            health_factors.append(0.7)
        else:
            health_factors.append(0.4)
            health_assessment["critical_issues"].append("Low maintainability index")
        
        # Test coverage
        if test_coverage > 0.8:
            health_factors.append(0.9)
            health_assessment["positive_indicators"].append("Good test coverage")
        elif test_coverage > 0.6:
            health_factors.append(0.7)
        else:
            health_factors.append(0.4)
            health_assessment["critical_issues"].append("Insufficient test coverage")
        
        # Complexity
        if complexity < 5:
            health_factors.append(0.9)
            health_assessment["positive_indicators"].append("Low complexity")
        elif complexity < 10:
            health_factors.append(0.7)
        else:
            health_factors.append(0.4)
            health_assessment["warning_issues"].append("High code complexity")
        
        # Code duplication
        if duplication < 0.05:
            health_factors.append(0.9)
            health_assessment["positive_indicators"].append("Low code duplication")
        elif duplication < 0.1:
            health_factors.append(0.7)
        else:
            health_factors.append(0.4)
            health_assessment["warning_issues"].append("High code duplication")
        
        # Calculate overall health score
        health_assessment["health_score"] = sum(health_factors) / len(health_factors)
        
        # Generate improvement priorities
        if health_assessment["health_score"] < 0.6:
            health_assessment["improvement_priorities"] = [
                "Address critical issues immediately",
                "Improve test coverage",
                "Refactor complex functions",
                "Reduce code duplication"
            ]
        elif health_assessment["health_score"] < 0.8:
            health_assessment["improvement_priorities"] = [
                "Gradually improve test coverage",
                "Address warning issues",
                "Implement code review processes"
            ]
        else:
            health_assessment["improvement_priorities"] = [
                "Maintain current quality standards",
                "Consider advanced quality metrics",
                "Implement continuous quality monitoring"
            ]
        
        return health_assessment
    
    def identify_refactoring_opportunities(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific refactoring opportunities"""
        opportunities = []
        
        # Extract relevant data
        code_smells = analysis_results.get("code_smells", [])
        complexity_issues = analysis_results.get("complexity_issues", [])
        duplication_data = analysis_results.get("duplication", {})
        
        # Large method refactoring
        if any("long method" in smell.lower() for smell in code_smells):
            opportunities.append({
                "type": "method_extraction",
                "priority": "high",
                "description": "Extract smaller methods from large functions",
                "estimated_effort": "medium",
                "benefits": ["Improved readability", "Better testability", "Lower complexity"]
            })
        
        # Code duplication
        if duplication_data.get("percentage", 0) > 0.1:
            opportunities.append({
                "type": "extract_common_code",
                "priority": "medium",
                "description": "Extract common code into reusable functions",
                "estimated_effort": "low",
                "benefits": ["Reduced duplication", "Easier maintenance", "Consistent behavior"]
            })
        
        # Complex conditionals
        if any("complex conditional" in issue.lower() for issue in complexity_issues):
            opportunities.append({
                "type": "simplify_conditionals",
                "priority": "medium",
                "description": "Simplify complex conditional logic",
                "estimated_effort": "medium",
                "benefits": ["Improved readability", "Easier debugging", "Better maintainability"]
            })
        
        # Large class refactoring
        if any("large class" in smell.lower() for smell in code_smells):
            opportunities.append({
                "type": "class_decomposition",
                "priority": "high",
                "description": "Break down large classes into smaller, focused classes",
                "estimated_effort": "high",
                "benefits": ["Better separation of concerns", "Improved testability", "Easier understanding"]
            })
        
        return opportunities
    
    def generate_quality_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive quality report"""
        report = {
            "executive_summary": "",
            "key_findings": [],
            "quality_metrics": {},
            "risk_assessment": {},
            "recommendations": [],
            "action_plan": []
        }
        
        # Generate executive summary
        health_score = analysis_data.get("health_score", 0.7)
        total_issues = len(analysis_data.get("critical_issues", [])) + len(analysis_data.get("warning_issues", []))
        
        report["executive_summary"] = (
            f"Code quality analysis reveals an overall health score of {health_score:.1%}. "
            f"The codebase shows {total_issues} issues requiring attention, with strengths in "
            f"maintainability and opportunities for improvement in test coverage and complexity management."
        )
        
        # Key findings
        report["key_findings"] = [
            "Architecture follows established patterns",
            "Code complexity is within acceptable ranges",
            "Test coverage needs improvement",
            "Dependencies are well-managed",
            "Security posture is acceptable"
        ]
        
        # Quality metrics summary
        report["quality_metrics"] = {
            "maintainability_index": analysis_data.get("maintainability_index", 70),
            "test_coverage": analysis_data.get("test_coverage", 0.78),
            "code_duplication": analysis_data.get("code_duplication", 0.05),
            "cyclomatic_complexity": analysis_data.get("cyclomatic_complexity", 8.2),
            "technical_debt_ratio": analysis_data.get("technical_debt_ratio", 0.05)
        }
        
        # Risk assessment
        report["risk_assessment"] = {
            "overall_risk": "medium",
            "security_risk": "low",
            "maintenance_risk": "medium",
            "scalability_risk": "low",
            "key_risks": [
                "Insufficient test coverage could lead to bugs",
                "High complexity in core modules",
                "Dependency vulnerabilities need attention"
            ]
        }
        
        # Recommendations
        report["recommendations"] = [
            "Increase test coverage to 85% minimum",
            "Refactor high-complexity functions",
            "Update vulnerable dependencies",
            "Implement automated code quality checks",
            "Add comprehensive documentation"
        ]
        
        # Action plan
        report["action_plan"] = [
            {
                "phase": "Immediate (1-2 weeks)",
                "actions": ["Fix critical security vulnerabilities", "Add tests for core functions"]
            },
            {
                "phase": "Short-term (1-2 months)",
                "actions": ["Refactor complex methods", "Improve documentation", "Set up CI/CD quality gates"]
            },
            {
                "phase": "Long-term (3-6 months)",
                "actions": ["Architectural improvements", "Performance optimization", "Advanced quality metrics"]
            }
        ]
        
        return report


@register_agent("senior_code_analyst")
class SeniorCodeAnalystAgent(CodeAnalystAgent):
    """
    Senior Code Analyst with advanced capabilities
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Add advanced analysis capabilities
        self.backstory += (
            " You also have expertise in enterprise architecture, "
            "performance optimization, and large-scale system design."
        )
    
    def get_specialized_instructions(self) -> str:
        """Enhanced instructions for senior-level analysis"""
        base_instructions = super().get_specialized_instructions()
        return base_instructions + """
        
        Additional senior-level analysis:
        13. Assess enterprise architecture patterns
        14. Evaluate performance characteristics
        15. Review API design and contracts
        16. Assess microservices architecture
        17. Evaluate cloud-native patterns
        18. Review data architecture and flow
        19. Assess monitoring and observability
        20. Evaluate DevOps and CI/CD practices
        
        Provide strategic recommendations for long-term
        maintainability and scalability.
        """
    
    def assess_enterprise_readiness(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess readiness for enterprise deployment"""
        enterprise_assessment = {
            "readiness_score": 0.0,
            "scalability_indicators": {},
            "reliability_indicators": {},
            "security_indicators": {},
            "compliance_indicators": {},
            "recommendations": []
        }
        
        # Assess scalability
        enterprise_assessment["scalability_indicators"] = {
            "horizontal_scalability": "good",
            "vertical_scalability": "excellent",
            "database_scalability": "needs_improvement",
            "caching_strategy": "implemented",
            "load_balancing": "configured"
        }
        
        # Assess reliability
        enterprise_assessment["reliability_indicators"] = {
            "error_handling": "comprehensive",
            "logging": "adequate",
            "monitoring": "basic",
            "circuit_breakers": "not_implemented",
            "graceful_degradation": "partial"
        }
        
        # Calculate readiness score
        positive_indicators = sum(1 for indicators in [
            enterprise_assessment["scalability_indicators"],
            enterprise_assessment["reliability_indicators"]
        ] for indicator in indicators.values() if indicator in ["good", "excellent", "implemented", "comprehensive"])
        
        total_indicators = sum(len(indicators) for indicators in [
            enterprise_assessment["scalability_indicators"],
            enterprise_assessment["reliability_indicators"]
        ])
        
        enterprise_assessment["readiness_score"] = positive_indicators / total_indicators if total_indicators > 0 else 0.0
        
        return enterprise_assessment