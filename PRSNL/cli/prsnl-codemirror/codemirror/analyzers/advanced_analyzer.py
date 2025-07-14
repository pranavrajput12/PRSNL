"""
Advanced Analysis Tools Integration

Integrates GitPython, PyDriller, Semgrep, and Comby for deep code analysis.
"""

import logging
import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

import git
from pydriller import Repository
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

logger = logging.getLogger(__name__)
console = Console()


class GitHistoryAnalyzer:
    """Analyzes git history using GitPython and PyDriller."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        
    def analyze_commit_patterns(self, days: int = 90) -> Dict[str, Any]:
        """Analyze commit patterns over time."""
        since = datetime.now() - timedelta(days=days)
        
        patterns = {
            'commit_frequency': defaultdict(int),
            'author_contributions': defaultdict(int),
            'file_churn': defaultdict(int),
            'commit_messages': [],
            'hotspots': defaultdict(int),
            'refactoring_commits': []
        }
        
        for commit in Repository(str(self.repo_path), since=since).traverse_commits():
            # Track commit frequency by day
            day = commit.committer_date.date()
            patterns['commit_frequency'][str(day)] += 1
            
            # Track author contributions
            patterns['author_contributions'][commit.author.name] += 1
            
            # Analyze commit message for patterns
            msg_lower = commit.msg.lower()
            patterns['commit_messages'].append({
                'hash': commit.hash[:8],
                'message': commit.msg.split('\n')[0][:80],
                'is_fix': 'fix' in msg_lower,
                'is_feature': any(word in msg_lower for word in ['feat', 'add', 'new']),
                'is_refactor': 'refactor' in msg_lower
            })
            
            if 'refactor' in msg_lower:
                patterns['refactoring_commits'].append(commit.hash[:8])
            
            # Track file modifications
            for mod in commit.modified_files:
                if mod.filename:
                    patterns['file_churn'][mod.filename] += 1
                    patterns['hotspots'][mod.filename] += mod.added_lines + mod.deleted_lines
        
        # Get top hotspots
        patterns['top_hotspots'] = sorted(
            patterns['hotspots'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return patterns
    
    def analyze_code_ownership(self) -> Dict[str, Any]:
        """Analyze code ownership by file and directory."""
        ownership = defaultdict(lambda: defaultdict(int))
        
        for commit in Repository(str(self.repo_path)).traverse_commits():
            for mod in commit.modified_files:
                if mod.filename:
                    ownership[mod.filename][commit.author.name] += 1
        
        # Calculate primary owner for each file
        file_owners = {}
        for file, authors in ownership.items():
            primary_owner = max(authors.items(), key=lambda x: x[1])
            file_owners[file] = {
                'primary_owner': primary_owner[0],
                'ownership_percentage': primary_owner[1] / sum(authors.values()) * 100,
                'contributors': list(authors.keys())
            }
        
        return file_owners


class SemgrepAnalyzer:
    """Runs Semgrep security and code quality analysis."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        
    def run_security_scan(self) -> Dict[str, Any]:
        """Run Semgrep security scan."""
        try:
            # Run semgrep with auto config for security issues
            result = subprocess.run(
                ['semgrep', '--config=auto', '--json', '--metrics=off'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                findings = json.loads(result.stdout)
                return self._process_semgrep_results(findings)
            else:
                logger.error(f"Semgrep failed: {result.stderr}")
                return {'error': result.stderr}
                
        except FileNotFoundError:
            logger.warning("Semgrep not found. Install with: pip install semgrep")
            return {'error': 'Semgrep not installed'}
        except json.JSONDecodeError:
            logger.error("Failed to parse Semgrep output")
            return {'error': 'Invalid Semgrep output'}
    
    def run_pattern_scan(self, patterns: List[str]) -> Dict[str, Any]:
        """Run custom pattern scans."""
        results = {}
        
        for pattern in patterns:
            try:
                result = subprocess.run(
                    ['semgrep', '--pattern', pattern, '--json', '--metrics=off'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    findings = json.loads(result.stdout)
                    results[pattern] = self._process_semgrep_results(findings)
                    
            except Exception as e:
                logger.error(f"Pattern scan failed for {pattern}: {e}")
                
        return results
    
    def _process_semgrep_results(self, findings: Dict) -> Dict[str, Any]:
        """Process Semgrep findings into structured format."""
        processed = {
            'total_findings': len(findings.get('results', [])),
            'by_severity': defaultdict(int),
            'by_category': defaultdict(int),
            'findings': []
        }
        
        for finding in findings.get('results', []):
            severity = finding.get('extra', {}).get('severity', 'unknown')
            category = finding.get('check_id', '').split('.')[0]
            
            processed['by_severity'][severity] += 1
            processed['by_category'][category] += 1
            
            processed['findings'].append({
                'check_id': finding.get('check_id'),
                'path': finding.get('path'),
                'line': finding.get('start', {}).get('line'),
                'message': finding.get('extra', {}).get('message', ''),
                'severity': severity
            })
        
        return processed


class CombyTransformAnalyzer:
    """Uses Comby for pattern matching and transformation analysis."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        
    def find_patterns(self, pattern_templates: Dict[str, str]) -> Dict[str, Any]:
        """Find code patterns using Comby templates."""
        results = {}
        
        for name, template in pattern_templates.items():
            try:
                # Write template to temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
                    f.write(template)
                    template_file = f.name
                
                # Run comby
                result = subprocess.run(
                    ['comby', '-templates', template_file, '-d', str(self.repo_path), '-json-lines'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    matches = []
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            matches.append(json.loads(line))
                    results[name] = matches
                    
                Path(template_file).unlink()
                
            except FileNotFoundError:
                logger.warning("Comby not found. Install from: https://comby.dev/docs/get-started")
                results[name] = {'error': 'Comby not installed'}
            except Exception as e:
                logger.error(f"Comby pattern search failed: {e}")
                results[name] = {'error': str(e)}
                
        return results


class AdvancedAnalyzer:
    """Orchestrates all advanced analysis tools."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.git_analyzer = GitHistoryAnalyzer(repo_path)
        self.semgrep_analyzer = SemgrepAnalyzer(repo_path)
        self.comby_analyzer = CombyTransformAnalyzer(repo_path)
        
    async def run_full_analysis(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive analysis using all tools."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'repository': str(self.repo_path),
            'analyses': {}
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Git history analysis
            if config.get('git_history', True):
                task = progress.add_task("Analyzing git history...", total=None)
                try:
                    results['analyses']['git_history'] = {
                        'commit_patterns': self.git_analyzer.analyze_commit_patterns(),
                        'code_ownership': self.git_analyzer.analyze_code_ownership()
                    }
                except Exception as e:
                    logger.error(f"Git history analysis failed: {e}")
                    results['analyses']['git_history'] = {'error': str(e)}
                progress.remove_task(task)
            
            # Security analysis
            if config.get('security_scan', True):
                task = progress.add_task("Running security scan...", total=None)
                results['analyses']['security'] = self.semgrep_analyzer.run_security_scan()
                progress.remove_task(task)
            
            # Pattern detection
            if config.get('patterns') and isinstance(config['patterns'], dict):
                task = progress.add_task("Detecting code patterns...", total=None)
                results['analyses']['patterns'] = self.comby_analyzer.find_patterns(
                    config['patterns']
                )
                progress.remove_task(task)
            
            # Custom Semgrep patterns
            if config.get('custom_patterns'):
                task = progress.add_task("Running custom pattern scans...", total=None)
                results['analyses']['custom_patterns'] = self.semgrep_analyzer.run_pattern_scan(
                    config['custom_patterns']
                )
                progress.remove_task(task)
        
        return results
    
    def generate_insights(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable insights from analysis results."""
        insights = []
        
        # Git history insights
        if 'git_history' in analysis_results.get('analyses', {}):
            history = analysis_results['analyses']['git_history']
            
            if 'commit_patterns' in history:
                patterns = history['commit_patterns']
                
                # Identify hotspots
                if patterns.get('top_hotspots'):
                    insights.append({
                        'type': 'hotspot',
                        'severity': 'medium',
                        'title': 'Code Hotspots Detected',
                        'description': f"Top {len(patterns['top_hotspots'])} files with high change frequency",
                        'files': [f[0] for f in patterns['top_hotspots'][:5]],
                        'recommendation': 'Consider refactoring frequently changed files'
                    })
                
                # Analyze refactoring commits
                if len(patterns.get('refactoring_commits', [])) > 5:
                    insights.append({
                        'type': 'refactoring',
                        'severity': 'low',
                        'title': 'Active Refactoring',
                        'description': f"Found {len(patterns['refactoring_commits'])} refactoring commits",
                        'recommendation': 'Good practice! Continue systematic refactoring'
                    })
        
        # Security insights
        if 'security' in analysis_results.get('analyses', {}):
            security = analysis_results['analyses']['security']
            
            if security.get('total_findings', 0) > 0:
                high_severity = security.get('by_severity', {}).get('HIGH', 0)
                if high_severity > 0:
                    insights.append({
                        'type': 'security',
                        'severity': 'high',
                        'title': 'Security Vulnerabilities Found',
                        'description': f"Found {high_severity} high-severity security issues",
                        'recommendation': 'Address high-severity issues immediately'
                    })
        
        return insights


# Pattern templates for common code issues
DEFAULT_COMBY_PATTERNS = {
    'unused_variables': '''
[rule]
match = "let :[var] = :[value];\\n:[rest]"
where = ":[rest]" != ":[var]"
message = "Potentially unused variable"
''',
    'console_logs': '''
[rule]
match = "console.log(:[args])"
message = "Console.log found - consider removing in production"
''',
    'todo_comments': '''
[rule]
match = "// TODO: :[comment]"
message = "TODO comment found"
'''
}