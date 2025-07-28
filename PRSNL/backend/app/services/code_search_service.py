"""
Code Search Service for PRSNL CodeMirror CLI Integration

Structural code search and transformation using Comby for pattern-based
refactoring opportunities and architecture consistency analysis.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of code patterns"""
    ARCHITECTURAL = "architectural"
    DESIGN_PATTERN = "design_pattern"
    ANTI_PATTERN = "anti_pattern"
    REFACTORING_OPPORTUNITY = "refactoring_opportunity"
    API_USAGE = "api_usage"
    ERROR_HANDLING = "error_handling"
    SECURITY_PATTERN = "security_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"


@dataclass
class CodeMatch:
    """Data class for code search matches"""
    file_path: str
    line_number: int
    column_number: int
    matched_text: str
    context_before: str
    context_after: str
    pattern_name: str
    confidence_score: float


@dataclass
class StructuralPattern:
    """Data class for structural patterns"""
    pattern_id: str
    pattern_name: str
    pattern_type: PatternType
    description: str
    template: str
    replacement_template: Optional[str]
    languages: List[str]
    examples: List[str]
    benefits: List[str]
    difficulty: str  # "easy", "medium", "hard"


@dataclass
class RefactoringOpportunity:
    """Data class for refactoring opportunities"""
    opportunity_id: str
    title: str
    description: str
    pattern_type: PatternType
    file_path: str
    line_range: Tuple[int, int]
    current_code: str
    suggested_code: Optional[str]
    benefits: List[str]
    effort_estimate: str  # "low", "medium", "high"
    risk_level: str  # "low", "medium", "high"


@dataclass
class CodeSearchResult:
    """Complete code search result"""
    repository_path: str
    search_timestamp: datetime
    search_duration_seconds: float
    
    # Pattern matches
    total_matches: int
    matches_by_pattern: Dict[str, int]
    all_matches: List[CodeMatch]
    
    # Structural analysis
    identified_patterns: List[StructuralPattern]
    architecture_insights: Dict[str, Any]
    consistency_violations: List[Dict[str, Any]]
    
    # Refactoring opportunities
    refactoring_opportunities: List[RefactoringOpportunity]
    high_impact_refactorings: List[RefactoringOpportunity]
    
    # Code quality metrics
    pattern_diversity_score: float
    consistency_score: float
    maintainability_score: float
    
    # Language-specific insights
    language_patterns: Dict[str, List[Dict[str, Any]]]
    framework_usage: Dict[str, List[Dict[str, Any]]]


class CodeSearchService:
    """
    Service for structural code search and analysis using Comby.
    
    Provides pattern-based refactoring opportunities, architecture consistency
    analysis, and structural code insights.
    """
    
    def __init__(self):
        self.temp_dirs = []  # Track temporary directories for cleanup
        
        # Predefined structural patterns for common languages
        self.structural_patterns = self._load_structural_patterns()
        
        # Language-specific configurations
        self.language_configs = {
            'python': {
                'file_extensions': ['.py'],
                'comment_patterns': ['#', '"""', "'''"],
                'import_patterns': ['import :[module]', 'from :[module] import :[items]']
            },
            'javascript': {
                'file_extensions': ['.js', '.jsx'],
                'comment_patterns': ['//', '/*'],
                'import_patterns': ['import :[items] from :[module]', 'const :[var] = require(:[module])']
            },
            'typescript': {
                'file_extensions': ['.ts', '.tsx'],
                'comment_patterns': ['//', '/*'],
                'import_patterns': ['import :[items] from :[module]', 'import * as :[alias] from :[module]']
            },
            'java': {
                'file_extensions': ['.java'],
                'comment_patterns': ['//', '/*'],
                'import_patterns': ['import :[package].:[class]']
            },
            'go': {
                'file_extensions': ['.go'],
                'comment_patterns': ['//', '/*'],
                'import_patterns': ['import :[package]', 'import ":[package]"']
            }
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
    
    def _load_structural_patterns(self) -> Dict[str, List[StructuralPattern]]:
        """Load predefined structural patterns for analysis"""
        
        patterns = {
            'python': [
                StructuralPattern(
                    pattern_id="python_singleton",
                    pattern_name="Singleton Pattern",
                    pattern_type=PatternType.DESIGN_PATTERN,
                    description="Singleton pattern implementation",
                    template="class :[class_name]:\n    def __new__(cls):\n        if not hasattr(cls, 'instance'):\n            cls.instance = super(:[class_name], cls).__new__(cls)\n        return cls.instance",
                    replacement_template=None,
                    languages=["python"],
                    examples=["Database connection managers", "Configuration handlers"],
                    benefits=["Controlled instance creation", "Global access point"],
                    difficulty="medium"
                ),
                StructuralPattern(
                    pattern_id="python_context_manager",
                    pattern_name="Context Manager Usage",
                    pattern_type=PatternType.ARCHITECTURAL,
                    description="Context manager usage for resource handling",
                    template="with :[resource] as :[var]:\n    :[body]",
                    replacement_template=None,
                    languages=["python"],
                    examples=["File handling", "Database connections", "Lock management"],
                    benefits=["Automatic resource cleanup", "Exception safety"],
                    difficulty="easy"
                ),
                StructuralPattern(
                    pattern_id="python_nested_loops",
                    pattern_name="Nested Loops Anti-Pattern",
                    pattern_type=PatternType.ANTI_PATTERN,
                    description="Deeply nested loops that may need optimization",
                    template="for :[var1] in :[iter1]:\n    for :[var2] in :[iter2]:\n        for :[var3] in :[iter3]:\n            :[body]",
                    replacement_template="# Consider using itertools, list comprehension, or restructuring",
                    languages=["python"],
                    examples=["O(n³) complexity loops", "Nested data processing"],
                    benefits=["Performance improvement", "Code readability"],
                    difficulty="medium"
                )
            ],
            'javascript': [
                StructuralPattern(
                    pattern_id="js_callback_hell",
                    pattern_name="Callback Hell Anti-Pattern",
                    pattern_type=PatternType.ANTI_PATTERN,
                    description="Deeply nested callback functions",
                    template=":[func1](:[args1], function(:[params1]) {\n    :[func2](:[args2], function(:[params2]) {\n        :[func3](:[args3], function(:[params3]) {\n            :[body]\n        });\n    });\n});",
                    replacement_template="// Consider using Promises or async/await",
                    languages=["javascript", "typescript"],
                    examples=["Nested API calls", "Sequential async operations"],
                    benefits=["Better error handling", "Improved readability"],
                    difficulty="medium"
                ),
                StructuralPattern(
                    pattern_id="js_promise_chain",
                    pattern_name="Promise Chain Pattern",
                    pattern_type=PatternType.ARCHITECTURAL,
                    description="Promise chaining for async operations",
                    template=":[promise]\n.then(:[handler1])\n.then(:[handler2])\n.catch(:[error_handler])",
                    replacement_template=None,
                    languages=["javascript", "typescript"],
                    examples=["API call sequences", "Data transformation pipelines"],
                    benefits=["Async flow control", "Error propagation"],
                    difficulty="easy"
                )
            ],
            'general': [
                StructuralPattern(
                    pattern_id="god_function",
                    pattern_name="God Function Anti-Pattern",
                    pattern_type=PatternType.ANTI_PATTERN,
                    description="Functions that are too long and do too much",
                    template="def :[func_name](:[params]):\n    :[body]",  # Will be refined with line count logic
                    replacement_template="# Consider breaking into smaller functions",
                    languages=["python", "javascript", "java", "go"],
                    examples=["Functions over 50 lines", "Multiple responsibilities"],
                    benefits=["Better testability", "Improved maintainability"],
                    difficulty="medium"
                ),
                StructuralPattern(
                    pattern_id="duplicate_code",
                    pattern_name="Code Duplication Pattern",
                    pattern_type=PatternType.REFACTORING_OPPORTUNITY,
                    description="Similar code blocks that could be extracted",
                    template=":[identical_block]",  # Will be detected via similarity analysis
                    replacement_template="# Extract to shared function or method",
                    languages=["python", "javascript", "java", "go"],
                    examples=["Repeated logic", "Similar error handling"],
                    benefits=["DRY principle", "Easier maintenance"],
                    difficulty="easy"
                )
            ]
        }
        
        return patterns
    
    @observe(name="code_search_full")
    async def search_repository(
        self, 
        repo_path: str,
        search_config: Optional[Dict[str, Any]] = None
    ) -> CodeSearchResult:
        """
        Perform comprehensive structural code search on repository.
        
        Args:
            repo_path: Path to repository to search
            search_config: Optional search configuration
            
        Returns:
            CodeSearchResult with comprehensive structural analysis
        """
        logger.info(f"Starting structural code search for repository: {repo_path}")
        start_time = datetime.utcnow()
        
        try:
            # Validate repository path
            if not os.path.exists(repo_path):
                raise ValueError(f"Repository path does not exist: {repo_path}")
            
            # Setup search configuration
            config = search_config or {}
            languages = config.get('languages', self._detect_languages(repo_path))
            custom_patterns = config.get('custom_patterns', [])
            include_patterns = config.get('include_patterns', ['**/*'])
            exclude_patterns = config.get('exclude_patterns', [
                '**/.git/**', '**/node_modules/**', '**/venv/**', 
                '**/__pycache__/**', '**/build/**', '**/dist/**'
            ])
            
            # Perform pattern searches
            all_matches = []
            matches_by_pattern = {}
            
            # Search for predefined patterns
            for language in languages:
                if language in self.structural_patterns:
                    for pattern in self.structural_patterns[language]:
                        matches = await self._search_pattern(
                            repo_path, pattern, include_patterns, exclude_patterns
                        )
                        all_matches.extend(matches)
                        matches_by_pattern[pattern.pattern_name] = len(matches)
            
            # Search for general patterns
            if 'general' in self.structural_patterns:
                for pattern in self.structural_patterns['general']:
                    matches = await self._search_pattern(
                        repo_path, pattern, include_patterns, exclude_patterns
                    )
                    all_matches.extend(matches)
                    matches_by_pattern[pattern.pattern_name] = len(matches)
            
            # Analyze architecture and consistency
            architecture_insights = await self._analyze_architecture(repo_path, languages)
            consistency_violations = await self._find_consistency_violations(repo_path, all_matches)
            
            # Identify refactoring opportunities
            refactoring_opportunities = await self._identify_refactoring_opportunities(
                repo_path, all_matches, architecture_insights
            )
            
            # Calculate quality metrics
            pattern_diversity_score = self._calculate_pattern_diversity(all_matches)
            consistency_score = self._calculate_consistency_score(consistency_violations)
            maintainability_score = self._calculate_maintainability_score(
                all_matches, refactoring_opportunities
            )
            
            # Language-specific analysis
            language_patterns = await self._analyze_language_patterns(repo_path, languages)
            framework_usage = await self._analyze_framework_usage(repo_path, languages)
            
            # Process results
            search_duration = (datetime.utcnow() - start_time).total_seconds()
            
            return CodeSearchResult(
                repository_path=repo_path,
                search_timestamp=datetime.utcnow(),
                search_duration_seconds=search_duration,
                total_matches=len(all_matches),
                matches_by_pattern=matches_by_pattern,
                all_matches=all_matches,
                identified_patterns=self._get_identified_patterns(languages),
                architecture_insights=architecture_insights,
                consistency_violations=consistency_violations,
                refactoring_opportunities=refactoring_opportunities,
                high_impact_refactorings=[
                    opp for opp in refactoring_opportunities 
                    if opp.effort_estimate == "low" and opp.risk_level == "low"
                ][:10],
                pattern_diversity_score=pattern_diversity_score,
                consistency_score=consistency_score,
                maintainability_score=maintainability_score,
                language_patterns=language_patterns,
                framework_usage=framework_usage
            )
            
        except Exception as e:
            logger.error(f"Structural code search failed for {repo_path}: {e}")
            raise
        finally:
            # Cleanup temporary resources
            self._cleanup_temp_dirs()
    
    def _detect_languages(self, repo_path: str) -> List[str]:
        """Detect programming languages in repository"""
        languages = set()
        
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_ext = os.path.splitext(file)[1].lower()
                for lang, config in self.language_configs.items():
                    if file_ext in config['file_extensions']:
                        languages.add(lang)
                        break
        
        return list(languages)
    
    async def _search_pattern(
        self, 
        repo_path: str, 
        pattern: StructuralPattern,
        include_patterns: List[str],
        exclude_patterns: List[str]
    ) -> List[CodeMatch]:
        """Search for a specific pattern using Comby"""
        
        try:
            # Build comby command
            cmd = [
                'comby',
                '-match', pattern.template,
                '-directory', repo_path,
                '-json'
            ]
            
            # Add language-specific matcher if available
            if len(pattern.languages) == 1:
                lang_matchers = {
                    'python': '.py',
                    'javascript': '.js',
                    'typescript': '.ts',
                    'java': '.java',
                    'go': '.go'
                }
                if pattern.languages[0] in lang_matchers:
                    cmd.extend(['-matcher', lang_matchers[pattern.languages[0]]])
            
            # Add exclude patterns
            for exclude_pattern in exclude_patterns:
                cmd.extend(['-exclude-dir', exclude_pattern.replace('**/', '')])
            
            logger.debug(f"Running comby search for pattern: {pattern.pattern_name}")
            
            # Run comby
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.debug(f"Comby search returned non-zero exit code for pattern {pattern.pattern_name}: {stderr.decode()}")
                return []
            
            # Parse JSON output
            try:
                results = json.loads(stdout.decode())
                matches = []
                
                for result in results:
                    match = self._parse_comby_result(result, pattern)
                    if match:
                        matches.append(match)
                
                logger.debug(f"Found {len(matches)} matches for pattern: {pattern.pattern_name}")
                return matches
                
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse comby JSON output for pattern {pattern.pattern_name}: {e}")
                return []
                
        except Exception as e:
            logger.debug(f"Comby pattern search failed for {pattern.pattern_name}: {e}")
            return []
    
    def _parse_comby_result(self, result: Dict[str, Any], pattern: StructuralPattern) -> Optional[CodeMatch]:
        """Parse a comby search result into our CodeMatch format"""
        
        try:
            # Extract location information
            uri = result.get('uri', '')
            range_info = result.get('range', {})
            start_info = range_info.get('start', {})
            
            line_number = start_info.get('line', 0)
            column_number = start_info.get('column', 0)
            
            # Extract matched text
            matched_text = result.get('matched', '')
            
            # Get surrounding context if available
            context_before = ''
            context_after = ''
            
            # Calculate confidence score based on pattern type and match quality
            confidence_score = self._calculate_match_confidence(matched_text, pattern)
            
            return CodeMatch(
                file_path=uri,
                line_number=line_number,
                column_number=column_number,
                matched_text=matched_text,
                context_before=context_before,
                context_after=context_after,
                pattern_name=pattern.pattern_name,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.debug(f"Error parsing comby result: {e}")
            return None
    
    def _calculate_match_confidence(self, matched_text: str, pattern: StructuralPattern) -> float:
        """Calculate confidence score for a pattern match"""
        
        # Base confidence based on pattern type
        base_confidence = {
            PatternType.DESIGN_PATTERN: 0.8,
            PatternType.ARCHITECTURAL: 0.7,
            PatternType.ANTI_PATTERN: 0.9,
            PatternType.REFACTORING_OPPORTUNITY: 0.6,
            PatternType.API_USAGE: 0.8,
            PatternType.ERROR_HANDLING: 0.7,
            PatternType.SECURITY_PATTERN: 0.9,
            PatternType.PERFORMANCE_PATTERN: 0.7
        }.get(pattern.pattern_type, 0.5)
        
        # Adjust based on match length and complexity
        length_factor = min(1.0, len(matched_text) / 100)  # Longer matches are more reliable
        
        # Adjust based on context (simple heuristic)
        context_factor = 1.0
        if 'TODO' in matched_text or 'FIXME' in matched_text:
            context_factor = 0.9  # Slightly less confident for temporary code
        
        final_confidence = base_confidence * (0.7 + 0.3 * length_factor) * context_factor
        return round(min(1.0, final_confidence), 2)
    
    async def _analyze_architecture(self, repo_path: str, languages: List[str]) -> Dict[str, Any]:
        """Analyze architectural patterns and structure"""
        
        insights = {
            'directory_structure': self._analyze_directory_structure(repo_path),
            'module_organization': {},
            'dependency_patterns': {},
            'layering_violations': []
        }
        
        # Language-specific architectural analysis
        for language in languages:
            if language == 'python':
                insights['module_organization'][language] = await self._analyze_python_modules(repo_path)
            elif language in ['javascript', 'typescript']:
                insights['module_organization'][language] = await self._analyze_js_modules(repo_path)
        
        return insights
    
    def _analyze_directory_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze directory structure patterns"""
        
        structure_analysis = {
            'total_directories': 0,
            'max_depth': 0,
            'common_patterns': [],
            'potential_issues': []
        }
        
        # Walk directory tree
        for root, dirs, files in os.walk(repo_path):
            structure_analysis['total_directories'] += 1
            
            # Calculate depth
            depth = root.replace(repo_path, '').count(os.sep)
            structure_analysis['max_depth'] = max(structure_analysis['max_depth'], depth)
            
            # Check for common patterns
            if any(pattern in root.lower() for pattern in ['test', 'spec']):
                if 'test_directories' not in structure_analysis:
                    structure_analysis['test_directories'] = 0
                structure_analysis['test_directories'] += 1
            
            # Check for potential issues
            if depth > 8:  # Very deep nesting
                structure_analysis['potential_issues'].append({
                    'type': 'deep_nesting',
                    'path': root,
                    'depth': depth
                })
        
        return structure_analysis
    
    async def _analyze_python_modules(self, repo_path: str) -> Dict[str, Any]:
        """Analyze Python module organization"""
        
        module_analysis = {
            'total_modules': 0,
            'package_structure': [],
            'import_patterns': {},
            'circular_imports': []
        }
        
        # Find all Python files
        python_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        module_analysis['total_modules'] = len(python_files)
        
        # Analyze import patterns (simplified)
        import_counts = {}
        for file_path in python_files[:10]:  # Limit to first 10 files for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line in lines[:20]:  # Only check first 20 lines
                        line = line.strip()
                        if line.startswith('import ') or line.startswith('from '):
                            import_type = 'absolute' if line.startswith('import ') else 'relative'
                            import_counts[import_type] = import_counts.get(import_type, 0) + 1
            except Exception:
                continue
        
        module_analysis['import_patterns'] = import_counts
        
        return module_analysis
    
    async def _analyze_js_modules(self, repo_path: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript module organization"""
        
        module_analysis = {
            'total_modules': 0,
            'module_types': {},
            'import_patterns': {}
        }
        
        # Find all JS/TS files
        js_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    js_files.append(os.path.join(root, file))
        
        module_analysis['total_modules'] = len(js_files)
        
        # Basic analysis of module patterns
        for file_path in js_files[:10]:  # Limit for performance
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check module system
                    if 'export ' in content or 'import ' in content:
                        module_analysis['module_types']['es6'] = module_analysis['module_types'].get('es6', 0) + 1
                    elif 'module.exports' in content or 'require(' in content:
                        module_analysis['module_types']['commonjs'] = module_analysis['module_types'].get('commonjs', 0) + 1
                        
            except Exception:
                continue
        
        return module_analysis
    
    async def _find_consistency_violations(
        self, 
        repo_path: str, 
        matches: List[CodeMatch]
    ) -> List[Dict[str, Any]]:
        """Find consistency violations in code patterns"""
        
        violations = []
        
        # Group matches by pattern type
        pattern_groups = {}
        for match in matches:
            pattern_name = match.pattern_name
            if pattern_name not in pattern_groups:
                pattern_groups[pattern_name] = []
            pattern_groups[pattern_name].append(match)
        
        # Check for inconsistent usage of the same pattern
        for pattern_name, pattern_matches in pattern_groups.items():
            if len(pattern_matches) > 1:
                # Simple consistency check - look for variations in similar code
                unique_implementations = set(match.matched_text.strip() for match in pattern_matches)
                
                if len(unique_implementations) > len(pattern_matches) * 0.7:  # More than 70% different
                    violations.append({
                        'type': 'inconsistent_pattern_usage',
                        'pattern_name': pattern_name,
                        'occurrences': len(pattern_matches),
                        'unique_implementations': len(unique_implementations),
                        'severity': 'medium',
                        'files_affected': list(set(match.file_path for match in pattern_matches))
                    })
        
        return violations
    
    async def _identify_refactoring_opportunities(
        self, 
        repo_path: str, 
        matches: List[CodeMatch], 
        architecture_insights: Dict[str, Any]
    ) -> List[RefactoringOpportunity]:
        """Identify refactoring opportunities based on pattern analysis"""
        
        opportunities = []
        
        # Look for anti-patterns that could be refactored
        anti_pattern_matches = [
            match for match in matches 
            if any(pattern.pattern_type == PatternType.ANTI_PATTERN 
                  for patterns in self.structural_patterns.values() 
                  for pattern in patterns 
                  if pattern.pattern_name == match.pattern_name)
        ]
        
        for match in anti_pattern_matches:
            # Find the corresponding pattern definition
            pattern_def = None
            for patterns in self.structural_patterns.values():
                for pattern in patterns:
                    if pattern.pattern_name == match.pattern_name:
                        pattern_def = pattern
                        break
                if pattern_def:
                    break
            
            if pattern_def and pattern_def.replacement_template:
                opportunity = RefactoringOpportunity(
                    opportunity_id=f"refactor_{match.file_path}_{match.line_number}",
                    title=f"Refactor {pattern_def.pattern_name}",
                    description=f"Replace {pattern_def.pattern_name} with better implementation",
                    pattern_type=pattern_def.pattern_type,
                    file_path=match.file_path,
                    line_range=(match.line_number, match.line_number + match.matched_text.count('\n')),
                    current_code=match.matched_text,
                    suggested_code=pattern_def.replacement_template,
                    benefits=pattern_def.benefits,
                    effort_estimate=self._estimate_refactoring_effort(match, pattern_def),
                    risk_level=self._estimate_refactoring_risk(match, pattern_def)
                )
                opportunities.append(opportunity)
        
        # Look for code duplication opportunities
        duplicate_opportunities = await self._find_duplication_opportunities(repo_path, matches)
        opportunities.extend(duplicate_opportunities)
        
        return opportunities[:20]  # Limit to top 20 opportunities
    
    def _estimate_refactoring_effort(self, match: CodeMatch, pattern: StructuralPattern) -> str:
        """Estimate effort required for refactoring"""
        
        # Base effort on pattern difficulty and code size
        difficulty_weights = {"easy": 1, "medium": 2, "hard": 3}
        base_effort = difficulty_weights.get(pattern.difficulty, 2)
        
        # Adjust for code size
        code_lines = match.matched_text.count('\n') + 1
        if code_lines > 50:
            base_effort += 1
        elif code_lines < 10:
            base_effort = max(1, base_effort - 1)
        
        # Map to effort level
        if base_effort <= 1:
            return "low"
        elif base_effort <= 2:
            return "medium"
        else:
            return "high"
    
    def _estimate_refactoring_risk(self, match: CodeMatch, pattern: StructuralPattern) -> str:
        """Estimate risk level for refactoring"""
        
        # Base risk on pattern type
        risk_levels = {
            PatternType.ANTI_PATTERN: "low",
            PatternType.REFACTORING_OPPORTUNITY: "low",
            PatternType.ARCHITECTURAL: "medium",
            PatternType.DESIGN_PATTERN: "medium",
            PatternType.SECURITY_PATTERN: "high"
        }
        
        base_risk = risk_levels.get(pattern.pattern_type, "medium")
        
        # Adjust for code complexity
        if match.matched_text.count('\n') > 30:  # Large code block
            if base_risk == "low":
                base_risk = "medium"
            elif base_risk == "medium":
                base_risk = "high"
        
        return base_risk
    
    async def _find_duplication_opportunities(
        self, 
        repo_path: str, 
        matches: List[CodeMatch]
    ) -> List[RefactoringOpportunity]:
        """Find code duplication refactoring opportunities"""
        
        opportunities = []
        
        # Simple duplication detection based on similar matched text
        text_groups = {}
        for match in matches:
            # Normalize text for comparison
            normalized_text = ' '.join(match.matched_text.split())
            if len(normalized_text) > 50:  # Only consider substantial code blocks
                if normalized_text not in text_groups:
                    text_groups[normalized_text] = []
                text_groups[normalized_text].append(match)
        
        # Find groups with multiple matches (potential duplicates)
        for text, group_matches in text_groups.items():
            if len(group_matches) >= 2:  # Found duplicates
                opportunity = RefactoringOpportunity(
                    opportunity_id=f"duplicate_{hash(text)}",
                    title="Extract Duplicate Code",
                    description=f"Extract {len(group_matches)} similar code blocks into a shared function",
                    pattern_type=PatternType.REFACTORING_OPPORTUNITY,
                    file_path=group_matches[0].file_path,
                    line_range=(group_matches[0].line_number, group_matches[0].line_number + 10),
                    current_code=group_matches[0].matched_text,
                    suggested_code="# Extract to shared function or method",
                    benefits=["Reduced code duplication", "Easier maintenance", "DRY principle"],
                    effort_estimate="medium",
                    risk_level="low"
                )
                opportunities.append(opportunity)
        
        return opportunities[:5]  # Limit to top 5 duplication opportunities
    
    def _calculate_pattern_diversity(self, matches: List[CodeMatch]) -> float:
        """Calculate pattern diversity score"""
        if not matches:
            return 0.0
        
        unique_patterns = len(set(match.pattern_name for match in matches))
        total_matches = len(matches)
        
        # Diversity score based on unique patterns vs total matches
        diversity_score = unique_patterns / max(1, total_matches) * 100
        return round(min(100.0, diversity_score), 2)
    
    def _calculate_consistency_score(self, violations: List[Dict[str, Any]]) -> float:
        """Calculate consistency score based on violations"""
        if not violations:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {"high": 3, "medium": 2, "low": 1}
        total_weight = sum(severity_weights.get(v.get('severity', 'medium'), 2) for v in violations)
        
        # Scale to 0-100 (lower weight = higher score)
        max_expected_weight = 20  # Assume 20 weighted violations = 0 score
        consistency_score = max(0, 100 - (total_weight * 100 / max_expected_weight))
        
        return round(consistency_score, 2)
    
    def _calculate_maintainability_score(
        self, 
        matches: List[CodeMatch], 
        opportunities: List[RefactoringOpportunity]
    ) -> float:
        """Calculate maintainability score"""
        
        # Start with base score
        base_score = 80.0
        
        # Reduce score for anti-patterns
        anti_pattern_count = sum(1 for match in matches if 'anti-pattern' in match.pattern_name.lower())
        base_score -= anti_pattern_count * 2
        
        # Reduce score for high-effort refactoring opportunities
        high_effort_opportunities = sum(1 for opp in opportunities if opp.effort_estimate == "high")
        base_score -= high_effort_opportunities * 3
        
        # Increase score for good patterns
        good_pattern_count = sum(1 for match in matches if any(
            keyword in match.pattern_name.lower() 
            for keyword in ['context manager', 'promise', 'pattern']
        ))
        base_score += good_pattern_count * 1
        
        return round(max(0.0, min(100.0, base_score)), 2)
    
    def _get_identified_patterns(self, languages: List[str]) -> List[StructuralPattern]:
        """Get all identified patterns for the languages"""
        patterns = []
        
        for language in languages:
            if language in self.structural_patterns:
                patterns.extend(self.structural_patterns[language])
        
        if 'general' in self.structural_patterns:
            patterns.extend(self.structural_patterns['general'])
        
        return patterns
    
    async def _analyze_language_patterns(self, repo_path: str, languages: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze language-specific patterns"""
        
        language_patterns = {}
        
        for language in languages:
            patterns = []
            
            if language == 'python':
                patterns.extend(await self._analyze_python_specific_patterns(repo_path))
            elif language in ['javascript', 'typescript']:
                patterns.extend(await self._analyze_js_specific_patterns(repo_path))
            
            language_patterns[language] = patterns
        
        return language_patterns
    
    async def _analyze_python_specific_patterns(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze Python-specific patterns"""
        
        patterns = []
        
        # Look for common Python patterns
        python_patterns = [
            {
                'name': 'List Comprehensions',
                'pattern': '[:[expr] for :[var] in :[iterable]]',
                'description': 'Usage of list comprehensions for concise code'
            },
            {
                'name': 'Dictionary Comprehensions', 
                'pattern': '{:[key]: :[value] for :[var] in :[iterable]}',
                'description': 'Usage of dictionary comprehensions'
            },
            {
                'name': 'Generator Expressions',
                'pattern': '(:[expr] for :[var] in :[iterable])',
                'description': 'Memory-efficient generator expressions'
            }
        ]
        
        # Search for each pattern (simplified implementation)
        for pattern_info in python_patterns:
            # This would use comby to search, but simplified here
            patterns.append({
                'name': pattern_info['name'],
                'description': pattern_info['description'],
                'occurrences': 0,  # Would be populated by actual search
                'files': []
            })
        
        return patterns
    
    async def _analyze_js_specific_patterns(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript/TypeScript-specific patterns"""
        
        patterns = []
        
        # Look for common JS patterns
        js_patterns = [
            {
                'name': 'Arrow Functions',
                'pattern': ':[var] => :[body]',
                'description': 'Usage of ES6 arrow functions'
            },
            {
                'name': 'Destructuring Assignment',
                'pattern': 'const {:[vars]} = :[object]',
                'description': 'ES6 destructuring for cleaner code'
            },
            {
                'name': 'Template Literals',
                'pattern': '`:[template]`',
                'description': 'String interpolation with template literals'
            }
        ]
        
        # Search for each pattern (simplified implementation)
        for pattern_info in js_patterns:
            patterns.append({
                'name': pattern_info['name'],
                'description': pattern_info['description'],
                'occurrences': 0,  # Would be populated by actual search
                'files': []
            })
        
        return patterns
    
    async def _analyze_framework_usage(self, repo_path: str, languages: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze framework usage patterns"""
        
        framework_usage = {}
        
        for language in languages:
            frameworks = []
            
            if language == 'python':
                frameworks.extend(await self._detect_python_frameworks(repo_path))
            elif language in ['javascript', 'typescript']:
                frameworks.extend(await self._detect_js_frameworks(repo_path))
            
            framework_usage[language] = frameworks
        
        return framework_usage
    
    async def _detect_python_frameworks(self, repo_path: str) -> List[Dict[str, Any]]:
        """Detect Python frameworks in use"""
        
        frameworks = []
        
        # Check for common framework imports/patterns
        framework_patterns = {
            'Django': ['from django', 'import django'],
            'Flask': ['from flask', 'import flask'],
            'FastAPI': ['from fastapi', 'import fastapi'],
            'SQLAlchemy': ['from sqlalchemy', 'import sqlalchemy']
        }
        
        # Simple detection by looking for imports (would be more sophisticated in practice)
        for framework_name, patterns in framework_patterns.items():
            frameworks.append({
                'name': framework_name,
                'detected': False,  # Would be set by actual detection
                'usage_patterns': [],
                'version': 'unknown'
            })
        
        return frameworks
    
    async def _detect_js_frameworks(self, repo_path: str) -> List[Dict[str, Any]]:
        """Detect JavaScript/TypeScript frameworks in use"""
        
        frameworks = []
        
        # Check for common framework patterns
        framework_patterns = {
            'React': ['import React', 'from \'react\''],
            'Vue': ['import Vue', 'from \'vue\''],
            'Angular': ['@angular', '@Component'],
            'Express': ['import express', 'require(\'express\')']
        }
        
        # Simple detection (would be more sophisticated in practice)
        for framework_name, patterns in framework_patterns.items():
            frameworks.append({
                'name': framework_name,
                'detected': False,  # Would be set by actual detection
                'usage_patterns': [],
                'version': 'unknown'
            })
        
        return frameworks
    
    async def search_custom_pattern(
        self, 
        repo_path: str, 
        pattern_template: str, 
        pattern_name: str = "Custom Pattern"
    ) -> List[CodeMatch]:
        """Search for a custom pattern in the repository"""
        
        custom_pattern = StructuralPattern(
            pattern_id="custom",
            pattern_name=pattern_name,
            pattern_type=PatternType.ARCHITECTURAL,
            description="Custom search pattern",
            template=pattern_template,
            replacement_template=None,
            languages=["general"],
            examples=[],
            benefits=[],
            difficulty="unknown"
        )
        
        return await self._search_pattern(repo_path, custom_pattern, ['**/*'], [])
    
    async def get_search_summary(self, repo_path: str) -> Dict[str, Any]:
        """Get a quick structural search summary of repository"""
        try:
            # Quick search with limited patterns
            result = await self.search_repository(repo_path, {
                'languages': self._detect_languages(repo_path)[:2]  # Limit to 2 languages
            })
            
            return {
                'repository_path': result.repository_path,
                'total_matches': result.total_matches,
                'pattern_diversity_score': result.pattern_diversity_score,
                'consistency_score': result.consistency_score,
                'maintainability_score': result.maintainability_score,
                'languages_detected': list(result.language_patterns.keys()),
                'refactoring_opportunities': len(result.refactoring_opportunities),
                'high_impact_refactorings': len(result.high_impact_refactorings),
                'top_patterns': dict(list(result.matches_by_pattern.items())[:5])
            }
        except Exception as e:
            logger.error(f"Failed to get search summary: {e}")
            return {'error': str(e)}


# Singleton instance
code_search_service = CodeSearchService()