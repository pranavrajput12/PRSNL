"""
GitHub Service - OAuth and API integration for CodeMirror

Handles GitHub authentication and repository data fetching.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings
from app.db.database import get_db_pool
from app.services.http_client_factory import http_client_factory, ClientType

logger = logging.getLogger(__name__)

class GitHubService:
    """
    GitHub integration service for PRSNL CodeMirror.
    Handles OAuth flow and repository data fetching.
    """
    
    GITHUB_API_BASE = "https://api.github.com"
    OAUTH_BASE = "https://github.com/login/oauth"
    SCOPES = ["read:user", "repo", "metadata"]
    
    def __init__(self):
        # Use centralized HTTP client factory
        self.http_client_factory = http_client_factory
        # Use environment variable for encryption key
        self.encryption_key = settings.ENCRYPTION_KEY.encode()[:32]  # AES-256 requires 32 bytes
        
    async def init_oauth_flow(self, user_id: str) -> str:
        """Generate GitHub OAuth URL for user authorization"""
        
        # Generate secure state token
        import secrets
        state = f"{user_id}:{secrets.token_urlsafe(32)}"
        
        # Store state temporarily
        from app.services.cache import cache_service
        await cache_service.set(f"github_oauth_state:{state}", user_id, expire=600)
        
        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": f"{settings.BACKEND_URL}/api/github/auth/callback",
            "scope": " ".join(self.SCOPES),
            "state": state
        }
        
        return f"{self.OAUTH_BASE}/authorize?{urlencode(params)}"
    
    async def complete_oauth_flow(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token"""
        
        logger.info(f"Starting OAuth flow completion with code={code[:10]}... state={state[:20]}...")
        
        # Verify state
        from app.services.cache import cache_service
        user_id = await cache_service.get(f"github_oauth_state:{state}")
        
        if not user_id:
            # Fallback: Extract user_id from state for development
            # State format: "user_id:random_string"
            user_id = state.split(":")[0] if ":" in state else None
            
            if not user_id:
                raise ValueError("Invalid or expired OAuth state")
            
            logger.warning(f"GitHub OAuth: Using fallback user_id extraction from state, user_id={user_id}")
        
        # Exchange code for token
        async with self.http_client_factory.client_session(ClientType.GITHUB) as client:
            token_response = await client.post(
                f"{self.OAUTH_BASE}/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": f"{settings.BACKEND_URL}/api/github/auth/callback"
                }
            )
        
        token_data = token_response.json()
        if "access_token" not in token_data:
            logger.error(f"OAuth token exchange failed: {token_data}")
            raise ValueError(f"OAuth failed: {token_data.get('error_description', 'Unknown error')}")
        
        logger.info(f"Successfully obtained access token")
        
        # Get user info
        user_info = await self.get_user_info(token_data["access_token"])
        logger.info(f"Got GitHub user info: id={user_info.get('id')}, login={user_info.get('login')}")
        
        # Encrypt token with separate nonce
        aesgcm = AESGCM(self.encryption_key)
        nonce = os.urandom(12)
        encrypted_token = aesgcm.encrypt(nonce, token_data["access_token"].encode(), None)
        
        pool = await get_db_pool()
        async with pool.acquire() as db:
            # Check if GitHub account already exists (for any user)
            existing_account = await db.fetchrow("""
                SELECT id, user_id FROM github_accounts WHERE github_id = $1
            """, user_info["id"])
            
            if existing_account:
                # GitHub account exists - update it with new user and tokens
                logger.info(f"GitHub account {user_info['id']} already exists for user {existing_account['user_id']}, updating to user {user_id}")
                
                await db.execute("""
                    UPDATE github_accounts SET
                        user_id = $1,
                        github_username = $2,
                        github_email = $3,
                        avatar_url = $4,
                        access_token_encrypted = $5,
                        access_token_nonce = $6,
                        repos_url = $7,
                        organizations_url = $8,
                        updated_at = NOW()
                    WHERE github_id = $9
                """, 
                    user_id,
                    user_info["login"],
                    user_info.get("email"),
                    user_info.get("avatar_url"),
                    encrypted_token,
                    nonce,
                    user_info.get("repos_url"),
                    user_info.get("organizations_url"),
                    user_info["id"]
                )
                
                logger.info(f"Successfully updated GitHub account for user {user_id}, github_id={user_info['id']}")
            else:
                # New GitHub account - insert it
                await db.execute("""
                    INSERT INTO github_accounts (
                        user_id, github_id, github_username, github_email,
                        avatar_url, access_token_encrypted, access_token_nonce,
                        repos_url, organizations_url
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                    user_id,
                    user_info["id"],
                    user_info["login"],
                    user_info.get("email"),
                    user_info.get("avatar_url"),
                    encrypted_token,
                    nonce,
                    user_info.get("repos_url"),
                    user_info.get("organizations_url")
                )
                
                logger.info(f"Successfully created new GitHub account for user {user_id}, github_id={user_info['id']}")
        
        # Clean up state (cache_manager not implemented yet)
        # await cache_manager.delete(f"github_oauth_state:{state}")
        
        return {
            "github_username": user_info["login"],
            "avatar_url": user_info.get("avatar_url"),
            "name": user_info.get("name")
        }
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get GitHub user information"""
        
        async with self.http_client_factory.client_session(ClientType.GITHUB) as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/user",
                headers={"Authorization": f"token {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_repos(self, user_id: str, page: int = 1, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get user's GitHub repositories"""
        
        # Get access token
        access_token = await self._get_user_token(user_id)
        
        async with self.http_client_factory.client_session(ClientType.GITHUB) as client:
            response = await client.get(
                f"{self.GITHUB_API_BASE}/user/repos",
                headers={"Authorization": f"token {access_token}"},
                params={
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            }
        )
        response.raise_for_status()
        
        repos = response.json()
        
        # Store/update repos in database
        pool = await get_db_pool()
        async with pool.acquire() as db:
            account_id = await db.fetchval(
                "SELECT id FROM github_accounts WHERE user_id = $1",
                user_id
            )
            
            for repo in repos:
                await db.execute("""
                    INSERT INTO github_repos (
                        account_id, full_name, owner, name,
                        default_branch, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (account_id, full_name) DO UPDATE SET
                        default_branch = EXCLUDED.default_branch,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """,
                    account_id,
                    repo["full_name"],
                    repo["owner"]["login"],
                    repo["name"],
                    repo.get("default_branch", "main"),
                    json.dumps({
                        "description": repo.get("description"),
                        "language": repo.get("language"),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "topics": repo.get("topics", []),
                        "homepage": repo.get("homepage"),
                        "size": repo.get("size", 0),
                        "updated_at": repo.get("updated_at")
                    })
                )
        
        return repos
    
    async def fetch_file(self, repo_full_name: str, file_path: str) -> Optional[str]:
        """Fetch a specific file from a repository"""
        
        # Get access token from repo owner
        access_token = await self._get_token_for_repo(repo_full_name)
        
        try:
            async with self.http_client_factory.client_session(ClientType.GITHUB) as client:
                response = await client.get(
                    f"{self.GITHUB_API_BASE}/repos/{repo_full_name}/contents/{file_path}",
                    headers={"Authorization": f"token {access_token}"}
                )
                response.raise_for_status()
            
            data = response.json()
            if data.get("type") == "file" and "content" in data:
                # Decode base64 content
                import base64
                return base64.b64decode(data["content"]).decode('utf-8')
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        
        return None
    
    async def fetch_repo_structure(self, repo_full_name: str) -> List[str]:
        """Fetch repository file structure"""
        
        access_token = await self._get_token_for_repo(repo_full_name)
        
        # Get default branch
        async with self.http_client_factory.client_session(ClientType.GITHUB) as client:
            repo_response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{repo_full_name}",
                headers={"Authorization": f"token {access_token}"}
            )
            repo_data = repo_response.json()
            default_branch = repo_data.get("default_branch", "main")
            
            # Get tree
            tree_response = await client.get(
                f"{self.GITHUB_API_BASE}/repos/{repo_full_name}/git/trees/{default_branch}",
                headers={"Authorization": f"token {access_token}"},
                params={"recursive": "1"}
            )
            tree_data = tree_response.json()
        
        # Extract file paths
        files = []
        for item in tree_data.get("tree", []):
            if item["type"] == "blob":  # Files only, not directories
                files.append(item["path"])
        
        return files
    
    async def _fetch_package_files(self, repo_full_name: str) -> Dict[str, Any]:
        """Fetch package manager files for dependency analysis"""
        
        package_files = {}
        
        # Common package files to check
        files_to_fetch = [
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "requirements.txt",
            "Pipfile",
            "Pipfile.lock",
            "go.mod",
            "Cargo.toml",
            "pom.xml",
            "build.gradle",
            "composer.json"
        ]
        
        for file_name in files_to_fetch:
            content = await self.fetch_file(repo_full_name, file_name)
            if content:
                package_files[file_name] = content
        
        return package_files
    
    async def _fetch_code_samples(self, repo_full_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch sample code files for pattern analysis"""
        
        # Get file structure
        files = await self.fetch_repo_structure(repo_full_name)
        
        # Filter for code files
        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp']
        code_files = [f for f in files if any(f.endswith(ext) for ext in code_extensions)]
        
        # Sample files (prioritize src/ and lib/ directories)
        priority_files = [f for f in code_files if f.startswith(('src/', 'lib/', 'app/'))]
        other_files = [f for f in code_files if f not in priority_files]
        
        sample_files = (priority_files[:limit//2] + other_files[:limit//2])[:limit]
        
        # Fetch content
        samples = []
        for file_path in sample_files:
            content = await self.fetch_file(repo_full_name, file_path)
            if content:
                samples.append({
                    "path": file_path,
                    "content": content[:5000],  # Limit content size
                    "language": self._detect_language(file_path)
                })
        
        return samples
    
    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension"""
        
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        for ext, lang in ext_to_lang.items():
            if file_path.endswith(ext):
                return lang
        
        return 'unknown'
    
    async def _get_user_token(self, user_id: str) -> str:
        """Get decrypted access token for a user"""
        
        pool = await get_db_pool()
        async with pool.acquire() as db:
            encrypted_token = await db.fetchval(
                "SELECT access_token_encrypted FROM github_accounts WHERE user_id = $1",
                user_id
            )
            
            if not encrypted_token:
                raise ValueError("No GitHub account linked")
            
            return self.decrypt_token(encrypted_token)
    
    async def _get_token_for_repo(self, repo_full_name: str) -> str:
        """Get access token for a specific repository"""
        
        pool = await get_db_pool()
        async with pool.acquire() as db:
            encrypted_token = await db.fetchval("""
                SELECT ga.access_token_encrypted
                FROM github_repos gr
                JOIN github_accounts ga ON gr.account_id = ga.id
                WHERE gr.full_name = $1
            """, repo_full_name)
            
            if not encrypted_token:
                raise ValueError(f"No access to repository {repo_full_name}")
            
            return self.decrypt_token(encrypted_token)
    
    def encrypt_token(self, token: str) -> bytes:
        """Encrypt token using AES-256-GCM"""
        
        aesgcm = AESGCM(self.encryption_key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, token.encode(), None)
        return nonce + ciphertext  # Prepend nonce to ciphertext
    
    def decrypt_token(self, encrypted: bytes) -> str:
        """Decrypt token"""
        
        aesgcm = AESGCM(self.encryption_key)
        nonce = encrypted[:12]  # Extract nonce
        ciphertext = encrypted[12:]  # Extract ciphertext
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    
    def _decrypt_token(self, encrypted: bytes, nonce: bytes) -> str:
        """Decrypt token with separate nonce"""
        
        aesgcm = AESGCM(self.encryption_key)
        plaintext = aesgcm.decrypt(nonce, encrypted, None)
        return plaintext.decode('utf-8')
    
    async def fetch_user_repos(self, access_token: str) -> List[Dict[str, Any]]:
        """Fetch all user repositories"""
        
        all_repos = []
        page = 1
        per_page = 100
        
        async with self.http_client_factory.client_session(ClientType.GITHUB) as client:
            while True:
                response = await client.get(
                    f"{self.GITHUB_API_BASE}/user/repos",
                    headers={"Authorization": f"token {access_token}"},
                    params={
                        "page": page,
                        "per_page": per_page,
                        "sort": "updated",
                        "direction": "desc",
                        "type": "all"
                    }
                )
                response.raise_for_status()
                
                repos = response.json()
                if not repos:
                    break
                    
                all_repos.extend(repos)
                
                # Check if there are more pages
                if len(repos) < per_page:
                    break
                
                page += 1
                
                # Safety limit
                if page > 10:
                    break
        
        return all_repos
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # HTTP client cleanup is handled by the factory
        pass