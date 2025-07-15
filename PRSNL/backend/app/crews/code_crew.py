"""
Code Analysis Crew - Orchestrates code intelligence workflows

This crew handles comprehensive code analysis including architecture assessment,
pattern detection, security scanning, and quality evaluation.
"""

import logging
from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, crew, task

from app.crews.base_crew import PRSNLBaseCrew
from app.crews import register_crew
from app.agents.code import (
    CodeAnalystAgent,
    PatternDetectorAgent,
    InsightGeneratorAgent,
    SecurityAnalystAgent
)

logger = logging.getLogger(__name__)


@register_crew("code_analysis")
class CodeAnalysisCrew(PRSNLBaseCrew):
    """Crew for comprehensive code analysis and intelligence"""
    
    @agent
    def code_analyst(self) -> Agent:
        """Code Analyst agent"""
        agent_instance = CodeAnalystAgent()
        return agent_instance.get_agent()
    
    @agent
    def pattern_detector(self) -> Agent:
        """Pattern Detector agent"""
        agent_instance = PatternDetectorAgent()
        return agent_instance.get_agent()
    
    @agent
    def security_analyst(self) -> Agent:
        """Security Analyst agent"""
        agent_instance = SecurityAnalystAgent()
        return agent_instance.get_agent()
    
    @agent
    def insight_generator(self) -> Agent:
        """Insight Generator agent"""
        agent_instance = InsightGeneratorAgent()
        return agent_instance.get_agent()
    
    @task
    def analyze_code_structure_task(self) -> Task:
        """Task for analyzing code structure and architecture"""
        return Task(
            description=(
                "Analyze the code repository structure, architecture patterns, "
                "and overall design quality. Assess maintainability, scalability, "
                "and adherence to best practices. Repository: {repository_path}"
            ),
            expected_output=(
                "Comprehensive code structure analysis including:\n"
                "1. Architecture assessment and patterns identified\n"
                "2. Code quality metrics and maintainability index\n"
                "3. Dependency analysis and recommendations\n"
                "4. Test coverage and quality assessment\n"
                "5. Technical debt evaluation\n"
                "6. Scalability and performance implications"
            ),
            agent=self.code_analyst()
        )
    
    @task
    def detect_patterns_task(self) -> Task:
        """Task for detecting design patterns and code smells"""
        return Task(
            description=(
                "Detect design patterns, anti-patterns, and code smells in the "
                "codebase. Identify both positive patterns to reinforce and "
                "negative patterns that need attention."
            ),
            expected_output=(
                "Pattern detection report including:\n"
                "1. Design patterns found and their appropriateness\n"
                "2. Anti-patterns and their impact on code quality\n"
                "3. Code smells prioritized by severity\n"
                "4. Refactoring recommendations with effort estimates\n"
                "5. Pattern usage best practices\n"
                "6. Code improvement roadmap"
            ),
            agent=self.pattern_detector()
        )
    
    @task
    def security_analysis_task(self) -> Task:
        """Task for security analysis and vulnerability detection"""
        return Task(
            description=(
                "Perform comprehensive security analysis of the codebase. "
                "Identify vulnerabilities, security risks, and provide "
                "recommendations for improving security posture."
            ),
            expected_output=(
                "Security analysis report including:\n"
                "1. Vulnerability assessment with severity ratings\n"
                "2. Security best practices compliance\n"
                "3. Dependency security analysis\n"
                "4. Authentication and authorization review\n"
                "5. Data protection and privacy assessment\n"
                "6. Security improvement recommendations"
            ),
            agent=self.security_analyst()
        )
    
    @task
    def generate_insights_task(self) -> Task:
        """Task for generating actionable insights from analysis"""
        return Task(
            description=(
                "Synthesize results from code analysis, pattern detection, and "
                "security analysis to generate actionable insights and strategic "
                "recommendations for the development team."
            ),
            expected_output=(
                "Strategic insights report including:\n"
                "1. Executive summary of code health\n"
                "2. Key findings and their business impact\n"
                "3. Prioritized action plan with timelines\n"
                "4. Risk assessment and mitigation strategies\n"
                "5. Team productivity recommendations\n"
                "6. Long-term architectural guidance"
            ),
            agent=self.insight_generator()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Code Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
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


@register_crew("enterprise_code_analysis")
class EnterpriseCodeAnalysisCrew(CodeAnalysisCrew):
    """Enhanced crew for enterprise-level code analysis"""
    
    @agent
    def senior_code_analyst(self) -> Agent:
        """Senior Code Analyst agent"""
        from app.agents.code.code_analyst import SeniorCodeAnalystAgent
        agent_instance = SeniorCodeAnalystAgent()
        return agent_instance.get_agent()
    
    @task
    def enterprise_readiness_task(self) -> Task:
        """Task for assessing enterprise readiness"""
        return Task(
            description=(
                "Assess the codebase for enterprise deployment readiness. "
                "Evaluate scalability, reliability, security, and compliance "
                "requirements for enterprise environments."
            ),
            expected_output=(
                "Enterprise readiness assessment including:\n"
                "1. Scalability assessment and recommendations\n"
                "2. Reliability and fault tolerance evaluation\n"
                "3. Security and compliance posture\n"
                "4. Performance and monitoring capabilities\n"
                "5. DevOps and CI/CD readiness\n"
                "6. Enterprise architecture alignment"
            ),
            agent=self.senior_code_analyst()
        )
    
    def get_process_type(self) -> str:
        """Use hierarchical process for enterprise analysis"""
        return "hierarchical"
    
    @crew
    def crew(self) -> Crew:
        """Creates the Enterprise Code Analysis crew"""
        # Replace code analyst with senior version
        agents = [
            self.senior_code_analyst(),
            self.pattern_detector(),
            self.security_analyst(),
            self.insight_generator()
        ]
        
        tasks = self.tasks + [self.enterprise_readiness_task()]
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.hierarchical,
            manager_llm=self.get_llm_config(),
            verbose=True,
            memory=True
        )


@register_crew("security_focused_analysis")
class SecurityFocusedAnalysisCrew(PRSNLBaseCrew):
    """Specialized crew for security-focused code analysis"""
    
    @agent
    def security_analyst(self) -> Agent:
        """Security Analyst agent"""
        agent_instance = SecurityAnalystAgent()
        return agent_instance.get_agent()
    
    @agent
    def vulnerability_assessor(self) -> Agent:
        """Vulnerability Assessor agent"""
        return Agent(
            role="Vulnerability Assessor",
            goal="Identify and assess security vulnerabilities in code",
            backstory="Expert in vulnerability assessment and penetration testing",
            tools=[],
            llm=self.get_llm_config()
        )
    
    @task
    def vulnerability_scan_task(self) -> Task:
        """Task for comprehensive vulnerability scanning"""
        return Task(
            description=(
                "Perform deep vulnerability scanning of the codebase. "
                "Identify security weaknesses, potential attack vectors, "
                "and provide detailed remediation guidance."
            ),
            expected_output=(
                "Vulnerability assessment report including:\n"
                "1. Detailed vulnerability inventory\n"
                "2. Risk assessment and CVSS scores\n"
                "3. Attack vector analysis\n"
                "4. Remediation recommendations\n"
                "5. Security testing recommendations\n"
                "6. Compliance gap analysis"
            ),
            agent=self.vulnerability_assessor()
        )
    
    @task
    def security_recommendations_task(self) -> Task:
        """Task for generating security recommendations"""
        return Task(
            description=(
                "Generate comprehensive security recommendations based on "
                "vulnerability assessment and security analysis results."
            ),
            expected_output=(
                "Security recommendations including:\n"
                "1. Immediate security fixes required\n"
                "2. Security architecture improvements\n"
                "3. Secure coding practices guidance\n"
                "4. Security testing strategy\n"
                "5. Monitoring and alerting recommendations\n"
                "6. Long-term security roadmap"
            ),
            agent=self.security_analyst()
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Security Focused Analysis crew"""
        return Crew(
            agents=[self.security_analyst(), self.vulnerability_assessor()],
            tasks=[self.vulnerability_scan_task(), self.security_recommendations_task()],
            process=Process.sequential,
            verbose=True,
            memory=True
        )