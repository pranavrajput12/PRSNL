"""
Git Analysis Service for PRSNL CodeMirror CLI Integration

Deep repository analysis using GitPython for commit history, author patterns,
branch analysis, and development velocity insights.
"""

import asyncio
import logging
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

import git
from git import Repo, InvalidGitRepositoryError
from app.core.langfuse_wrapper import observe  # Safe wrapper to handle get_tracer error
logger = logging.getLogger(__name__)


@dataclass
class CommitData:
    """Data class for commit information"""
    sha: str
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    message: str
    timestamp: datetime
    files_changed: List[str]
    lines_added: int
    lines_deleted: int
    is_merge: bool


@dataclass
class AuthorStats:
    """Statistics for a repository author"""
    name: str
    email: str
    total_commits: int
    lines_added: int
    lines_deleted: int
    files_touched: int
    first_commit: datetime
    last_commit: datetime
    favorite_extensions: List[str]


@dataclass
class GitAnalysisResult:
    """Complete git analysis result"""
    repository_url: str
    analysis_timestamp: datetime
    total_commits: int
    total_authors: int
    repository_age_days: int
    primary_language: str
    
    # Commit patterns
    commits_by_hour: Dict[int, int]
    commits_by_day: Dict[str, int]
    commits_by_month: Dict[str, int]
    
    # Author analysis
    top_authors: List[AuthorStats]
    author_collaboration: Dict[str, List[str]]
    
    # File patterns
    most_changed_files: List[Dict[str, Any]]
    file_extensions: Dict[str, int]
    hotspot_files: List[Dict[str, Any]]
    
    # Development patterns
    average_commit_size: float
    merge_frequency: float
    branch_patterns: Dict[str, Any]
    release_patterns: List[Dict[str, Any]]
    
    # Code quality indicators
    commit_message_quality: Dict[str, Any]
    refactoring_patterns: List[Dict[str, Any]]
    technical_debt_indicators: List[Dict[str, Any]]


class GitAnalysisService:
    """
    Service for deep Git repository analysis using GitPython.
    
    Provides comprehensive insights into repository history, development patterns,
    author collaboration, and code evolution.
    """
    
    def __init__(self):
        self.temp_dirs = []  # Track temporary directories for cleanup
        
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
    
    @observe(name="git_analysis_full")
    async def analyze_repository(
        self, 
        repo_url: str, 
        analysis_depth: str = "standard",
        max_commits: Optional[int] = None
    ) -> GitAnalysisResult:
        """
        Perform comprehensive Git repository analysis.
        
        Args:
            repo_url: Git repository URL or local path
            analysis_depth: Level of analysis ('quick', 'standard', 'deep')
            max_commits: Maximum number of commits to analyze (None for all)
            
        Returns:
            GitAnalysisResult with comprehensive analysis data
        """
        logger.info(f"Starting Git analysis for repository: {repo_url}")
        start_time = datetime.utcnow()
        
        try:
            # Clone or access repository
            repo = await self._get_repository(repo_url)
            
            # Set analysis limits based on depth
            commit_limit = self._get_commit_limit(analysis_depth, max_commits)
            
            # Extract commit data
            commits = await self._extract_commits(repo, limit=commit_limit)
            
            if not commits:
                raise ValueError("No commits found in repository")
            
            # Perform analysis based on depth
            analysis_result = await self._perform_analysis(
                repo, commits, repo_url, analysis_depth
            )
            
            analysis_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Git analysis completed in {analysis_time:.2f} seconds")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Git analysis failed for {repo_url}: {e}")
            raise
        finally:
            # Cleanup temporary resources
            self._cleanup_temp_dirs()
    
    async def _get_repository(self, repo_url: str) -> Repo:
        """Get repository object, cloning if necessary"""
        
        # Check if it's a local path
        if os.path.exists(repo_url) and os.path.isdir(repo_url):
            try:
                return Repo(repo_url)
            except InvalidGitRepositoryError:
                raise ValueError(f"Local path {repo_url} is not a Git repository")
        
        # Remote repository - need to clone
        temp_dir = tempfile.mkdtemp(prefix="prsnl_git_analysis_")
        self.temp_dirs.append(temp_dir)
        
        try:
            logger.info(f"Cloning repository {repo_url} to {temp_dir}")
            repo = Repo.clone_from(repo_url, temp_dir, depth=1000)  # Shallow clone
            return repo
        except Exception as e:
            logger.error(f"Failed to clone repository {repo_url}: {e}")
            raise ValueError(f"Could not access repository: {e}")
    
    def _get_commit_limit(self, depth: str, max_commits: Optional[int]) -> Optional[int]:
        """Determine commit limit based on analysis depth"""
        depth_limits = {
            "quick": 100,
            "standard": 1000,
            "deep": None  # No limit
        }
        
        depth_limit = depth_limits.get(depth, 1000)
        
        if max_commits is not None:
            return min(max_commits, depth_limit) if depth_limit else max_commits
        
        return depth_limit
    
    @observe(name="git_extract_commits")
    async def _extract_commits(self, repo: Repo, limit: Optional[int] = None) -> List[CommitData]:
        """Extract commit data from repository"""
        commits = []
        
        try:
            # Get commits from all branches for comprehensive analysis
            commit_iter = repo.iter_commits('--all', max_count=limit)
            
            for commit in commit_iter:
                try:
                    # Get file changes
                    files_changed = []
                    lines_added = 0
                    lines_deleted = 0
                    
                    # Calculate diff stats
                    if commit.parents:  # Not the initial commit
                        try:
                            diff = commit.parents[0].diff(commit)
                            for diff_item in diff:
                                if diff_item.a_path:
                                    files_changed.append(diff_item.a_path)
                                if diff_item.b_path and diff_item.b_path not in files_changed:
                                    files_changed.append(diff_item.b_path)
                            
                            # Get line changes from stats
                            stats = commit.stats.total
                            lines_added = stats.get('insertions', 0)
                            lines_deleted = stats.get('deletions', 0)
                            
                        except Exception as e:
                            logger.debug(f"Could not calculate diff for commit {commit.hexsha}: {e}")
                    
                    commit_data = CommitData(
                        sha=commit.hexsha,
                        author_name=commit.author.name,
                        author_email=commit.author.email,
                        committer_name=commit.committer.name,
                        committer_email=commit.committer.email,
                        message=commit.message.strip(),
                        timestamp=commit.committed_datetime,
                        files_changed=files_changed,
                        lines_added=lines_added,
                        lines_deleted=lines_deleted,
                        is_merge=len(commit.parents) > 1
                    )
                    
                    commits.append(commit_data)
                    
                except Exception as e:
                    logger.debug(f"Error processing commit {commit.hexsha}: {e}")
                    continue
            
            logger.info(f"Extracted {len(commits)} commits for analysis")
            return commits
            
        except Exception as e:
            logger.error(f"Failed to extract commits: {e}")
            return []
    
    @observe(name="git_perform_analysis")
    async def _perform_analysis(
        self, 
        repo: Repo, 
        commits: List[CommitData], 
        repo_url: str, 
        depth: str
    ) -> GitAnalysisResult:
        """Perform comprehensive analysis on commit data"""
        
        if not commits:
            raise ValueError("No commits available for analysis")
        
        # Basic repository stats
        total_commits = len(commits)
        unique_authors = len(set(commit.author_email for commit in commits))
        
        # Calculate repository age
        oldest_commit = min(commits, key=lambda c: c.timestamp)
        newest_commit = max(commits, key=lambda c: c.timestamp)
        repo_age_days = (newest_commit.timestamp - oldest_commit.timestamp).days
        
        # Time-based patterns
        commits_by_hour = self._analyze_commit_timing_hour(commits)
        commits_by_day = self._analyze_commit_timing_day(commits)
        commits_by_month = self._analyze_commit_timing_month(commits)
        
        # Author analysis
        author_stats = self._analyze_authors(commits)
        top_authors = sorted(author_stats.values(), key=lambda a: a.total_commits, reverse=True)[:10]
        author_collaboration = self._analyze_author_collaboration(commits)
        
        # File analysis
        most_changed_files = self._analyze_file_changes(commits)
        file_extensions = self._analyze_file_extensions(commits)
        hotspot_files = self._identify_hotspot_files(commits)
        
        # Development patterns
        average_commit_size = self._calculate_average_commit_size(commits)
        merge_frequency = self._calculate_merge_frequency(commits)
        branch_patterns = await self._analyze_branch_patterns(repo) if depth != "quick" else {}
        release_patterns = self._analyze_release_patterns(commits) if depth == "deep" else []
        
        # Code quality indicators
        commit_message_quality = self._analyze_commit_message_quality(commits)
        refactoring_patterns = self._identify_refactoring_patterns(commits) if depth != "quick" else []
        technical_debt_indicators = self._identify_technical_debt(commits) if depth == "deep" else []
        
        # Determine primary language
        primary_language = self._determine_primary_language(file_extensions)
        
        return GitAnalysisResult(
            repository_url=repo_url,
            analysis_timestamp=datetime.utcnow(),
            total_commits=total_commits,
            total_authors=unique_authors,
            repository_age_days=repo_age_days,
            primary_language=primary_language,
            commits_by_hour=commits_by_hour,
            commits_by_day=commits_by_day,
            commits_by_month=commits_by_month,
            top_authors=top_authors,
            author_collaboration=author_collaboration,
            most_changed_files=most_changed_files,
            file_extensions=file_extensions,
            hotspot_files=hotspot_files,
            average_commit_size=average_commit_size,
            merge_frequency=merge_frequency,
            branch_patterns=branch_patterns,
            release_patterns=release_patterns,
            commit_message_quality=commit_message_quality,
            refactoring_patterns=refactoring_patterns,
            technical_debt_indicators=technical_debt_indicators
        )
    
    def _analyze_commit_timing_hour(self, commits: List[CommitData]) -> Dict[int, int]:
        """Analyze commit patterns by hour of day"""
        hour_counts = defaultdict(int)
        for commit in commits:
            hour = commit.timestamp.hour
            hour_counts[hour] += 1
        return dict(hour_counts)
    
    def _analyze_commit_timing_day(self, commits: List[CommitData]) -> Dict[str, int]:
        """Analyze commit patterns by day of week"""
        day_counts = defaultdict(int)
        for commit in commits:
            day_name = commit.timestamp.strftime('%A')
            day_counts[day_name] += 1
        return dict(day_counts)
    
    def _analyze_commit_timing_month(self, commits: List[CommitData]) -> Dict[str, int]:
        """Analyze commit patterns by month"""
        month_counts = defaultdict(int)
        for commit in commits:
            month_key = commit.timestamp.strftime('%Y-%m')
            month_counts[month_key] += 1
        return dict(month_counts)
    
    def _analyze_authors(self, commits: List[CommitData]) -> Dict[str, AuthorStats]:
        """Analyze author statistics and patterns"""
        author_data = defaultdict(lambda: {
            'commits': [],
            'files': set(),
            'lines_added': 0,
            'lines_deleted': 0
        })
        
        # Collect data per author
        for commit in commits:
            key = f"{commit.author_name} <{commit.author_email}>"
            author_data[key]['commits'].append(commit)
            author_data[key]['files'].update(commit.files_changed)
            author_data[key]['lines_added'] += commit.lines_added
            author_data[key]['lines_deleted'] += commit.lines_deleted
        
        # Create AuthorStats objects
        author_stats = {}
        for author_key, data in author_data.items():
            commits_list = data['commits']
            
            # Get file extensions this author works with
            extensions = []
            for commit in commits_list:
                for file_path in commit.files_changed:
                    if '.' in file_path:
                        ext = file_path.split('.')[-1].lower()
                        extensions.append(ext)
            
            favorite_extensions = [ext for ext, _ in Counter(extensions).most_common(5)]
            
            author_stats[author_key] = AuthorStats(
                name=commits_list[0].author_name,
                email=commits_list[0].author_email,
                total_commits=len(commits_list),
                lines_added=data['lines_added'],
                lines_deleted=data['lines_deleted'],
                files_touched=len(data['files']),
                first_commit=min(c.timestamp for c in commits_list),
                last_commit=max(c.timestamp for c in commits_list),
                favorite_extensions=favorite_extensions
            )
        
        return author_stats
    
    def _analyze_author_collaboration(self, commits: List[CommitData]) -> Dict[str, List[str]]:
        """Analyze which authors frequently modify the same files"""
        file_authors = defaultdict(set)
        
        # Map files to authors who modified them
        for commit in commits:
            author = f"{commit.author_name} <{commit.author_email}>"
            for file_path in commit.files_changed:
                file_authors[file_path].add(author)
        
        # Find collaboration patterns
        collaborations = defaultdict(set)
        for file_path, authors in file_authors.items():
            if len(authors) > 1:
                author_list = list(authors)
                for i, author1 in enumerate(author_list):
                    for author2 in author_list[i+1:]:
                        collaborations[author1].add(author2)
                        collaborations[author2].add(author1)
        
        # Convert to lists and limit to top collaborators
        return {
            author: list(collaborators)[:5] 
            for author, collaborators in collaborations.items()
        }
    
    def _analyze_file_changes(self, commits: List[CommitData]) -> List[Dict[str, Any]]:
        """Analyze which files change most frequently"""
        file_changes = defaultdict(int)
        
        for commit in commits:
            for file_path in commit.files_changed:
                file_changes[file_path] += 1
        
        # Return top 20 most changed files
        most_changed = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return [
            {
                'file_path': file_path,
                'change_count': count,
                'change_frequency': count / len(commits)
            }
            for file_path, count in most_changed
        ]
    
    def _analyze_file_extensions(self, commits: List[CommitData]) -> Dict[str, int]:
        """Analyze file extensions to understand technology stack"""
        extensions = defaultdict(int)
        
        for commit in commits:
            for file_path in commit.files_changed:
                if '.' in file_path and not file_path.startswith('.'):
                    ext = file_path.split('.')[-1].lower()
                    extensions[ext] += 1
        
        return dict(extensions)
    
    def _identify_hotspot_files(self, commits: List[CommitData]) -> List[Dict[str, Any]]:
        """Identify files that are changed frequently and have large changes"""
        file_stats = defaultdict(lambda: {'changes': 0, 'lines_added': 0, 'lines_deleted': 0})
        
        for commit in commits:
            for file_path in commit.files_changed:
                file_stats[file_path]['changes'] += 1
                file_stats[file_path]['lines_added'] += commit.lines_added / len(commit.files_changed) if commit.files_changed else 0
                file_stats[file_path]['lines_deleted'] += commit.lines_deleted / len(commit.files_changed) if commit.files_changed else 0
        
        # Calculate hotspot score (frequency * average change size)
        hotspots = []
        for file_path, stats in file_stats.items():
            if stats['changes'] > 1:  # Only files changed multiple times
                avg_change_size = (stats['lines_added'] + stats['lines_deleted']) / stats['changes']
                hotspot_score = stats['changes'] * avg_change_size
                
                hotspots.append({
                    'file_path': file_path,
                    'change_count': stats['changes'],
                    'avg_change_size': avg_change_size,
                    'hotspot_score': hotspot_score
                })
        
        # Return top 15 hotspots
        return sorted(hotspots, key=lambda x: x['hotspot_score'], reverse=True)[:15]
    
    def _calculate_average_commit_size(self, commits: List[CommitData]) -> float:
        """Calculate average commit size in lines changed"""
        if not commits:
            return 0.0
        
        total_lines = sum(commit.lines_added + commit.lines_deleted for commit in commits)
        return total_lines / len(commits)
    
    def _calculate_merge_frequency(self, commits: List[CommitData]) -> float:
        """Calculate frequency of merge commits"""
        if not commits:
            return 0.0
        
        merge_commits = sum(1 for commit in commits if commit.is_merge)
        return merge_commits / len(commits)
    
    async def _analyze_branch_patterns(self, repo: Repo) -> Dict[str, Any]:
        """Analyze branching patterns and strategies"""
        try:
            branches = list(repo.branches)
            remote_branches = []
            
            # Get remote branches if available
            try:
                for remote in repo.remotes:
                    remote_branches.extend([ref.name for ref in remote.refs])
            except Exception:
                pass
            
            return {
                'local_branches': len(branches),
                'remote_branches': len(remote_branches),
                'branch_names': [branch.name for branch in branches[:10]],  # Top 10
                'active_branches': len([b for b in branches if (datetime.now() - b.commit.committed_datetime).days < 30])
            }
        except Exception as e:
            logger.debug(f"Could not analyze branch patterns: {e}")
            return {}
    
    def _analyze_release_patterns(self, commits: List[CommitData]) -> List[Dict[str, Any]]:
        """Identify potential release patterns from commit messages"""
        release_keywords = ['release', 'version', 'tag', 'v1.', 'v2.', 'bump', 'deploy']
        release_commits = []
        
        for commit in commits:
            message_lower = commit.message.lower()
            if any(keyword in message_lower for keyword in release_keywords):
                release_commits.append({
                    'sha': commit.sha,
                    'message': commit.message,
                    'timestamp': commit.timestamp.isoformat(),
                    'author': commit.author_name
                })
        
        return release_commits[:20]  # Return last 20 potential releases
    
    def _analyze_commit_message_quality(self, commits: List[CommitData]) -> Dict[str, Any]:
        """Analyze commit message quality and patterns"""
        if not commits:
            return {}
        
        total_commits = len(commits)
        
        # Analyze message characteristics
        short_messages = sum(1 for c in commits if len(c.message) < 10)
        long_messages = sum(1 for c in commits if len(c.message) > 100)
        conventional_commits = sum(1 for c in commits if self._is_conventional_commit(c.message))
        
        # Common words in commit messages
        words = []
        for commit in commits:
            words.extend(commit.message.lower().split())
        
        common_words = [word for word, _ in Counter(words).most_common(10)]
        
        return {
            'total_commits': total_commits,
            'short_messages_percent': (short_messages / total_commits) * 100,
            'long_messages_percent': (long_messages / total_commits) * 100,
            'conventional_commits_percent': (conventional_commits / total_commits) * 100,
            'average_message_length': sum(len(c.message) for c in commits) / total_commits,
            'common_words': common_words
        }
    
    def _is_conventional_commit(self, message: str) -> bool:
        """Check if commit message follows conventional commit format"""
        conventional_prefixes = ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:']
        return any(message.lower().startswith(prefix) for prefix in conventional_prefixes)
    
    def _identify_refactoring_patterns(self, commits: List[CommitData]) -> List[Dict[str, Any]]:
        """Identify potential refactoring commits"""
        refactoring_keywords = ['refactor', 'cleanup', 'reorganize', 'restructure', 'extract', 'rename']
        refactoring_commits = []
        
        for commit in commits:
            message_lower = commit.message.lower()
            if any(keyword in message_lower for keyword in refactoring_keywords):
                refactoring_commits.append({
                    'sha': commit.sha,
                    'message': commit.message,
                    'timestamp': commit.timestamp.isoformat(),
                    'files_changed': len(commit.files_changed),
                    'lines_changed': commit.lines_added + commit.lines_deleted
                })
        
        return refactoring_commits[:15]  # Return last 15 refactoring commits
    
    def _identify_technical_debt(self, commits: List[CommitData]) -> List[Dict[str, Any]]:
        """Identify indicators of technical debt from commit patterns"""
        debt_indicators = []
        
        # Look for commits with debt-related keywords
        debt_keywords = ['hack', 'todo', 'fixme', 'temporary', 'workaround', 'quick fix']
        
        for commit in commits:
            message_lower = commit.message.lower()
            found_keywords = [keyword for keyword in debt_keywords if keyword in message_lower]
            
            if found_keywords:
                debt_indicators.append({
                    'sha': commit.sha,
                    'message': commit.message,
                    'timestamp': commit.timestamp.isoformat(),
                    'debt_keywords': found_keywords,
                    'severity': 'high' if 'hack' in found_keywords else 'medium'
                })
        
        return debt_indicators[:10]  # Return top 10 debt indicators
    
    def _determine_primary_language(self, file_extensions: Dict[str, int]) -> str:
        """Determine primary programming language from file extensions"""
        language_map = {
            'py': 'Python',
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'java': 'Java',
            'cpp': 'C++',
            'c': 'C',
            'cs': 'C#',
            'go': 'Go',
            'rs': 'Rust',
            'php': 'PHP',
            'rb': 'Ruby',
            'swift': 'Swift',
            'kt': 'Kotlin',
            'scala': 'Scala'
        }
        
        if not file_extensions:
            return 'Unknown'
        
        # Find most common programming language extension
        prog_extensions = {ext: count for ext, count in file_extensions.items() if ext in language_map}
        
        if prog_extensions:
            most_common_ext = max(prog_extensions, key=prog_extensions.get)
            return language_map[most_common_ext]
        
        return 'Unknown'
    
    async def get_repository_summary(self, repo_url: str) -> Dict[str, Any]:
        """Get a quick summary of repository statistics"""
        try:
            result = await self.analyze_repository(repo_url, analysis_depth="quick", max_commits=50)
            
            return {
                'repository_url': result.repository_url,
                'total_commits': result.total_commits,
                'total_authors': result.total_authors,
                'repository_age_days': result.repository_age_days,
                'primary_language': result.primary_language,
                'top_authors': [asdict(author) for author in result.top_authors[:3]],
                'most_active_hour': max(result.commits_by_hour, key=result.commits_by_hour.get) if result.commits_by_hour else None,
                'file_extensions': dict(list(result.file_extensions.items())[:5])
            }
        except Exception as e:
            logger.error(f"Failed to get repository summary: {e}")
            return {'error': str(e)}


# Singleton instance
git_analysis_service = GitAnalysisService()