"""
Rich Preview Service for Development Content

Generates rich previews for GitHub repositories, Stack Overflow questions,
and other development-related content to enhance timeline display.
"""

import os
import re
import json
import asyncio
import aiohttp
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

from app.utils.url_classifier import URLClassifier

logger = logging.getLogger(__name__)

class PreviewService:
    """Service for generating rich previews of development content."""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.cache_duration = timedelta(hours=6)  # Cache previews for 6 hours
        
    async def generate_preview(self, url: str, content_type: str = 'development') -> Dict[str, Any]:
        """
        Generate a rich preview for the given URL.
        
        Args:
            url: The URL to generate preview for
            content_type: Type of content ('development', 'auto', etc.)
            
        Returns:
            Dictionary containing preview data
        """
        try:
            # Classify the URL first
            classification = URLClassifier.classify_url(url)
            
            if not classification['is_development']:
                return await self._generate_basic_preview(url)
            
            platform = classification.get('platform')
            
            if platform == 'github':
                return await self._generate_github_preview(url, classification)
            elif platform == 'stackoverflow':
                return await self._generate_stackoverflow_preview(url, classification)
            elif platform == 'documentation':
                return await self._generate_documentation_preview(url, classification)
            else:
                return await self._generate_development_preview(url, classification)
                
        except Exception as e:
            logger.error(f"Error generating preview for {url}: {e}")
            return {
                'type': 'error',
                'error': str(e),
                'url': url
            }
    
    async def _generate_github_preview(self, url: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rich preview for GitHub repositories."""
        try:
            metadata = classification.get('metadata', {})
            repo_url = metadata.get('repo_url', url)
            
            # Extract owner and repo from URL
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
            if not match:
                return await self._generate_basic_preview(url)
            
            owner, repo = match.groups()
            repo = repo.rstrip('.git')  # Remove .git suffix if present
            
            async with aiohttp.ClientSession() as session:
                # Fetch repository data from GitHub API
                repo_data = await self._fetch_github_repo_data(session, owner, repo)
                
                if not repo_data:
                    return await self._generate_basic_preview(url)
                
                # Fetch README content
                readme_content = await self._fetch_github_readme(session, owner, repo)
                
                # Fetch recent commits
                commits = await self._fetch_github_commits(session, owner, repo, limit=3)
                
                # Fetch repository topics/languages
                languages = await self._fetch_github_languages(session, owner, repo)
                
                return {
                    'type': 'github_repo',
                    'platform': 'github',
                    'url': url,
                    'repo': {
                        'name': repo_data.get('name'),
                        'full_name': repo_data.get('full_name'),
                        'description': repo_data.get('description'),
                        'language': repo_data.get('language'),
                        'homepage': repo_data.get('homepage'),
                        'clone_url': repo_data.get('clone_url'),
                        'ssh_url': repo_data.get('ssh_url'),
                        'archived': repo_data.get('archived', False),
                        'private': repo_data.get('private', False),
                        'fork': repo_data.get('fork', False)
                    },
                    'stats': {
                        'stars': repo_data.get('stargazers_count', 0),
                        'forks': repo_data.get('forks_count', 0),
                        'watchers': repo_data.get('watchers_count', 0),
                        'open_issues': repo_data.get('open_issues_count', 0),
                        'size': repo_data.get('size', 0)  # Repository size in KB
                    },
                    'timestamps': {
                        'created_at': repo_data.get('created_at'),
                        'updated_at': repo_data.get('updated_at'),
                        'pushed_at': repo_data.get('pushed_at')
                    },
                    'readme': {
                        'snippet': readme_content.get('snippet') if readme_content else None,
                        'full_length': readme_content.get('full_length') if readme_content else 0
                    },
                    'recent_commits': commits,
                    'languages': languages,
                    'topics': repo_data.get('topics', []),
                    'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
                    'default_branch': repo_data.get('default_branch', 'main'),
                    'owner': {
                        'login': repo_data.get('owner', {}).get('login'),
                        'type': repo_data.get('owner', {}).get('type'),
                        'avatar_url': repo_data.get('owner', {}).get('avatar_url')
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating GitHub preview: {e}")
            return await self._generate_basic_preview(url)
    
    async def _fetch_github_repo_data(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch repository data from GitHub API."""
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            async with session.get(api_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"GitHub API returned status {response.status} for {owner}/{repo}")
                    
        except Exception as e:
            logger.error(f"Error fetching GitHub repo data: {e}")
        
        return None
    
    async def _fetch_github_readme(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch README content from GitHub repository."""
        readme_files = ['README.md', 'readme.md', 'Readme.md', 'README.rst', 'README.txt', 'README']
        
        for readme_file in readme_files:
            try:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_file}"
                headers = {'Accept': 'application/vnd.github.v3+json'}
                
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                async with session.get(api_url, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        readme_data = await response.json()
                        
                        if readme_data.get('encoding') == 'base64':
                            import base64
                            content = base64.b64decode(readme_data['content']).decode('utf-8')
                            
                            # Extract meaningful snippet (remove headers, links, badges)
                            snippet = self._extract_readme_snippet(content)
                            
                            return {
                                'snippet': snippet,
                                'full_length': len(content),
                                'file_name': readme_file
                            }
                            
            except Exception as e:
                logger.debug(f"README {readme_file} not found or error: {e}")
                continue
        
        return None
    
    def _extract_readme_snippet(self, content: str) -> str:
        """Extract a meaningful snippet from README content."""
        lines = content.split('\n')
        clean_lines = []
        
        for line in lines:
            # Skip common badges and shields
            if re.search(r'!\[.*\]\(.*badge.*\)', line, re.IGNORECASE):
                continue
            if re.search(r'!\[.*\]\(.*shield.*\)', line, re.IGNORECASE):
                continue
            
            # Clean markdown formatting
            clean_line = re.sub(r'#+\s*', '', line)  # Remove headers
            clean_line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_line)  # Remove links
            clean_line = re.sub(r'[*_`]', '', clean_line)  # Remove formatting
            clean_line = clean_line.strip()
            
            if clean_line and len(clean_line) > 10:  # Meaningful content
                clean_lines.append(clean_line)
                
                # Stop after we have enough content
                if len(' '.join(clean_lines)) > 300:
                    break
        
        snippet = ' '.join(clean_lines)
        if len(snippet) > 400:
            snippet = snippet[:400] + '...'
        
        return snippet or "No description available."
    
    async def _fetch_github_commits(self, session: aiohttp.ClientSession, owner: str, repo: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Fetch recent commits from GitHub repository."""
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            params = {'per_page': limit}
            
            async with session.get(api_url, headers=headers, params=params, timeout=5) as response:
                if response.status == 200:
                    commits_data = await response.json()
                    
                    return [
                        {
                            'sha': commit['sha'][:7],
                            'message': commit['commit']['message'].split('\n')[0][:100],
                            'author': commit['commit']['author']['name'],
                            'date': commit['commit']['author']['date'],
                            'url': commit['html_url']
                        }
                        for commit in commits_data
                    ]
                    
        except Exception as e:
            logger.debug(f"Error fetching commits: {e}")
        
        return []
    
    async def _fetch_github_languages(self, session: aiohttp.ClientSession, owner: str, repo: str) -> Dict[str, int]:
        """Fetch programming languages from GitHub repository."""
        try:
            api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            async with session.get(api_url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                    
        except Exception as e:
            logger.debug(f"Error fetching languages: {e}")
        
        return {}
    
    async def _generate_stackoverflow_preview(self, url: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rich preview for Stack Overflow questions."""
        try:
            metadata = classification.get('metadata', {})
            question_id = metadata.get('question_id')
            
            if not question_id:
                return await self._generate_basic_preview(url)
            
            # Use Stack Exchange API to get question details
            api_url = f"https://api.stackexchange.com/2.3/questions/{question_id}"
            params = {
                'site': 'stackoverflow',
                'filter': 'withbody'  # Include question body
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('items'):
                            question = data['items'][0]
                            
                            return {
                                'type': 'stackoverflow_question',
                                'platform': 'stackoverflow',
                                'url': url,
                                'question': {
                                    'title': question.get('title'),
                                    'body_snippet': BeautifulSoup(question.get('body', ''), 'html.parser').get_text()[:300] + '...',
                                    'tags': question.get('tags', []),
                                    'score': question.get('score', 0),
                                    'view_count': question.get('view_count', 0),
                                    'answer_count': question.get('answer_count', 0),
                                    'is_answered': question.get('is_answered', False),
                                    'creation_date': datetime.fromtimestamp(question.get('creation_date', 0)).isoformat(),
                                    'last_activity_date': datetime.fromtimestamp(question.get('last_activity_date', 0)).isoformat()
                                }
                            }
            
        except Exception as e:
            logger.error(f"Error generating Stack Overflow preview: {e}")
        
        return await self._generate_basic_preview(url)
    
    async def _generate_documentation_preview(self, url: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate rich preview for documentation sites."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Extract common documentation metadata
                        title = self._extract_title(soup)
                        description = self._extract_description(soup)
                        
                        return {
                            'type': 'documentation',
                            'platform': 'documentation',
                            'url': url,
                            'title': title,
                            'description': description,
                            'domain': urlparse(url).netloc,
                            'programming_language': classification.get('programming_language'),
                            'project_category': classification.get('project_category')
                        }
            
        except Exception as e:
            logger.error(f"Error generating documentation preview: {e}")
        
        return await self._generate_basic_preview(url)
    
    async def _generate_development_preview(self, url: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic development content preview."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        title = self._extract_title(soup)
                        description = self._extract_description(soup)
                        
                        return {
                            'type': 'development_content',
                            'platform': classification.get('platform', 'unknown'),
                            'url': url,
                            'title': title,
                            'description': description,
                            'domain': urlparse(url).netloc,
                            'programming_language': classification.get('programming_language'),
                            'project_category': classification.get('project_category'),
                            'difficulty_level': classification.get('difficulty_level')
                        }
            
        except Exception as e:
            logger.error(f"Error generating development preview: {e}")
        
        return await self._generate_basic_preview(url)
    
    async def _generate_basic_preview(self, url: str) -> Dict[str, Any]:
        """Generate basic preview for non-development content."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        title = self._extract_title(soup)
                        description = self._extract_description(soup)
                        
                        return {
                            'type': 'basic',
                            'url': url,
                            'title': title,
                            'description': description,
                            'domain': urlparse(url).netloc
                        }
            
        except Exception as e:
            logger.error(f"Error generating basic preview: {e}")
        
        return {
            'type': 'error',
            'url': url,
            'error': 'Unable to generate preview'
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML."""
        # Try Open Graph title first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']
        
        # Try Twitter title
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content']
        
        # Fallback to HTML title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        return "No title available"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract description from HTML."""
        # Try Open Graph description first
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content']
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']
        
        # Try Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content']
        
        return "No description available"

# Global instance
preview_service = PreviewService()