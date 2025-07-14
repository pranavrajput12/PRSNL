"""
PRSNL synchronization client for CodeMirror CLI.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import aiohttp
import asyncio


class PRSNLSync:
    """Handles synchronization with PRSNL backend."""
    
    def __init__(self, config, console):
        self.config = config
        self.console = console
        self.base_url = config.prsnl_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {config.prsnl_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'PRSNL-CodeMirror-CLI/1.0.0'
        }
    
    async def upload_analysis(self, analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Upload analysis results to PRSNL."""
        try:
            async with aiohttp.ClientSession() as session:
                # First, get or create the repository
                repo_data = await self._get_or_create_repository(session, analysis_result)
                if not repo_data:
                    return None
                
                # Upload the analysis
                upload_data = {
                    'repo_id': repo_data['id'],
                    'analysis_type': 'cli',
                    'analysis_depth': analysis_result.get('analysis_depth', 'standard'),
                    'analysis_data': analysis_result,
                    'metadata': {
                        'cli_version': '1.0.0',
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'cli'
                    }
                }
                
                async with session.post(
                    f'{self.base_url}/api/code-cortex/codemirror/cli/sync',
                    headers=self.headers,
                    json=upload_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'analysis_id': result.get('analysis_id'),
                            'analysis_url': f"{self.base_url}/code-cortex/codemirror?analysis={result.get('analysis_id')}"
                        }
                    else:
                        error_text = await response.text()
                        self.console.print(f"[red]Upload failed: {response.status} - {error_text}[/red]")
                        return None
        
        except Exception as e:
            if self.config.debug:
                self.console.print_exception()
            self.console.print(f"[red]Upload error: {e}[/red]")
            return None
    
    async def download_analyses(self, repo_id: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Download analyses from PRSNL."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f'{self.base_url}/api/code-cortex/codemirror/analyses'
                params = {}
                if repo_id:
                    params['repo_id'] = repo_id
                
                async with session.get(
                    url,
                    headers=self.headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        analyses = await response.json()
                        
                        # Cache downloaded analyses
                        for analysis in analyses:
                            self._cache_downloaded_analysis(analysis)
                        
                        return analyses
                    else:
                        error_text = await response.text()
                        self.console.print(f"[red]Download failed: {response.status} - {error_text}[/red]")
                        return None
        
        except Exception as e:
            if self.config.debug:
                self.console.print_exception()
            self.console.print(f"[red]Download error: {e}[/red]")
            return None
    
    async def _get_or_create_repository(self, session: aiohttp.ClientSession, 
                                      analysis_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get existing repository or create new one."""
        repo_info = analysis_result.get('repository', {})
        git_info = repo_info.get('git', {})
        
        # Try to find existing repository by remote URL
        if git_info.get('remote'):
            existing_repo = await self._find_repository_by_remote(session, git_info['remote'])
            if existing_repo:
                return existing_repo
        
        # Create new repository
        repo_data = {
            'name': repo_info.get('name', 'Unknown'),
            'description': f'Repository analyzed via CLI on {datetime.utcnow().strftime("%Y-%m-%d")}',
            'remote_url': git_info.get('remote'),
            'default_branch': git_info.get('branch', 'main'),
            'source': 'cli',
            'metadata': {
                'path': repo_info.get('path'),
                'size': repo_info.get('size'),
                'last_commit': git_info.get('last_commit')
            }
        }
        
        try:
            async with session.post(
                f'{self.base_url}/api/github/repos/create-local',
                headers=self.headers,
                json=repo_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    self.console.print(f"[red]Failed to create repository: {response.status} - {error_text}[/red]")
                    return None
        
        except Exception as e:
            if self.config.debug:
                self.console.print_exception()
            self.console.print(f"[red]Repository creation error: {e}[/red]")
            return None
    
    async def _find_repository_by_remote(self, session: aiohttp.ClientSession, 
                                       remote_url: str) -> Optional[Dict[str, Any]]:
        """Find repository by remote URL."""
        try:
            async with session.get(
                f'{self.base_url}/api/github/repos',
                headers=self.headers,
                params={'remote_url': remote_url}
            ) as response:
                if response.status == 200:
                    repos = await response.json()
                    return repos[0] if repos else None
                else:
                    return None
        
        except Exception:
            return None
    
    def _cache_downloaded_analysis(self, analysis: Dict[str, Any]):
        """Cache downloaded analysis locally."""
        try:
            repo_name = analysis.get('repository', {}).get('name', 'unknown')
            cache_path = self.config.get_cache_path(f"{repo_name}_remote")
            
            # Load existing cache
            cached_analyses = []
            if cache_path.exists():
                try:
                    with open(cache_path, 'r') as f:
                        cached_analyses = json.load(f)
                except Exception:
                    pass
            
            # Add new analysis if not already cached
            analysis_id = analysis.get('id')
            if not any(a.get('id') == analysis_id for a in cached_analyses):
                cached_analyses.append(analysis)
                
                # Keep only last 10 analyses
                cached_analyses = cached_analyses[-10:]
                
                # Save updated cache
                with open(cache_path, 'w') as f:
                    json.dump(cached_analyses, f, indent=2, default=str)
        
        except Exception as e:
            if self.config.debug:
                self.console.print(f"[yellow]Warning: Failed to cache analysis: {e}[/yellow]")
    
    def clear_cache(self):
        """Clear all cached data."""
        self.config.clear_cache()
    
    async def test_connection(self) -> bool:
        """Test connection to PRSNL backend."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.base_url}/health',
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        
        except Exception:
            return False