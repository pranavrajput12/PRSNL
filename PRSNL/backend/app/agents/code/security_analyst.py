"""
Security Analyst Agent - Specialized in code security analysis
"""

import logging
from typing import Optional, Dict, Any, List
from crewai import Agent

from app.agents.base_agent import PRSNLBaseAgent
from app.config import settings

logger = logging.getLogger(__name__)


class SecurityAnalystAgent(PRSNLBaseAgent):
    """Agent specialized in code security analysis and vulnerability detection"""
    
    def __init__(
        self,
        role: str = "Code Security Analyst",
        goal: str = "Identify security vulnerabilities and provide security recommendations for code",
        backstory: Optional[str] = None,
        **kwargs
    ):
        if backstory is None:
            backstory = (
                "You are a cybersecurity expert with extensive experience in code security "
                "analysis and vulnerability assessment. Your expertise includes identifying "
                "common security vulnerabilities such as SQL injection, XSS, CSRF, "
                "authentication flaws, and insecure configurations. You excel at providing "
                "actionable security recommendations and helping development teams implement "
                "secure coding practices."
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
    
    def analyze_security_vulnerabilities(
        self,
        code_content: str,
        file_path: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze code for security vulnerabilities
        
        Args:
            code_content: The code content to analyze
            file_path: Path to the file being analyzed
            context: Additional context about the code
            
        Returns:
            Dict containing security analysis results
        """
        try:
            vulnerabilities = []
            security_score = 100
            
            # Check for common vulnerabilities
            sql_injection_issues = self._check_sql_injection(code_content, file_path)
            xss_issues = self._check_xss_vulnerabilities(code_content, file_path)
            auth_issues = self._check_authentication_flaws(code_content, file_path)
            crypto_issues = self._check_cryptographic_issues(code_content, file_path)
            input_validation_issues = self._check_input_validation(code_content, file_path)
            
            all_issues = (sql_injection_issues + xss_issues + auth_issues + 
                         crypto_issues + input_validation_issues)
            
            # Calculate security score
            critical_count = len([i for i in all_issues if i.get('severity') == 'critical'])
            high_count = len([i for i in all_issues if i.get('severity') == 'high'])
            medium_count = len([i for i in all_issues if i.get('severity') == 'medium'])
            
            security_score -= (critical_count * 20)
            security_score -= (high_count * 10)
            security_score -= (medium_count * 5)
            security_score = max(0, security_score)
            
            return {
                'vulnerabilities': all_issues,
                'security_score': security_score,
                'risk_level': self._calculate_risk_level(security_score),
                'recommendations': self._generate_security_recommendations(all_issues),
                'summary': {
                    'total_issues': len(all_issues),
                    'critical': critical_count,
                    'high': high_count,
                    'medium': medium_count,
                    'low': len(all_issues) - critical_count - high_count - medium_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing security vulnerabilities: {e}")
            return {"error": str(e)}
    
    def _check_sql_injection(self, code_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for SQL injection vulnerabilities"""
        issues = []
        
        # Common SQL injection patterns
        sql_patterns = [
            r'execute\s*\(\s*["\'].*\+.*["\']',  # String concatenation in SQL
            r'query\s*\(\s*["\'].*\+.*["\']',    # Query with string concatenation
            r'raw\s*\(\s*["\'].*\+.*["\']',      # Raw SQL with concatenation
        ]
        
        import re
        for i, line in enumerate(code_content.split('\n'), 1):
            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'sql_injection',
                        'severity': 'critical',
                        'line': i,
                        'description': 'Potential SQL injection vulnerability detected',
                        'recommendation': 'Use parameterized queries or prepared statements',
                        'file_path': file_path
                    })
        
        return issues
    
    def _check_xss_vulnerabilities(self, code_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for XSS vulnerabilities"""
        issues = []
        
        # XSS patterns
        xss_patterns = [
            r'innerHTML\s*=\s*.*\+',           # innerHTML with concatenation
            r'document\.write\s*\(',           # document.write usage
            r'eval\s*\(',                      # eval usage
            r'dangerouslySetInnerHTML',        # React dangerous HTML
        ]
        
        import re
        for i, line in enumerate(code_content.split('\n'), 1):
            for pattern in xss_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'xss',
                        'severity': 'high',
                        'line': i,
                        'description': 'Potential XSS vulnerability detected',
                        'recommendation': 'Sanitize user input and use safe DOM manipulation methods',
                        'file_path': file_path
                    })
        
        return issues
    
    def _check_authentication_flaws(self, code_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for authentication and authorization flaws"""
        issues = []
        
        # Authentication patterns
        auth_patterns = [
            r'password\s*=\s*["\'][^"\']*["\']',  # Hardcoded passwords
            r'api_key\s*=\s*["\'][^"\']*["\']',   # Hardcoded API keys
            r'secret\s*=\s*["\'][^"\']*["\']',    # Hardcoded secrets
            r'token\s*=\s*["\'][^"\']*["\']',     # Hardcoded tokens
        ]
        
        import re
        for i, line in enumerate(code_content.split('\n'), 1):
            for pattern in auth_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'hardcoded_credentials',
                        'severity': 'critical',
                        'line': i,
                        'description': 'Hardcoded credentials detected',
                        'recommendation': 'Use environment variables or secure credential storage',
                        'file_path': file_path
                    })
        
        return issues
    
    def _check_cryptographic_issues(self, code_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for cryptographic issues"""
        issues = []
        
        # Crypto patterns
        crypto_patterns = [
            r'md5\s*\(',                       # MD5 usage (weak)
            r'sha1\s*\(',                      # SHA1 usage (weak)
            r'DES\s*\(',                       # DES encryption (weak)
            r'random\s*\(\)',                  # Weak random number generation
        ]
        
        import re
        for i, line in enumerate(code_content.split('\n'), 1):
            for pattern in crypto_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'weak_cryptography',
                        'severity': 'medium',
                        'line': i,
                        'description': 'Weak cryptographic algorithm detected',
                        'recommendation': 'Use strong cryptographic algorithms (SHA-256, AES, etc.)',
                        'file_path': file_path
                    })
        
        return issues
    
    def _check_input_validation(self, code_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for input validation issues"""
        issues = []
        
        # Input validation patterns
        validation_patterns = [
            r'request\.\w+\s*\[.*\](?!\s*in\s|\s*==|\s*!=)',  # Direct request parameter access
            r'params\[.*\](?!\s*in\s|\s*==|\s*!=)',           # Direct parameter access
            r'open\s*\(\s*.*request',                         # File operation with user input
        ]
        
        import re
        for i, line in enumerate(code_content.split('\n'), 1):
            for pattern in validation_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'type': 'input_validation',
                        'severity': 'medium',
                        'line': i,
                        'description': 'Potential input validation issue detected',
                        'recommendation': 'Validate and sanitize all user inputs',
                        'file_path': file_path
                    })
        
        return issues
    
    def _calculate_risk_level(self, security_score: int) -> str:
        """Calculate risk level based on security score"""
        if security_score >= 80:
            return 'low'
        elif security_score >= 60:
            return 'medium'
        elif security_score >= 40:
            return 'high'
        else:
            return 'critical'
    
    def _generate_security_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on found issues"""
        recommendations = []
        
        # Group issues by type
        issue_types = {}
        for issue in issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        # Generate recommendations for each type
        if 'sql_injection' in issue_types:
            recommendations.append(
                "Implement parameterized queries or prepared statements to prevent SQL injection"
            )
        
        if 'xss' in issue_types:
            recommendations.append(
                "Implement input sanitization and output encoding to prevent XSS attacks"
            )
        
        if 'hardcoded_credentials' in issue_types:
            recommendations.append(
                "Move all credentials to environment variables or secure credential storage"
            )
        
        if 'weak_cryptography' in issue_types:
            recommendations.append(
                "Replace weak cryptographic algorithms with strong alternatives"
            )
        
        if 'input_validation' in issue_types:
            recommendations.append(
                "Implement comprehensive input validation for all user inputs"
            )
        
        # General recommendations
        recommendations.extend([
            "Conduct regular security code reviews",
            "Implement automated security testing in CI/CD pipeline",
            "Follow OWASP secure coding guidelines",
            "Keep all dependencies up to date with security patches"
        ])
        
        return recommendations