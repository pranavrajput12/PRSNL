"""
Repository Analyzer Service

Provides AI-powered analysis and auto-categorization of open source repositories.
Integrates with GitHub API and existing AI infrastructure for intelligent repository processing.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp
from pydantic import BaseModel

from app.config import settings
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)


class RepositoryMetadata(BaseModel):
    """Repository metadata structure"""
    repo_url: str
    repo_name: str
    owner: str
    description: Optional[str] = None
    stars: int = 0
    forks: int = 0
    language: Optional[str] = None
    tech_stack: List[str] = []
    use_case: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    license: Optional[str] = None
    topics: List[str] = []
    last_updated: Optional[str] = None
    ai_analysis: Dict[str, Any] = {}
    github_data: Dict[str, Any] = {}


class RepositoryAnalyzer:
    """Service for analyzing and categorizing repositories"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        self.github_token = settings.GITHUB_TOKEN  # Add to config if not exists
        
    async def analyze_repository(self, repo_url: str) -> RepositoryMetadata:
        """
        Analyze a repository URL and return comprehensive metadata
        
        Args:
            repo_url: GitHub/GitLab repository URL
            
        Returns:
            RepositoryMetadata with AI analysis and categorization
        """
        try:
            # Extract repository info from URL
            repo_info = self._extract_repo_info(repo_url)
            if not repo_info:
                raise ValueError(f"Invalid repository URL: {repo_url}")
            
            # Fetch GitHub data
            github_data = await self._fetch_github_data(repo_info['owner'], repo_info['name'])
            
            # Fetch additional repository content for analysis
            repo_content = await self._fetch_repository_content(repo_info['owner'], repo_info['name'])
            
            # Perform AI analysis
            ai_analysis = await self._perform_ai_analysis(github_data, repo_content)
            
            # Build comprehensive metadata
            metadata = RepositoryMetadata(
                repo_url=repo_url,
                repo_name=repo_info['name'],
                owner=repo_info['owner'],
                description=github_data.get('description', ''),
                stars=github_data.get('stargazers_count', 0),
                forks=github_data.get('forks_count', 0),
                language=github_data.get('language'),
                tech_stack=ai_analysis.get('tech_stack', []),
                use_case=ai_analysis.get('use_case'),
                category=ai_analysis.get('category'),
                difficulty=ai_analysis.get('difficulty'),
                license=github_data.get('license', {}).get('spdx_id') if github_data.get('license') else None,
                topics=github_data.get('topics', []),
                last_updated=github_data.get('updated_at'),
                ai_analysis=ai_analysis,
                github_data=github_data
            )
            
            logger.info(f"Successfully analyzed repository: {repo_url}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_url}: {e}")
            # Return basic metadata even if analysis fails
            repo_info = self._extract_repo_info(repo_url) or {'owner': 'unknown', 'name': 'unknown'}
            return RepositoryMetadata(
                repo_url=repo_url,
                repo_name=repo_info['name'],
                owner=repo_info['owner'],
                description="Analysis failed - manual categorization required",
                ai_analysis={"error": str(e), "confidence": 0.0}
            )
    
    def _extract_repo_info(self, repo_url: str) -> Optional[Dict[str, str]]:
        """Extract owner and repository name from URL"""
        try:
            # Support GitHub and GitLab URLs
            patterns = [
                r'github\.com/([^/]+)/([^/]+)',
                r'gitlab\.com/([^/]+)/([^/]+)',
                r'bitbucket\.org/([^/]+)/([^/]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, repo_url.lower())
                if match:
                    owner, name = match.groups()
                    # Remove .git suffix if present
                    name = name.replace('.git', '')
                    return {'owner': owner, 'name': name}
            
            return None
        except Exception:
            return None
    
    async def _fetch_github_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository data from GitHub API"""
        try:
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            url = f"https://api.github.com/repos/{owner}/{repo}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"GitHub API returned {response.status} for {owner}/{repo}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching GitHub data for {owner}/{repo}: {e}")
            return {}
    
    async def _fetch_repository_content(self, owner: str, repo: str) -> Dict[str, str]:
        """Fetch key repository files for analysis"""
        content = {}
        
        # Files to fetch for analysis
        key_files = ['README.md', 'package.json', 'requirements.txt', 'setup.py', 'Cargo.toml', 
                    'composer.json', 'pom.xml', 'go.mod', 'Dockerfile']
        
        try:
            headers = {}
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            async with aiohttp.ClientSession() as session:
                for file in key_files:
                    try:
                        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file}"
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                file_data = await response.json()
                                if file_data.get('content'):
                                    # Decode base64 content
                                    import base64
                                    decoded_content = base64.b64decode(file_data['content']).decode('utf-8', errors='ignore')
                                    content[file] = decoded_content[:5000]  # Limit content size
                    except Exception:
                        continue  # Skip files that can't be fetched
            
        except Exception as e:
            logger.error(f"Error fetching repository content for {owner}/{repo}: {e}")
        
        return content
    
    async def _perform_ai_analysis(self, github_data: Dict[str, Any], repo_content: Dict[str, str]) -> Dict[str, Any]:
        """Perform AI analysis of repository"""
        try:
            # Prepare analysis prompt
            analysis_prompt = self._build_analysis_prompt(github_data, repo_content)
            
            # Use existing AI service for analysis
            response = await self.ai_service.complete(
                prompt=analysis_prompt,
                system_prompt="""You are an expert software developer analyzing open source repositories. 
                Analyze the provided repository information and return a JSON response with the following structure:
                {
                    "tech_stack": ["technology1", "technology2", ...],
                    "category": "frontend|backend|fullstack|ai|devops|mobile|desktop|library|tool|framework",
                    "use_case": "brief description of primary use case",
                    "difficulty": "beginner|intermediate|advanced",
                    "purpose": "detailed description of what this repository does",
                    "key_features": ["feature1", "feature2", ...],
                    "learning_curve": "easy|moderate|steep",
                    "community_size": "small|medium|large|very-large",
                    "maintenance_status": "active|maintained|inactive|deprecated",
                    "confidence": 0.95
                }
                
                Focus on accurate categorization and be specific with tech stack identification.""",
                max_tokens=1000,
                temperature=0.3,
                model=settings.AZURE_OPENAI_DEPLOYMENT
            )
            
            # Parse AI response
            try:
                ai_analysis = json.loads(response)
                ai_analysis['generated_at'] = datetime.utcnow().isoformat()
                return ai_analysis
            except json.JSONDecodeError:
                logger.warning("AI returned non-JSON response, using fallback analysis")
                return self._fallback_analysis(github_data, repo_content)
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return self._fallback_analysis(github_data, repo_content)
    
    def _build_analysis_prompt(self, github_data: Dict[str, Any], repo_content: Dict[str, str]) -> str:
        """Build comprehensive analysis prompt"""
        prompt_parts = []
        
        # Basic repository info
        prompt_parts.append(f"Repository: {github_data.get('full_name', 'Unknown')}")
        prompt_parts.append(f"Description: {github_data.get('description', 'No description')}")
        prompt_parts.append(f"Primary Language: {github_data.get('language', 'Unknown')}")
        prompt_parts.append(f"Stars: {github_data.get('stargazers_count', 0)}")
        prompt_parts.append(f"Topics: {', '.join(github_data.get('topics', []))}")
        
        # Repository content analysis
        if 'README.md' in repo_content:
            readme_content = repo_content['README.md'][:2000]  # Limit README content
            prompt_parts.append(f"\nREADME Content:\n{readme_content}")
        
        # Package files analysis
        package_files = ['package.json', 'requirements.txt', 'Cargo.toml', 'composer.json', 'pom.xml']
        for file in package_files:
            if file in repo_content:
                prompt_parts.append(f"\n{file} Content:\n{repo_content[file][:1000]}")
        
        return "\n\n".join(prompt_parts)
    
    def _fallback_analysis(self, github_data: Dict[str, Any], repo_content: Dict[str, str]) -> Dict[str, Any]:
        """Fallback analysis when AI analysis fails"""
        # Basic rule-based analysis
        language = github_data.get('language', '').lower()
        topics = [topic.lower() for topic in github_data.get('topics', [])]
        description = github_data.get('description', '').lower()
        
        # Determine tech stack based on language and topics
        tech_stack = []
        if language:
            tech_stack.append(language)
        tech_stack.extend(topics[:5])  # Limit topics
        
        # Determine category
        category = 'library'  # Default
        if any(word in description for word in ['framework', 'api', 'server']):
            category = 'framework'
        elif any(word in description for word in ['tool', 'cli', 'utility']):
            category = 'tool'
        elif language in ['javascript', 'typescript', 'css', 'html']:
            category = 'frontend'
        elif language in ['python', 'java', 'go', 'rust', 'c++']:
            category = 'backend'
        
        # Determine difficulty based on stars and complexity
        stars = github_data.get('stargazers_count', 0)
        if stars > 10000:
            difficulty = 'intermediate'
        elif stars > 1000:
            difficulty = 'beginner'
        else:
            difficulty = 'advanced'  # Newer or more specialized projects
        
        return {
            'tech_stack': tech_stack,
            'category': category,
            'use_case': github_data.get('description', 'Repository for development'),
            'difficulty': difficulty,
            'purpose': github_data.get('description', 'Open source project'),
            'key_features': topics[:3],
            'learning_curve': 'moderate',
            'community_size': 'medium',
            'maintenance_status': 'active',
            'confidence': 0.7,
            'generated_at': datetime.utcnow().isoformat(),
            'analysis_method': 'fallback'
        }


# Global instance
repository_analyzer = RepositoryAnalyzer()