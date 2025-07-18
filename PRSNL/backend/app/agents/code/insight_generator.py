"""
Insight Generator Agent - Generates insights from code analysis
"""

import logging
from typing import Optional, Dict, Any, List
from crewai import Agent

from app.agents.base_agent import PRSNLBaseAgent
from app.config import settings

logger = logging.getLogger(__name__)


class InsightGeneratorAgent(PRSNLBaseAgent):
    """Agent for generating insights from code analysis results"""
    
    def __init__(
        self,
        role: str = "Code Insight Generator",
        goal: str = "Generate actionable insights and recommendations from code analysis results",
        backstory: Optional[str] = None,
        **kwargs
    ):
        if backstory is None:
            backstory = (
                "You are a senior software engineer and architect with expertise in "
                "generating actionable insights from code analysis. Your strength lies "
                "in identifying patterns, suggesting improvements, and creating "
                "comprehensive reports that help development teams make informed decisions. "
                "You excel at translating technical analysis into clear, actionable recommendations."
            )
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            **kwargs
        )
    
    def get_agent(self) -> Agent:
        """Get the configured agent instance"""
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            llm=self.get_llm_config(),
            verbose=self.verbose,
            allow_delegation=self.allow_delegation,
            max_iter=self.max_iter,
            memory=self.memory
        )
    
    def generate_code_insights(
        self,
        analysis_results: Dict[str, Any],
        repository_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate insights from code analysis results
        
        Args:
            analysis_results: Results from code analysis
            repository_context: Context about the repository
            
        Returns:
            Dict containing generated insights
        """
        try:
            # Extract key metrics from analysis
            metrics = analysis_results.get('metrics', {})
            patterns = analysis_results.get('patterns', [])
            issues = analysis_results.get('issues', [])
            
            insights = {
                'summary': self._generate_summary_insights(metrics, patterns, issues),
                'recommendations': self._generate_recommendations(analysis_results),
                'priorities': self._prioritize_issues(issues),
                'tech_debt': self._analyze_tech_debt(patterns, metrics),
                'quality_score': self._calculate_quality_score(metrics, issues)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating code insights: {e}")
            return {"error": str(e)}
    
    def _generate_summary_insights(
        self,
        metrics: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        issues: List[Dict[str, Any]]
    ) -> str:
        """Generate summary insights from analysis components"""
        total_lines = metrics.get('total_lines', 0)
        complexity = metrics.get('cyclomatic_complexity', 0)
        issue_count = len(issues)
        pattern_count = len(patterns)
        
        summary = f"Code analysis reveals {total_lines} lines of code with "
        summary += f"cyclomatic complexity of {complexity}. "
        summary += f"Found {issue_count} issues and {pattern_count} patterns."
        
        return summary
    
    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        metrics = analysis_results.get('metrics', {})
        issues = analysis_results.get('issues', [])
        
        # Complexity recommendations
        if metrics.get('cyclomatic_complexity', 0) > 10:
            recommendations.append("Consider refactoring complex functions to improve maintainability")
        
        # Code coverage recommendations
        if metrics.get('test_coverage', 100) < 80:
            recommendations.append("Increase test coverage to improve code reliability")
        
        # Security recommendations
        security_issues = [i for i in issues if i.get('category') == 'security']
        if security_issues:
            recommendations.append("Address security vulnerabilities as high priority")
        
        return recommendations
    
    def _prioritize_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize issues by severity and impact"""
        # Define priority mapping
        priority_map = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        
        # Sort issues by priority
        prioritized = sorted(
            issues,
            key=lambda x: priority_map.get(x.get('severity', 'low'), 4)
        )
        
        return prioritized
    
    def _analyze_tech_debt(
        self,
        patterns: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze technical debt indicators"""
        debt_score = 0
        debt_factors = []
        
        # Code complexity factor
        complexity = metrics.get('cyclomatic_complexity', 0)
        if complexity > 15:
            debt_score += 3
            debt_factors.append("High cyclomatic complexity")
        elif complexity > 10:
            debt_score += 2
            debt_factors.append("Moderate cyclomatic complexity")
        
        # Code duplication factor
        duplication = metrics.get('code_duplication', 0)
        if duplication > 10:
            debt_score += 2
            debt_factors.append("Code duplication detected")
        
        # Pattern-based debt
        antipatterns = [p for p in patterns if p.get('type') == 'antipattern']
        if antipatterns:
            debt_score += len(antipatterns)
            debt_factors.append(f"{len(antipatterns)} antipatterns detected")
        
        return {
            'score': debt_score,
            'level': 'high' if debt_score > 5 else 'medium' if debt_score > 2 else 'low',
            'factors': debt_factors
        }
    
    def _calculate_quality_score(
        self,
        metrics: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall code quality score"""
        base_score = 100
        
        # Deduct points for issues
        critical_issues = len([i for i in issues if i.get('severity') == 'critical'])
        high_issues = len([i for i in issues if i.get('severity') == 'high'])
        medium_issues = len([i for i in issues if i.get('severity') == 'medium'])
        
        base_score -= (critical_issues * 10)
        base_score -= (high_issues * 5)
        base_score -= (medium_issues * 2)
        
        # Factor in complexity
        complexity = metrics.get('cyclomatic_complexity', 0)
        if complexity > 15:
            base_score -= 10
        elif complexity > 10:
            base_score -= 5
        
        # Factor in test coverage
        coverage = metrics.get('test_coverage', 0)
        if coverage < 50:
            base_score -= 15
        elif coverage < 80:
            base_score -= 5
        
        # Ensure score doesn't go below 0
        final_score = max(0, base_score)
        
        # Determine grade
        if final_score >= 90:
            grade = 'A'
        elif final_score >= 80:
            grade = 'B'
        elif final_score >= 70:
            grade = 'C'
        elif final_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': final_score,
            'grade': grade,
            'factors': {
                'critical_issues': critical_issues,
                'high_issues': high_issues,
                'complexity': complexity,
                'test_coverage': coverage
            }
        }