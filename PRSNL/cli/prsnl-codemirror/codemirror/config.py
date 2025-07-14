"""
Configuration management for PRSNL CodeMirror CLI.
"""

import json
import os
from pathlib import Path
from typing import Optional


class CLIConfig:
    """Manages CLI configuration settings."""
    
    def __init__(self):
        self.config_dir = Path.home() / '.prsnl' / 'codemirror'
        self.config_file = self.config_dir / 'config.json'
        self.cache_dir = self.config_dir / 'cache'
        
        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self._config = {
            'prsnl_url': None,
            'prsnl_token': None,
            'github_token': None,
            'openai_key': None,
            'debug': False,
            'cache_ttl': 3600,  # 1 hour
            'max_file_size': 1048576,  # 1MB
            'exclude_patterns': [
                '.git/*',
                'node_modules/*',
                '*.pyc',
                '__pycache__/*',
                '.venv/*',
                '.env',
                '*.log',
                'dist/*',
                'build/*',
                '.svelte-kit/*'
            ],
            'include_extensions': [
                '.py', '.js', '.ts', '.jsx', '.tsx', '.svelte',
                '.html', '.css', '.scss', '.sass', '.less',
                '.go', '.rs', '.java', '.cpp', '.c', '.h',
                '.php', '.rb', '.swift', '.kt', '.scala',
                '.sql', '.md', '.yaml', '.yml', '.json',
                '.toml', '.ini', '.cfg', '.conf', '.sh'
            ]
        }
        
        # Load existing configuration
        self.load()
    
    def load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self._config.update(saved_config)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")
    
    @property
    def prsnl_url(self) -> Optional[str]:
        return self._config.get('prsnl_url')
    
    @prsnl_url.setter
    def prsnl_url(self, value: str):
        self._config['prsnl_url'] = value
    
    @property
    def prsnl_token(self) -> Optional[str]:
        return self._config.get('prsnl_token')
    
    @prsnl_token.setter
    def prsnl_token(self, value: str):
        self._config['prsnl_token'] = value
    
    @property
    def github_token(self) -> Optional[str]:
        return self._config.get('github_token')
    
    @github_token.setter
    def github_token(self, value: str):
        self._config['github_token'] = value
    
    @property
    def openai_key(self) -> Optional[str]:
        return self._config.get('openai_key')
    
    @openai_key.setter
    def openai_key(self, value: str):
        self._config['openai_key'] = value
    
    @property
    def debug(self) -> bool:
        return self._config.get('debug', False)
    
    @debug.setter
    def debug(self, value: bool):
        self._config['debug'] = value
    
    @property
    def cache_ttl(self) -> int:
        return self._config.get('cache_ttl', 3600)
    
    @property
    def max_file_size(self) -> int:
        return self._config.get('max_file_size', 1048576)
    
    @property
    def exclude_patterns(self) -> list:
        return self._config.get('exclude_patterns', [])
    
    @property
    def include_extensions(self) -> list:
        return self._config.get('include_extensions', [])
    
    def get_cache_path(self, repo_name: str) -> Path:
        """Get cache path for a repository."""
        return self.cache_dir / f"{repo_name}.json"
    
    def clear_cache(self):
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob('*.json'):
            cache_file.unlink()