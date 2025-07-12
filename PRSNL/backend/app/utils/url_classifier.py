"""
URL Classification Utilities for Auto-Detection of Development Content

This module provides intelligent URL pattern recognition to automatically
classify development-related links and extract metadata.
"""

import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

class URLClassifier:
    """Classifier for detecting and categorizing development-related URLs."""
    
    # GitHub platform patterns with content type detection
    GITHUB_REPO_PATTERNS = [
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/?$',  # Main repo page
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/tree/(.+)',  # Branch/folder view
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/releases',  # Releases page
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/issues',  # Issues page
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/pull',  # Pull requests
    ]
    
    GITHUB_DOCUMENT_PATTERNS = [
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/blob/(.+)\.md',  # Markdown files
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/blob/(.+)\.rst',  # RestructuredText
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/blob/(.+)\.txt',  # Text files
        r'github\.com/([\w\-\.]+)/([\w\-\.]+)/wiki',  # Wiki pages
        r'raw\.githubusercontent\.com/([\w\-\.]+)/([\w\-\.]+)/(.+)\.md',  # Raw markdown
    ]
    
    GITHUB_GIST_PATTERNS = [
        r'gist\.github\.com/([\w\-\.]+)/([\w\-\.]+)',  # Gists
    ]
    
    STACKOVERFLOW_PATTERNS = [
        r'stackoverflow\.com/questions/',
        r'serverfault\.com/questions/',
        r'superuser\.com/questions/',
        r'stackexchange\.com/',
        r'askubuntu\.com/questions/'
    ]
    
    DOCUMENTATION_PATTERNS = [
        r'docs\.python\.org',
        r'developer\.mozilla\.org',
        r'docs\.microsoft\.com',
        r'docs\.aws\.amazon\.com',
        r'kubernetes\.io/docs',
        r'docs\.docker\.com',
        r'reactjs\.org/docs',
        r'vuejs\.org/guide',
        r'angular\.io/docs',
        r'flask\.palletsprojects\.com',
        r'djangoproject\.com/en/',
        r'nodejs\.org/en/docs',
        r'go\.dev/doc',
        r'rust-lang\.org/learn',
        r'docs\.rs/',
        r'doc\.rust-lang\.org',
        r'docs\.oracle\.com/javase',
        r'spring\.io/guides',
        r'learn\.microsoft\.com',
        r'cloud\.google\.com/docs',
        r'docs\.gitlab\.com',
        r'atlassian\.com/git/tutorials',
        r'git-scm\.com/docs',
        r'nginx\.org/en/docs',
        r'apache\.org/docs',
        r'postgresql\.org/docs',
        r'mongodb\.com/docs',
        r'redis\.io/documentation'
    ]
    
    TUTORIAL_PATTERNS = [
        r'freecodecamp\.org',
        r'codecademy\.com',
        r'w3schools\.com',
        r'tutorialspoint\.com',
        r'geeksforgeeks\.org',
        r'javatpoint\.com',
        r'programiz\.com',
        r'realpython\.com',
        r'digitalocean\.com/community/tutorials',
        r'medium\.com.*programming',
        r'dev\.to',
        r'hackernoon\.com'
    ]
    
    # Language detection patterns
    LANGUAGE_PATTERNS = {
        'python': [r'python', r'django', r'flask', r'fastapi', r'pytorch', r'tensorflow'],
        'javascript': [r'javascript', r'js', r'node', r'react', r'vue', r'angular', r'express'],
        'typescript': [r'typescript', r'ts'],
        'java': [r'java', r'spring', r'hibernate', r'maven', r'gradle'],
        'go': [r'golang', r'\bgo\b', r'gin', r'fiber'],
        'rust': [r'rust', r'cargo', r'rustc'],
        'cpp': [r'c\+\+', r'cpp', r'cmake'],
        'c': [r'\bc\b', r'gcc'],
        'php': [r'php', r'laravel', r'symfony', r'composer'],
        'ruby': [r'ruby', r'rails', r'gem'],
        'swift': [r'swift', r'ios', r'xcode'],
        'kotlin': [r'kotlin', r'android'],
        'dart': [r'dart', r'flutter'],
        'scala': [r'scala', r'akka'],
        'elixir': [r'elixir', r'phoenix'],
        'haskell': [r'haskell'],
        'clojure': [r'clojure'],
        'r': [r'\br\b', r'rstudio'],
        'matlab': [r'matlab'],
        'sql': [r'sql', r'mysql', r'postgresql', r'sqlite', r'mongodb'],
        'shell': [r'bash', r'shell', r'zsh', r'fish'],
        'powershell': [r'powershell', r'pwsh'],
        'dockerfile': [r'docker', r'dockerfile', r'container'],
        'yaml': [r'yaml', r'yml', r'kubernetes', r'k8s'],
        'terraform': [r'terraform', r'tf'],
        'ansible': [r'ansible'],
        'html': [r'html', r'css', r'scss', r'sass'],
        'css': [r'css', r'scss', r'sass', r'tailwind']
    }
    
    # Category patterns
    CATEGORY_PATTERNS = {
        'Frontend': [
            r'react', r'vue', r'angular', r'frontend', r'ui', r'ux', 
            r'css', r'html', r'javascript', r'typescript', r'sass', r'tailwind'
        ],
        'Backend': [
            r'api', r'server', r'backend', r'database', r'sql', 
            r'django', r'flask', r'express', r'spring', r'gin'
        ],
        'DevOps': [
            r'docker', r'kubernetes', r'k8s', r'ci/cd', r'jenkins', 
            r'gitlab-ci', r'github-actions', r'terraform', r'ansible', r'aws', r'azure', r'gcp'
        ],
        'Mobile': [
            r'android', r'ios', r'flutter', r'react-native', 
            r'swift', r'kotlin', r'dart', r'mobile'
        ],
        'AI/ML': [
            r'machine-learning', r'ml', r'ai', r'artificial-intelligence',
            r'tensorflow', r'pytorch', r'scikit-learn', r'pandas', r'numpy'
        ],
        'Data Science': [
            r'data-science', r'analytics', r'pandas', r'numpy', 
            r'jupyter', r'matplotlib', r'seaborn', r'plotly'
        ],
        'Game Development': [
            r'unity', r'unreal', r'game-dev', r'gamedev', 
            r'c\+\+', r'c#', r'lua'
        ],
        'Security': [
            r'security', r'cybersecurity', r'penetration-testing',
            r'vulnerability', r'encryption', r'authentication'
        ]
    }

    @classmethod
    def classify_url(cls, url: str) -> Dict[str, any]:
        """
        Classify a URL and extract metadata for simplified permalink system.
        
        Args:
            url: The URL to classify
            
        Returns:
            Dictionary containing classification results with simplified categories
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()
        full_url = url.lower()
        
        result = {
            'is_development': False,
            'content_type': 'auto',
            'category': 'ideas',  # Default category for new system
            'platform': None,
            'programming_language': None,
            'project_category': None,
            'difficulty_level': None,
            'is_career_related': False,
            'metadata': {}
        }
        
        # Determine simplified category first
        result['category'] = cls._classify_simplified_category(full_url, domain, path)
        
        # Check for GitHub content first (most specific)
        github_info = cls._classify_github_content(url)
        if github_info:
            result['is_development'] = True
            result['content_type'] = github_info['github_type']  # github_repo or github_document
            result['platform'] = 'github'
            
            # Extract programming language
            result['programming_language'] = cls._detect_language(full_url, path)
            
            # Determine project category based on GitHub type
            if github_info['github_type'] == 'github_document':
                result['project_category'] = 'Documentation'
            else:
                result['project_category'] = cls._detect_category(full_url, path) or 'Repository'
            
            # Detect difficulty (basic heuristics)
            result['difficulty_level'] = cls._detect_difficulty(full_url, path)
            
            # Check if career-related
            result['is_career_related'] = cls._is_career_related(full_url, path)
            
            # Store GitHub-specific metadata
            result['metadata'] = {
                'github': github_info,
                'general': cls._extract_metadata(url, 'github')
            }
            
        # Check if it's other development-related URLs
        elif cls._is_development_url(full_url, domain, path):
            result['is_development'] = True
            result['content_type'] = 'development'
            
            # Determine platform
            result['platform'] = cls._detect_platform(full_url, domain)
            
            # Extract programming language
            result['programming_language'] = cls._detect_language(full_url, path)
            
            # Determine project category
            result['project_category'] = cls._detect_category(full_url, path)
            
            # Detect difficulty (basic heuristics)
            result['difficulty_level'] = cls._detect_difficulty(full_url, path)
            
            # Check if career-related
            result['is_career_related'] = cls._is_career_related(full_url, path)
            
            # Extract additional metadata
            result['metadata'] = cls._extract_metadata(url, result['platform'])
        
        return result
    
    @classmethod
    def _classify_simplified_category(cls, url: str, domain: str, path: str) -> str:
        """
        Classify URL into one of four simplified categories: dev, learn, media, ideas.
        
        Args:
            url: Full URL (lowercase)
            domain: Domain part (lowercase)
            path: Path part (lowercase)
            
        Returns:
            Category string: 'dev', 'learn', 'media', or 'ideas'
        """
        # Development content patterns
        dev_patterns = [
            'github.com', 'gitlab.com', 'bitbucket.org',
            'stackoverflow.com', 'stackexchange.com',
            'developer.mozilla.org', 'docs.python.org', 'docs.microsoft.com',
            'api.', 'docs.', 'documentation', 'developer.',
            'programming', 'coding', 'software', 'framework'
        ]
        
        # Learning content patterns
        learn_patterns = [
            'tutorial', 'course', 'learn', 'guide', 'education',
            'academy', 'training', 'workshop', 'udemy.com',
            'coursera.org', 'edx.org', 'pluralsight.com',
            'freecodecamp.org', 'codecademy.com', 'w3schools.com',
            'geeksforgeeks.org', 'tutorialspoint.com'
        ]
        
        # Media content patterns
        media_patterns = [
            'youtube.com', 'youtu.be', 'vimeo.com', 'twitch.tv',
            'video', 'audio', 'podcast', 'media', 'watch',
            'image', 'photo', 'presentation', 'slide',
            'instagram.com', 'tiktok.com'
        ]
        
        # Check for development content
        if any(pattern in url or pattern in domain for pattern in dev_patterns):
            return 'dev'
        
        # Check for learning content
        if any(pattern in url or pattern in domain for pattern in learn_patterns):
            return 'learn'
        
        # Check for media content
        if any(pattern in url or pattern in domain for pattern in media_patterns):
            return 'media'
        
        # Check path for additional clues
        if any(keyword in path for keyword in ['video', 'watch', 'media', 'image']):
            return 'media'
        
        if any(keyword in path for keyword in ['tutorial', 'course', 'learn', 'guide']):
            return 'learn'
        
        if any(keyword in path for keyword in ['api', 'docs', 'documentation', 'code']):
            return 'dev'
        
        # Default to ideas for personal notes, bookmarks, etc.
        return 'ideas'
    
    @classmethod
    def _classify_github_content(cls, url: str) -> Dict[str, any]:
        """Classify GitHub URL into specific content types."""
        # Check for GitHub documents first (most specific)
        for pattern in cls.GITHUB_DOCUMENT_PATTERNS:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return {
                    'github_type': 'github_document',
                    'user': match.group(1) if len(match.groups()) >= 1 else None,
                    'repo': match.group(2) if len(match.groups()) >= 2 else None,
                    'file_path': match.group(3) if len(match.groups()) >= 3 else None,
                    'is_markdown': url.lower().endswith('.md'),
                    'is_documentation': True
                }
        
        # Check for GitHub gists
        for pattern in cls.GITHUB_GIST_PATTERNS:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return {
                    'github_type': 'github_document',
                    'user': match.group(1) if len(match.groups()) >= 1 else None,
                    'gist_id': match.group(2) if len(match.groups()) >= 2 else None,
                    'is_gist': True,
                    'is_documentation': True
                }
        
        # Check for GitHub repos (broader patterns)
        for pattern in cls.GITHUB_REPO_PATTERNS:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return {
                    'github_type': 'github_repo',
                    'user': match.group(1) if len(match.groups()) >= 1 else None,
                    'repo': match.group(2) if len(match.groups()) >= 2 else None,
                    'is_repository': True,
                    'is_documentation': False
                }
        
        # Fallback for any GitHub URL
        if 'github.com' in url.lower():
            return {
                'github_type': 'github_repo',
                'is_repository': True,
                'is_documentation': False
            }
        
        return None
    
    @classmethod
    def _is_development_url(cls, url: str, domain: str, path: str) -> bool:
        """Check if URL is development-related."""
        # Check GitHub patterns
        github_info = cls._classify_github_content(url)
        if github_info:
            return True
            
        # Check other development patterns
        all_patterns = (
            cls.STACKOVERFLOW_PATTERNS + 
            cls.DOCUMENTATION_PATTERNS + cls.TUTORIAL_PATTERNS
        )
        
        for pattern in all_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def _detect_platform(cls, url: str, domain: str) -> Optional[str]:
        """Detect the platform type."""
        if 'github.com' in domain or 'githubusercontent.com' in domain:
            return 'github'
        elif any(pattern in domain for pattern in ['stackoverflow', 'stackexchange', 'serverfault', 'superuser', 'askubuntu']):
            return 'stackoverflow'
        elif any(re.search(pattern, url) for pattern in cls.DOCUMENTATION_PATTERNS):
            return 'documentation'
        elif any(re.search(pattern, url) for pattern in cls.TUTORIAL_PATTERNS):
            return 'tutorial'
        return 'other'
    
    @classmethod
    def _detect_language(cls, url: str, path: str) -> Optional[str]:
        """Detect programming language from URL."""
        for language, patterns in cls.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return language
        return None
    
    @classmethod
    def _detect_category(cls, url: str, path: str) -> Optional[str]:
        """Detect project category from URL."""
        for category, patterns in cls.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return category
        return 'Documentation'  # Default category
    
    @classmethod
    def _detect_difficulty(cls, url: str, path: str) -> Optional[int]:
        """Detect difficulty level from URL patterns."""
        # Basic heuristics for difficulty detection
        if any(word in url.lower() for word in ['beginner', 'intro', 'getting-started', 'tutorial', 'basics']):
            return 1
        elif any(word in url.lower() for word in ['intermediate', 'guide', 'best-practices']):
            return 2
        elif any(word in url.lower() for word in ['advanced', 'expert', 'deep-dive', 'architecture']):
            return 4
        elif any(word in url.lower() for word in ['master', 'comprehensive', 'complete']):
            return 5
        return 2  # Default to intermediate
    
    @classmethod
    def _is_career_related(cls, url: str, path: str) -> bool:
        """Check if content is career-related."""
        career_keywords = [
            'interview', 'job', 'career', 'hiring', 'resume', 
            'salary', 'leetcode', 'coding-interview', 'technical-interview'
        ]
        return any(keyword in url.lower() for keyword in career_keywords)
    
    @classmethod
    def _extract_metadata(cls, url: str, platform: Optional[str]) -> Dict[str, any]:
        """Extract additional metadata based on platform."""
        metadata = {}
        
        if platform == 'github':
            metadata.update(cls._extract_github_metadata(url))
        elif platform == 'stackoverflow':
            metadata.update(cls._extract_stackoverflow_metadata(url))
        
        return metadata
    
    @classmethod
    def _extract_github_metadata(cls, url: str) -> Dict[str, any]:
        """Extract GitHub-specific metadata."""
        metadata = {}
        
        # Extract owner and repo from GitHub URL
        github_match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if github_match:
            owner, repo = github_match.groups()
            metadata['github_owner'] = owner
            metadata['github_repo'] = repo
            metadata['repo_url'] = f"https://github.com/{owner}/{repo}"
        
        return metadata
    
    @classmethod
    def _extract_stackoverflow_metadata(cls, url: str) -> Dict[str, any]:
        """Extract Stack Overflow-specific metadata."""
        metadata = {}
        
        # Extract question ID from Stack Overflow URL
        so_match = re.search(r'/questions/(\d+)', url)
        if so_match:
            metadata['question_id'] = so_match.group(1)
        
        return metadata

class GitHubPreviewGenerator:
    """Generator for GitHub repository rich previews."""
    
    @staticmethod
    def generate_preview(repo_url: str, github_token: Optional[str] = None) -> Dict[str, any]:
        """
        Generate rich preview for GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            github_token: Optional GitHub API token for higher rate limits
            
        Returns:
            Dictionary containing preview data
        """
        try:
            # Extract owner and repo from URL
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
            if not match:
                return {}
            
            owner, repo = match.groups()
            repo = repo.rstrip('.git')  # Remove .git suffix if present
            
            # GitHub API endpoint
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            
            # Prepare headers
            headers = {'Accept': 'application/vnd.github.v3+json'}
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            # Fetch repository data
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                repo_data = response.json()
                
                preview = {
                    'type': 'github_repo',
                    'name': repo_data.get('name'),
                    'full_name': repo_data.get('full_name'),
                    'description': repo_data.get('description'),
                    'language': repo_data.get('language'),
                    'stars': repo_data.get('stargazers_count', 0),
                    'forks': repo_data.get('forks_count', 0),
                    'open_issues': repo_data.get('open_issues_count', 0),
                    'default_branch': repo_data.get('default_branch', 'main'),
                    'created_at': repo_data.get('created_at'),
                    'updated_at': repo_data.get('updated_at'),
                    'homepage': repo_data.get('homepage'),
                    'topics': repo_data.get('topics', []),
                    'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
                    'archived': repo_data.get('archived', False),
                    'private': repo_data.get('private', False)
                }
                
                # Fetch README if available
                readme_content = GitHubPreviewGenerator._fetch_readme(owner, repo, headers)
                if readme_content:
                    preview['readme_snippet'] = readme_content[:500] + '...' if len(readme_content) > 500 else readme_content
                
                return preview
            
        except Exception as e:
            print(f"Error generating GitHub preview: {e}")
        
        return {}
    
    @staticmethod
    def _fetch_readme(owner: str, repo: str, headers: Dict[str, str]) -> Optional[str]:
        """Fetch README content from repository."""
        readme_files = ['README.md', 'readme.md', 'Readme.md', 'README.rst', 'README.txt']
        
        for readme_file in readme_files:
            try:
                readme_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_file}"
                response = requests.get(readme_url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    readme_data = response.json()
                    if readme_data.get('encoding') == 'base64':
                        import base64
                        content = base64.b64decode(readme_data['content']).decode('utf-8')
                        # Extract first few lines, removing markdown syntax
                        lines = content.split('\n')[:10]
                        clean_lines = []
                        for line in lines:
                            # Remove markdown headers, links, etc.
                            clean_line = re.sub(r'#+\s*', '', line)  # Remove headers
                            clean_line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_line)  # Remove links
                            clean_line = re.sub(r'[*_`]', '', clean_line)  # Remove formatting
                            if clean_line.strip():
                                clean_lines.append(clean_line.strip())
                        
                        return '\n'.join(clean_lines)
            except Exception:
                continue
        
        return None