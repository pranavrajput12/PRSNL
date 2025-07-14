"""
Repository analysis engine for PRSNL CodeMirror CLI.
"""

import fnmatch
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import aiofiles
import aiohttp
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound


class RepositoryAnalyzer:
    """Analyzes repositories using AI and pattern detection."""
    
    def __init__(self, config, console):
        self.config = config
        self.console = console
        self.supported_languages = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.svelte': 'Svelte',
            '.vue': 'Vue.js',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C Header',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.sql': 'SQL',
            '.md': 'Markdown',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.toml': 'TOML',
            '.sh': 'Shell Script'
        }
    
    async def analyze_repository(self, repo_path: Path, depth: str = 'standard', 
                               include_patterns: bool = True, include_insights: bool = True) -> Dict[str, Any]:
        """Perform comprehensive repository analysis."""
        repo_info = self.get_repository_info(repo_path)
        
        # Collect files for analysis
        files = self._collect_files(repo_path)
        
        # Basic analysis
        result = {
            'repository': repo_info,
            'analysis_depth': depth,
            'timestamp': datetime.utcnow().isoformat(),
            'stats': self._calculate_stats(files),
            'languages': self._analyze_languages(files),
            'structure': self._analyze_structure(repo_path, files),
            'dependencies': self._analyze_dependencies(repo_path),
            'git_info': self._get_git_info(repo_path)
        }
        
        # Pattern detection (if requested)
        if include_patterns:
            result['patterns'] = await self._detect_patterns(files, depth)
        
        # AI insights (if requested and configured)
        if include_insights and (self.config.openai_key or self.config.prsnl_url):
            result['insights'] = await self._generate_insights(result, depth)
        
        # Cache results
        self._cache_results(repo_info['name'], result)
        
        return result
    
    def get_repository_info(self, repo_path: Path) -> Dict[str, Any]:
        """Get basic repository information."""
        git_info = self._get_git_info(repo_path)
        
        return {
            'name': repo_path.name,
            'path': str(repo_path),
            'git': git_info,
            'size': self._get_directory_size(repo_path),
            'cached_analyses': self._get_cached_analyses(repo_path.name)
        }
    
    def _collect_files(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Collect all relevant files for analysis."""
        files = []
        
        for file_path in repo_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip files that match exclude patterns
            relative_path = file_path.relative_to(repo_path)
            if self._should_exclude_file(relative_path):
                continue
            
            # Skip files that are too large
            try:
                size = file_path.stat().st_size
                if size > self.config.max_file_size:
                    continue
            except (OSError, IOError):
                continue
            
            # Only include files with supported extensions
            if file_path.suffix.lower() not in self.config.include_extensions:
                continue
            
            files.append({
                'path': str(relative_path),
                'absolute_path': str(file_path),
                'size': size,
                'extension': file_path.suffix.lower(),
                'language': self.supported_languages.get(file_path.suffix.lower(), 'Unknown')
            })
        
        return files
    
    def _should_exclude_file(self, relative_path: Path) -> bool:
        """Check if file should be excluded based on patterns."""
        path_str = str(relative_path)
        
        for pattern in self.config.exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
        
        return False
    
    def _calculate_stats(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate repository statistics."""
        total_size = sum(f['size'] for f in files)
        total_lines = 0
        
        # Count lines for text files
        for file_info in files:
            if file_info['extension'] in ['.py', '.js', '.ts', '.jsx', '.tsx', '.svelte', '.html', '.css']:
                try:
                    with open(file_info['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += sum(1 for _ in f)
                except (IOError, OSError):
                    pass
        
        return {
            'total_files': len(files),
            'total_size': total_size,
            'total_lines': total_lines,
            'files_analyzed': len(files)
        }
    
    def _analyze_languages(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze language distribution."""
        language_stats = {}
        
        for file_info in files:
            lang = file_info['language']
            if lang not in language_stats:
                language_stats[lang] = {
                    'name': lang,
                    'file_count': 0,
                    'total_size': 0,
                    'line_count': 0
                }
            
            language_stats[lang]['file_count'] += 1
            language_stats[lang]['total_size'] += file_info['size']
            
            # Count lines for this file
            if file_info['extension'] in ['.py', '.js', '.ts', '.jsx', '.tsx', '.svelte', '.html', '.css']:
                try:
                    with open(file_info['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
                        language_stats[lang]['line_count'] += sum(1 for _ in f)
                except (IOError, OSError):
                    pass
        
        # Sort by file count
        return sorted(language_stats.values(), key=lambda x: x['file_count'], reverse=True)
    
    def _analyze_structure(self, repo_path: Path, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze repository structure."""
        directories = set()
        
        for file_info in files:
            parts = Path(file_info['path']).parts
            for i in range(1, len(parts)):
                directories.add('/'.join(parts[:i]))
        
        # Find common directories
        common_dirs = []
        for dir_name in ['src', 'lib', 'components', 'pages', 'routes', 'api', 'tests', 'docs']:
            if any(dir_name in d for d in directories):
                common_dirs.append(dir_name)
        
        return {
            'total_directories': len(directories),
            'common_directories': common_dirs,
            'max_depth': max(len(Path(f['path']).parts) for f in files) if files else 0
        }
    
    def _analyze_dependencies(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze project dependencies."""
        dependencies = {}
        
        # Python dependencies
        requirements_files = ['requirements.txt', 'pyproject.toml', 'Pipfile']
        for req_file in requirements_files:
            req_path = repo_path / req_file
            if req_path.exists():
                dependencies['python'] = self._parse_python_dependencies(req_path)
                break
        
        # JavaScript dependencies
        package_json = repo_path / 'package.json'
        if package_json.exists():
            dependencies['javascript'] = self._parse_js_dependencies(package_json)
        
        # Go dependencies
        go_mod = repo_path / 'go.mod'
        if go_mod.exists():
            dependencies['go'] = self._parse_go_dependencies(go_mod)
        
        return dependencies
    
    def _parse_python_dependencies(self, req_path: Path) -> List[str]:
        """Parse Python dependencies."""
        try:
            with open(req_path, 'r') as f:
                if req_path.name == 'requirements.txt':
                    return [line.strip().split('==')[0].split('>=')[0] 
                           for line in f if line.strip() and not line.startswith('#')]
                else:
                    # Basic parsing for pyproject.toml or Pipfile
                    return []
        except (IOError, OSError):
            return []
    
    def _parse_js_dependencies(self, package_json: Path) -> List[str]:
        """Parse JavaScript dependencies."""
        try:
            with open(package_json, 'r') as f:
                data = json.load(f)
                deps = []
                deps.extend(data.get('dependencies', {}).keys())
                deps.extend(data.get('devDependencies', {}).keys())
                return deps
        except (IOError, OSError, json.JSONDecodeError):
            return []
    
    def _parse_go_dependencies(self, go_mod: Path) -> List[str]:
        """Parse Go dependencies."""
        try:
            with open(go_mod, 'r') as f:
                deps = []
                for line in f:
                    line = line.strip()
                    if line.startswith('require'):
                        continue
                    if ' v' in line and not line.startswith('//'):
                        deps.append(line.split()[0])
                return deps
        except (IOError, OSError):
            return []
    
    def _get_git_info(self, repo_path: Path) -> Dict[str, Any]:
        """Get Git repository information."""
        git_info = {}
        
        try:
            # Get current branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                git_info['branch'] = result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        try:
            # Get remote URL
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                git_info['remote'] = result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        try:
            # Get last commit
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%H %s'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                commit_info = result.stdout.strip().split(' ', 1)
                git_info['last_commit'] = {
                    'hash': commit_info[0][:8],
                    'message': commit_info[1] if len(commit_info) > 1 else ''
                }
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        return git_info
    
    def _get_directory_size(self, repo_path: Path) -> int:
        """Calculate total directory size."""
        total_size = 0
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except (OSError, IOError):
                    pass
        return total_size
    
    async def _detect_patterns(self, files: List[Dict[str, Any]], depth: str) -> List[Dict[str, Any]]:
        """Detect code patterns and architectural decisions."""
        patterns = []
        
        # Framework detection
        frameworks = self._detect_frameworks(files)
        for framework in frameworks:
            patterns.append({
                'type': 'framework',
                'name': framework['name'],
                'confidence': framework['confidence'],
                'description': f"Detected {framework['name']} framework usage",
                'files': framework['files']
            })
        
        # Architecture patterns
        arch_patterns = self._detect_architecture_patterns(files)
        patterns.extend(arch_patterns)
        
        # Code quality patterns
        if depth in ['standard', 'deep']:
            quality_patterns = await self._detect_quality_patterns(files)
            patterns.extend(quality_patterns)
        
        return patterns
    
    def _detect_frameworks(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect web frameworks and libraries."""
        frameworks = []
        
        # Check for specific files/patterns
        framework_indicators = {
            'Svelte': ['.svelte', 'svelte.config.js'],
            'React': ['.jsx', '.tsx', 'package.json'],
            'Vue.js': ['.vue'],
            'FastAPI': ['main.py', 'requirements.txt'],
            'Django': ['settings.py', 'manage.py'],
            'Flask': ['app.py', 'requirements.txt'],
            'Next.js': ['next.config.js', 'pages/'],
            'Express.js': ['package.json']
        }
        
        for framework, indicators in framework_indicators.items():
            confidence = 0
            matched_files = []
            
            for indicator in indicators:
                if indicator.startswith('.'):
                    # Extension check
                    matching = [f for f in files if f['extension'] == indicator]
                    if matching:
                        confidence += 0.3
                        matched_files.extend([f['path'] for f in matching[:3]])
                else:
                    # File name check
                    matching = [f for f in files if indicator in f['path']]
                    if matching:
                        confidence += 0.4
                        matched_files.extend([f['path'] for f in matching[:3]])
            
            if confidence > 0.3:
                frameworks.append({
                    'name': framework,
                    'confidence': min(confidence, 1.0),
                    'files': matched_files[:5]
                })
        
        return frameworks
    
    def _detect_architecture_patterns(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect architectural patterns."""
        patterns = []
        
        # Check for common directory structures
        dirs = set()
        for f in files:
            parts = Path(f['path']).parts
            if len(parts) > 1:
                dirs.add(parts[0])
        
        # MVC pattern
        if {'models', 'views', 'controllers'}.issubset(dirs):
            patterns.append({
                'type': 'architecture',
                'name': 'MVC Pattern',
                'confidence': 0.8,
                'description': 'Model-View-Controller architecture detected',
                'evidence': ['models/', 'views/', 'controllers/']
            })
        
        # Microservices pattern
        service_indicators = ['services', 'api', 'handlers', 'endpoints']
        if len([d for d in dirs if any(ind in d for ind in service_indicators)]) >= 2:
            patterns.append({
                'type': 'architecture',
                'name': 'Microservices',
                'confidence': 0.6,
                'description': 'Microservices architecture patterns detected',
                'evidence': [d for d in dirs if any(ind in d for ind in service_indicators)]
            })
        
        return patterns
    
    async def _detect_quality_patterns(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect code quality patterns and issues."""
        patterns = []
        
        # Check for test files
        test_files = [f for f in files if any(t in f['path'].lower() for t in ['test', 'spec'])]
        if test_files:
            test_ratio = len(test_files) / len(files)
            patterns.append({
                'type': 'quality',
                'name': 'Test Coverage',
                'confidence': 1.0,
                'description': f'Test files found ({len(test_files)} files, {test_ratio:.1%} ratio)',
                'metric': test_ratio
            })
        
        # Check for configuration files
        config_files = [f for f in files if any(c in f['path'].lower() 
                                              for c in ['config', '.env', 'settings'])]
        if config_files:
            patterns.append({
                'type': 'quality',
                'name': 'Configuration Management',
                'confidence': 0.8,
                'description': f'Configuration files detected ({len(config_files)} files)',
                'files': [f['path'] for f in config_files[:5]]
            })
        
        return patterns
    
    async def _generate_insights(self, analysis_result: Dict[str, Any], depth: str) -> List[Dict[str, Any]]:
        """Generate AI-powered insights."""
        insights = []
        
        # Use OpenAI API if available
        if self.config.openai_key:
            ai_insights = await self._generate_openai_insights(analysis_result, depth)
            insights.extend(ai_insights)
        
        # Use PRSNL API if available
        elif self.config.prsnl_url and self.config.prsnl_token:
            prsnl_insights = await self._generate_prsnl_insights(analysis_result, depth)
            insights.extend(prsnl_insights)
        
        # Fallback to rule-based insights
        else:
            rule_insights = self._generate_rule_based_insights(analysis_result)
            insights.extend(rule_insights)
        
        return insights
    
    async def _generate_openai_insights(self, analysis_result: Dict[str, Any], depth: str) -> List[Dict[str, Any]]:
        """Generate insights using OpenAI API."""
        # Placeholder for OpenAI integration
        return []
    
    async def _generate_prsnl_insights(self, analysis_result: Dict[str, Any], depth: str) -> List[Dict[str, Any]]:
        """Generate insights using PRSNL API."""
        # Placeholder for PRSNL API integration
        return []
    
    def _generate_rule_based_insights(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights using rule-based analysis."""
        insights = []
        
        # Language diversity insight
        languages = analysis_result.get('languages', [])
        if len(languages) > 5:
            insights.append({
                'type': 'code_quality',
                'title': 'High Language Diversity',
                'description': f'Repository uses {len(languages)} different languages. Consider consolidating to reduce complexity.',
                'severity': 'medium',
                'confidence_score': 0.7,
                'recommendation': 'Review if all languages are necessary or if some can be consolidated.'
            })
        
        # Large file count insight
        stats = analysis_result.get('stats', {})
        if stats.get('total_files', 0) > 1000:
            insights.append({
                'type': 'performance_optimization',
                'title': 'Large Number of Files',
                'description': f'Repository contains {stats["total_files"]} files. This may impact performance.',
                'severity': 'low',
                'confidence_score': 0.8,
                'recommendation': 'Consider organizing files into modules or removing unused files.'
            })
        
        # Missing tests insight
        patterns = analysis_result.get('patterns', [])
        test_pattern = next((p for p in patterns if p.get('name') == 'Test Coverage'), None)
        if not test_pattern:
            insights.append({
                'type': 'code_quality',
                'title': 'No Test Files Detected',
                'description': 'No test files were found in the repository.',
                'severity': 'high',
                'confidence_score': 0.9,
                'recommendation': 'Add unit tests to improve code reliability and maintainability.'
            })
        
        return insights
    
    def _cache_results(self, repo_name: str, result: Dict[str, Any]):
        """Cache analysis results."""
        cache_path = self.config.get_cache_path(repo_name)
        try:
            with open(cache_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to cache results: {e}[/yellow]")
    
    def _get_cached_analyses(self, repo_name: str) -> List[Dict[str, Any]]:
        """Get cached analyses for a repository."""
        cache_path = self.config.get_cache_path(repo_name)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return [json.load(f)]
            except Exception:
                pass
        return []