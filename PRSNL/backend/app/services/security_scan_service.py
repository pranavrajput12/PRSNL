"""
Security Scan Service for PRSNL CodeMirror CLI Integration

Static security analysis using Semgrep for vulnerability detection,
OWASP compliance checking, and custom security pattern recognition.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from langfuse import observe

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Security finding severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """Data class for security findings"""
    rule_id: str
    severity: SeverityLevel
    message: str
    file_path: str
    line_number: int
    column_number: Optional[int]
    code_snippet: str
    fix_suggestion: Optional[str]
    owasp_category: Optional[str]
    cwe_id: Optional[str]
    confidence: str  # "high", "medium", "low"
    
    
@dataclass
class SecurityScanResult:
    """Complete security scan result"""
    repository_path: str
    scan_timestamp: datetime
    scan_duration_seconds: float
    total_findings: int
    findings_by_severity: Dict[str, int]
    
    # Detailed findings
    findings: List[SecurityFinding]
    
    # Summary statistics
    files_scanned: int
    rules_executed: int
    owasp_categories: Dict[str, int]
    cwe_categories: Dict[str, int]
    
    # Risk assessment
    overall_security_score: float  # 0-100 (100 = most secure)
    high_risk_files: List[str]
    security_hotspots: List[Dict[str, Any]]
    
    # Compliance
    owasp_compliance_score: float
    common_vulnerabilities: List[Dict[str, Any]]


class SecurityScanService:
    """
    Service for static security analysis using Semgrep.
    
    Provides comprehensive vulnerability detection, OWASP compliance checking,
    and security pattern recognition for code repositories.
    """
    
    def __init__(self):
        self.temp_dirs = []  # Track temporary directories for cleanup
        self.custom_rules_path = None
        
        # Default Semgrep rulesets to use
        self.default_rulesets = [
            "p/security-audit",  # General security issues
            "p/owasp-top-ten",   # OWASP Top 10 vulnerabilities
            "p/cwe-top-25",      # CWE Top 25 most dangerous software errors
            "p/secrets",         # Secret detection
            "p/xss",            # Cross-site scripting
            "p/sql-injection",   # SQL injection
        ]
        
        # OWASP Top 10 2021 categories mapping
        self.owasp_categories = {
            "A01": "Broken Access Control",
            "A02": "Cryptographic Failures", 
            "A03": "Injection",
            "A04": "Insecure Design",
            "A05": "Security Misconfiguration",
            "A06": "Vulnerable and Outdated Components",
            "A07": "Identification and Authentication Failures",
            "A08": "Software and Data Integrity Failures",
            "A09": "Security Logging and Monitoring Failures",
            "A10": "Server-Side Request Forgery (SSRF)"
        }
        
    def __del__(self):
        """Cleanup temporary directories"""
        self._cleanup_temp_dirs()
    
    def _cleanup_temp_dirs(self):
        """Clean up any temporary directories created during analysis"""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
        self.temp_dirs.clear()
    
    @observe(name="security_scan_full")
    async def scan_repository(
        self, 
        repo_path: str,
        scan_config: Optional[Dict[str, Any]] = None
    ) -> SecurityScanResult:
        """
        Perform comprehensive security scan on repository.
        
        Args:
            repo_path: Path to repository to scan
            scan_config: Optional scan configuration
            
        Returns:
            SecurityScanResult with comprehensive security analysis
        """
        logger.info(f"Starting security scan for repository: {repo_path}")
        start_time = datetime.utcnow()
        
        try:
            # Validate repository path
            if not os.path.exists(repo_path):
                raise ValueError(f"Repository path does not exist: {repo_path}")
            
            # Setup scan configuration
            config = scan_config or {}
            rulesets = config.get('rulesets', self.default_rulesets)
            include_patterns = config.get('include_patterns', ['**/*'])
            exclude_patterns = config.get('exclude_patterns', [
                '**/.git/**', '**/node_modules/**', '**/venv/**', 
                '**/__pycache__/**', '**/build/**', '**/dist/**'
            ])
            
            # Run semgrep scan
            scan_results = await self._run_semgrep_scan(
                repo_path, rulesets, include_patterns, exclude_patterns
            )
            
            # Process and analyze results
            processed_results = await self._process_scan_results(
                repo_path, scan_results, start_time
            )
            
            scan_duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Security scan completed in {scan_duration:.2f} seconds")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Security scan failed for {repo_path}: {e}")
            raise
        finally:
            # Cleanup temporary resources
            self._cleanup_temp_dirs()
    
    async def _run_semgrep_scan(
        self, 
        repo_path: str, 
        rulesets: List[str],
        include_patterns: List[str],
        exclude_patterns: List[str]
    ) -> Dict[str, Any]:
        """Run semgrep scan with specified configuration"""
        
        try:
            # Build semgrep command
            cmd = [
                'semgrep',
                '--config=auto',  # Use auto-detection plus specified rulesets
                '--json',  # Output in JSON format
                '--no-git-ignore',  # Don't respect .gitignore for security scanning
                '--verbose',
                '--timeout=300',  # 5 minute timeout per file
            ]
            
            # Add rulesets
            for ruleset in rulesets:
                cmd.extend(['--config', ruleset])
            
            # Add include patterns
            for pattern in include_patterns:
                cmd.extend(['--include', pattern])
            
            # Add exclude patterns
            for pattern in exclude_patterns:
                cmd.extend(['--exclude', pattern])
            
            # Add target path
            cmd.append(repo_path)
            
            logger.info(f"Running semgrep command: {' '.join(cmd)}")
            
            # Run semgrep
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and process.returncode != 1:  # 1 = findings found
                logger.error(f"Semgrep scan failed with return code {process.returncode}")
                logger.error(f"Stderr: {stderr.decode()}")
                raise RuntimeError(f"Semgrep scan failed: {stderr.decode()}")
            
            # Parse JSON output
            try:
                results = json.loads(stdout.decode())
                logger.info(f"Semgrep scan completed with {len(results.get('results', []))} findings")
                return results
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse semgrep JSON output: {e}")
                logger.error(f"Output: {stdout.decode()[:1000]}")
                raise ValueError(f"Invalid JSON output from semgrep: {e}")
                
        except Exception as e:
            logger.error(f"Semgrep execution failed: {e}")
            raise
    
    @observe(name="security_process_results") 
    async def _process_scan_results(
        self, 
        repo_path: str, 
        scan_results: Dict[str, Any], 
        start_time: datetime
    ) -> SecurityScanResult:
        """Process and analyze semgrep scan results"""
        
        scan_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Extract findings from semgrep results
        raw_findings = scan_results.get('results', [])
        findings = []
        
        for raw_finding in raw_findings:
            try:
                finding = self._parse_semgrep_finding(raw_finding, repo_path)
                if finding:
                    findings.append(finding)
            except Exception as e:
                logger.debug(f"Error parsing finding: {e}")
                continue
        
        # Calculate statistics
        total_findings = len(findings)
        findings_by_severity = self._calculate_severity_distribution(findings)
        owasp_categories = self._analyze_owasp_categories(findings)
        cwe_categories = self._analyze_cwe_categories(findings)
        
        # Risk assessment
        overall_security_score = self._calculate_security_score(findings)
        high_risk_files = self._identify_high_risk_files(findings)
        security_hotspots = self._identify_security_hotspots(findings)
        
        # Compliance assessment
        owasp_compliance_score = self._calculate_owasp_compliance(findings)
        common_vulnerabilities = self._analyze_common_vulnerabilities(findings)
        
        # Count files scanned and rules executed
        files_scanned = len(set(f.file_path for f in findings)) if findings else 0
        rules_executed = len(set(f.rule_id for f in findings)) if findings else 0
        
        return SecurityScanResult(
            repository_path=repo_path,
            scan_timestamp=datetime.utcnow(),
            scan_duration_seconds=scan_duration,
            total_findings=total_findings,
            findings_by_severity=findings_by_severity,
            findings=findings,
            files_scanned=files_scanned,
            rules_executed=rules_executed,
            owasp_categories=owasp_categories,
            cwe_categories=cwe_categories,
            overall_security_score=overall_security_score,
            high_risk_files=high_risk_files,
            security_hotspots=security_hotspots,
            owasp_compliance_score=owasp_compliance_score,
            common_vulnerabilities=common_vulnerabilities
        )
    
    def _parse_semgrep_finding(self, raw_finding: Dict[str, Any], repo_path: str) -> Optional[SecurityFinding]:
        """Parse a semgrep finding into our SecurityFinding format"""
        
        try:
            # Extract basic information
            check_id = raw_finding.get('check_id', 'unknown')
            message = raw_finding.get('message', 'No message provided')
            
            # Extract file location
            path_info = raw_finding.get('path', '')
            start_info = raw_finding.get('start', {})
            line_number = start_info.get('line', 0)
            column_number = start_info.get('col')
            
            # Extract code snippet
            extra = raw_finding.get('extra', {})
            lines = extra.get('lines', '')
            
            # Determine severity
            severity_str = extra.get('severity', 'INFO').lower()
            severity = self._map_severity(severity_str)
            
            # Extract metadata
            metadata = extra.get('metadata', {})
            owasp_category = self._extract_owasp_category(metadata)
            cwe_id = self._extract_cwe_id(metadata)
            confidence = metadata.get('confidence', 'medium')
            
            # Generate fix suggestion if available
            fix_suggestion = self._generate_fix_suggestion(check_id, message, metadata)
            
            return SecurityFinding(
                rule_id=check_id,
                severity=severity,
                message=message,
                file_path=path_info,
                line_number=line_number,
                column_number=column_number,
                code_snippet=lines,
                fix_suggestion=fix_suggestion,
                owasp_category=owasp_category,
                cwe_id=cwe_id,
                confidence=confidence
            )
            
        except Exception as e:
            logger.debug(f"Error parsing semgrep finding: {e}")
            return None
    
    def _map_severity(self, severity_str: str) -> SeverityLevel:
        """Map semgrep severity to our severity enum"""
        severity_map = {
            'error': SeverityLevel.HIGH,
            'warning': SeverityLevel.MEDIUM, 
            'info': SeverityLevel.LOW,
            'critical': SeverityLevel.CRITICAL,
            'high': SeverityLevel.HIGH,
            'medium': SeverityLevel.MEDIUM,
            'low': SeverityLevel.LOW
        }
        return severity_map.get(severity_str.lower(), SeverityLevel.INFO)
    
    def _extract_owasp_category(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract OWASP category from metadata"""
        # Look for OWASP references in metadata
        for key, value in metadata.items():
            if 'owasp' in key.lower():
                if isinstance(value, list):
                    return value[0] if value else None
                return str(value)
        
        # Check in references
        references = metadata.get('references', [])
        for ref in references:
            if 'owasp' in ref.lower():
                # Extract OWASP category from URL or reference
                for category_id, category_name in self.owasp_categories.items():
                    if category_id.lower() in ref.lower() or category_name.lower() in ref.lower():
                        return f"{category_id}: {category_name}"
        
        return None
    
    def _extract_cwe_id(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Extract CWE ID from metadata"""
        # Look for CWE references
        for key, value in metadata.items():
            if 'cwe' in key.lower():
                if isinstance(value, list):
                    return f"CWE-{value[0]}" if value else None
                return f"CWE-{value}"
        
        # Check in references
        references = metadata.get('references', [])
        for ref in references:
            if 'cwe' in ref.lower():
                # Extract CWE number from reference
                import re
                cwe_match = re.search(r'cwe-(\d+)', ref.lower())
                if cwe_match:
                    return f"CWE-{cwe_match.group(1)}"
        
        return None
    
    def _generate_fix_suggestion(self, rule_id: str, message: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Generate fix suggestion based on the finding"""
        
        # Common fix suggestions based on rule patterns
        fix_suggestions = {
            'hardcoded-password': "Replace hardcoded password with environment variable or secure configuration.",
            'sql-injection': "Use parameterized queries or prepared statements to prevent SQL injection.",
            'xss': "Sanitize user input and use proper output encoding to prevent XSS attacks.",
            'csrf': "Implement CSRF tokens to protect against cross-site request forgery.",
            'weak-crypto': "Use strong cryptographic algorithms (AES-256, SHA-256) instead of weak ones.",
            'insecure-randomness': "Use cryptographically secure random number generators.",
            'path-traversal': "Validate and sanitize file paths to prevent directory traversal attacks.",
            'command-injection': "Validate input and use safe command execution methods.",
            'insecure-transport': "Use HTTPS/TLS for all data transmission.",
            'weak-hash': "Use strong hashing algorithms like bcrypt, scrypt, or Argon2 for passwords."
        }
        
        # Look for fix suggestions in rule metadata
        fix_from_metadata = metadata.get('fix', metadata.get('fix_regex'))
        if fix_from_metadata:
            return str(fix_from_metadata)
        
        # Match common patterns in rule ID
        rule_lower = rule_id.lower()
        for pattern, suggestion in fix_suggestions.items():
            if pattern in rule_lower:
                return suggestion
        
        # Generic suggestion based on message
        if 'password' in message.lower():
            return "Avoid hardcoding sensitive information. Use environment variables or secure vaults."
        elif 'injection' in message.lower():
            return "Validate and sanitize all user inputs to prevent injection attacks."
        elif 'crypto' in message.lower() or 'hash' in message.lower():
            return "Use up-to-date cryptographic libraries and strong algorithms."
        
        return None
    
    def _calculate_severity_distribution(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Calculate distribution of findings by severity"""
        distribution = {severity.value: 0 for severity in SeverityLevel}
        
        for finding in findings:
            distribution[finding.severity.value] += 1
        
        return distribution
    
    def _analyze_owasp_categories(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Analyze OWASP category distribution"""
        categories = {}
        
        for finding in findings:
            if finding.owasp_category:
                categories[finding.owasp_category] = categories.get(finding.owasp_category, 0) + 1
        
        return categories
    
    def _analyze_cwe_categories(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Analyze CWE category distribution"""
        categories = {}
        
        for finding in findings:
            if finding.cwe_id:
                categories[finding.cwe_id] = categories.get(finding.cwe_id, 0) + 1
        
        return categories
    
    def _calculate_security_score(self, findings: List[SecurityFinding]) -> float:
        """Calculate overall security score (0-100, higher is better)"""
        if not findings:
            return 100.0  # Perfect score if no findings
        
        # Weight findings by severity
        severity_weights = {
            SeverityLevel.CRITICAL: 20,
            SeverityLevel.HIGH: 10,
            SeverityLevel.MEDIUM: 5,
            SeverityLevel.LOW: 2,
            SeverityLevel.INFO: 1
        }
        
        total_weight = sum(severity_weights[finding.severity] for finding in findings)
        
        # Scale to 0-100 (assuming 100 weighted findings = 0 score)
        max_expected_weight = 100
        score = max(0, 100 - (total_weight * 100 / max_expected_weight))
        
        return round(score, 2)
    
    def _identify_high_risk_files(self, findings: List[SecurityFinding]) -> List[str]:
        """Identify files with the highest security risk"""
        file_risk_scores = {}
        
        severity_weights = {
            SeverityLevel.CRITICAL: 20,
            SeverityLevel.HIGH: 10,
            SeverityLevel.MEDIUM: 5,
            SeverityLevel.LOW: 2,
            SeverityLevel.INFO: 1
        }
        
        for finding in findings:
            file_path = finding.file_path
            weight = severity_weights[finding.severity]
            file_risk_scores[file_path] = file_risk_scores.get(file_path, 0) + weight
        
        # Return top 10 highest risk files
        sorted_files = sorted(file_risk_scores.items(), key=lambda x: x[1], reverse=True)
        return [file_path for file_path, _ in sorted_files[:10]]
    
    def _identify_security_hotspots(self, findings: List[SecurityFinding]) -> List[Dict[str, Any]]:
        """Identify security hotspots (files with multiple different vulnerability types)"""
        file_vulnerabilities = {}
        
        for finding in findings:
            file_path = finding.file_path
            if file_path not in file_vulnerabilities:
                file_vulnerabilities[file_path] = {
                    'total_findings': 0,
                    'unique_rules': set(),
                    'severity_counts': {s.value: 0 for s in SeverityLevel},
                    'owasp_categories': set(),
                    'cwe_ids': set()
                }
            
            file_data = file_vulnerabilities[file_path]
            file_data['total_findings'] += 1
            file_data['unique_rules'].add(finding.rule_id)
            file_data['severity_counts'][finding.severity.value] += 1
            
            if finding.owasp_category:
                file_data['owasp_categories'].add(finding.owasp_category)
            if finding.cwe_id:
                file_data['cwe_ids'].add(finding.cwe_id)
        
        # Create hotspot entries
        hotspots = []
        for file_path, data in file_vulnerabilities.items():
            if data['total_findings'] >= 3:  # Files with 3+ findings
                hotspots.append({
                    'file_path': file_path,
                    'total_findings': data['total_findings'],
                    'unique_vulnerability_types': len(data['unique_rules']),
                    'critical_findings': data['severity_counts']['critical'],
                    'high_findings': data['severity_counts']['high'],
                    'owasp_categories': list(data['owasp_categories']),
                    'cwe_ids': list(data['cwe_ids'])
                })
        
        # Sort by total findings and return top 10
        return sorted(hotspots, key=lambda x: x['total_findings'], reverse=True)[:10]
    
    def _calculate_owasp_compliance(self, findings: List[SecurityFinding]) -> float:
        """Calculate OWASP Top 10 compliance score"""
        owasp_findings = [f for f in findings if f.owasp_category]
        
        if not owasp_findings:
            return 100.0  # Perfect compliance if no OWASP-related findings
        
        # Weight by severity for OWASP findings
        severity_weights = {
            SeverityLevel.CRITICAL: 25,
            SeverityLevel.HIGH: 15,
            SeverityLevel.MEDIUM: 8,
            SeverityLevel.LOW: 3,
            SeverityLevel.INFO: 1
        }
        
        total_weight = sum(severity_weights[finding.severity] for finding in owasp_findings)
        
        # Scale to compliance score (100 weight points = 0% compliance)
        max_expected_weight = 100
        compliance_score = max(0, 100 - (total_weight * 100 / max_expected_weight))
        
        return round(compliance_score, 2)
    
    def _analyze_common_vulnerabilities(self, findings: List[SecurityFinding]) -> List[Dict[str, Any]]:
        """Analyze most common vulnerability types"""
        vulnerability_counts = {}
        
        for finding in findings:
            rule_id = finding.rule_id
            if rule_id not in vulnerability_counts:
                vulnerability_counts[rule_id] = {
                    'rule_id': rule_id,
                    'count': 0,
                    'severity': finding.severity.value,
                    'example_message': finding.message,
                    'files_affected': set()
                }
            
            vulnerability_counts[rule_id]['count'] += 1
            vulnerability_counts[rule_id]['files_affected'].add(finding.file_path)
        
        # Convert to list and add file count
        common_vulns = []
        for vuln_data in vulnerability_counts.values():
            vuln_data['files_affected'] = len(vuln_data['files_affected'])
            common_vulns.append(vuln_data)
        
        # Sort by count and return top 10
        return sorted(common_vulns, key=lambda x: x['count'], reverse=True)[:10]
    
    async def scan_file(self, file_path: str, custom_rules: Optional[List[str]] = None) -> List[SecurityFinding]:
        """Scan a single file for security issues"""
        
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        # Create temporary directory for single file scan
        temp_dir = tempfile.mkdtemp(prefix="prsnl_security_scan_")
        self.temp_dirs.append(temp_dir)
        
        try:
            # Run semgrep on single file
            rulesets = custom_rules or self.default_rulesets
            scan_results = await self._run_semgrep_scan(
                file_path, rulesets, ['**/*'], []
            )
            
            # Parse findings
            findings = []
            raw_findings = scan_results.get('results', [])
            
            for raw_finding in raw_findings:
                finding = self._parse_semgrep_finding(raw_finding, os.path.dirname(file_path))
                if finding:
                    findings.append(finding)
            
            return findings
            
        except Exception as e:
            logger.error(f"Single file security scan failed: {e}")
            raise
    
    async def get_security_summary(self, repo_path: str) -> Dict[str, Any]:
        """Get a quick security summary of repository"""
        try:
            # Run quick scan with limited rulesets
            quick_rulesets = ["p/security-audit", "p/secrets"]
            result = await self.scan_repository(
                repo_path, 
                {'rulesets': quick_rulesets}
            )
            
            return {
                'repository_path': result.repository_path,
                'total_findings': result.total_findings,
                'security_score': result.overall_security_score,
                'critical_findings': result.findings_by_severity.get('critical', 0),
                'high_findings': result.findings_by_severity.get('high', 0),
                'files_with_issues': len(result.high_risk_files),
                'most_common_issue': result.common_vulnerabilities[0]['rule_id'] if result.common_vulnerabilities else None,
                'owasp_compliance': result.owasp_compliance_score
            }
        except Exception as e:
            logger.error(f"Failed to get security summary: {e}")
            return {'error': str(e)}


# Singleton instance
security_scan_service = SecurityScanService()