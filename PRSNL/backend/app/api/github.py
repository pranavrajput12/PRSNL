"""
GitHub API - OAuth authentication and repository management

Handles GitHub login flow and personal repository synchronization.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.db.database import get_db_pool
from app.services.github_service import GitHubService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/github", tags=["github"])

# Request/Response Models
class GitHubAccount(BaseModel):
    id: str
    username: str
    email: Optional[str]
    avatar_url: Optional[str]
    connected_at: datetime
    repos_count: int
    
class GitHubRepo(BaseModel):
    id: str
    name: str
    full_name: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    is_private: bool
    default_branch: str
    last_synced: Optional[datetime]
    slug: Optional[str] = None
    html_url: Optional[str] = None
    owner: Optional[str] = None
    owner_avatar_url: Optional[str] = None
    owner_login: Optional[str] = None
    
class SyncReposRequest(BaseModel):
    force_refresh: bool = False

# Endpoints
@router.get("/auth/login")
async def github_login(
    redirect_uri: Optional[str] = Query(None)
):
    """Initiate GitHub OAuth flow"""
    
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth not configured"
        )
    
    # For now, use a temporary user ID. In a real app, you'd get this from session/auth
    # This will be replaced with proper user management
    temp_user_id = "temp-user-for-oauth"
    
    github_service = GitHubService()
    auth_url = await github_service.init_oauth_flow(temp_user_id)
    
    # Store redirect URI for after auth (temporarily disabled - cache not implemented)
    # if redirect_uri:
    #     from app.core.cache import cache_manager
    #     await cache_manager.set(
    #         f"github_redirect:{current_user.id}",
    #         redirect_uri,
    #         ttl=600
    #     )
    
    return {"auth_url": auth_url}

@router.get("/auth/callback")
async def github_callback(
    code: str,
    state: str,
    request: Request
):
    """Handle GitHub OAuth callback"""
    
    # Verify state and get user_id (temporarily disabled - cache not implemented)
    # from app.core.cache import cache_manager
    # user_id = await cache_manager.get(f"github_oauth_state:{state}")
    
    # if not user_id:
    #     raise HTTPException(status_code=400, detail="Invalid or expired state")
    
    # For now, use temp user ID
    user_id = "temp-user-for-oauth"
    
    # Exchange code for token
    github_service = GitHubService()
    try:
        account = await github_service.complete_oauth_flow(code, state)
    except Exception as e:
        logger.error(f"GitHub OAuth error: {str(e)}")
        raise HTTPException(status_code=400, detail="OAuth authentication failed")
    
    # Get redirect URI if stored (temporarily disabled - cache not implemented)
    # redirect_uri = await cache_manager.get(f"github_redirect:{user_id}")
    # if redirect_uri:
    #     await cache_manager.delete(f"github_redirect:{user_id}")
    #     return RedirectResponse(url=redirect_uri)
    
    # Default redirect to Code Cortex
    frontend_url = settings.FRONTEND_URL or "http://localhost:3004"
    return RedirectResponse(url=f"{frontend_url}/code-cortex/codemirror")

@router.get("/accounts")
async def get_github_accounts(
    current_user = Depends(get_current_user)
) -> List[GitHubAccount]:
    """Get connected GitHub accounts"""
    
    # For development/demo, check for temp user accounts too
    user_id = current_user.id if current_user else "temp-user-for-oauth"
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        accounts = await db.fetch("""
            SELECT 
                ga.id,
                ga.github_username as username,
                ga.github_email as email,
                ga.avatar_url,
                ga.created_at as connected_at,
                COUNT(gr.id) as repos_count
            FROM github_accounts ga
            LEFT JOIN github_repos gr ON ga.id = gr.account_id
            WHERE ga.user_id = $1
            GROUP BY ga.id
            ORDER BY ga.created_at DESC
        """, user_id)
        
        return [
            GitHubAccount(
                id=str(a['id']),
                username=a['username'],
                email=a['email'],
                avatar_url=a['avatar_url'],
                connected_at=a['connected_at'],
                repos_count=a['repos_count']
            )
            for a in accounts
        ]

@router.delete("/accounts/{account_id}")
async def disconnect_github_account(
    account_id: str,
    current_user = Depends(get_current_user)
):
    """Disconnect a GitHub account"""
    
    # For development/demo, allow temp user to disconnect
    user_id = current_user.id if current_user else "temp-user-for-oauth"
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        # Verify ownership
        account = await db.fetchrow("""
            SELECT id FROM github_accounts
            WHERE id = $1 AND user_id = $2
        """, UUID(account_id), user_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Delete account (cascades to repos and analyses)
        await db.execute("""
            DELETE FROM github_accounts WHERE id = $1
        """, UUID(account_id))
        
        return {"message": "GitHub account disconnected"}

@router.get("/repos")
async def get_repos(
    account_id: Optional[str] = None,
    language: Optional[str] = None,
    is_private: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user = Depends(get_current_user)
) -> List[GitHubRepo]:
    """Get synchronized repositories"""
    
    # For development/demo, check for temp user accounts too
    user_id = current_user.id if current_user else "temp-user-for-oauth"
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        query = """
            SELECT 
                gr.id,
                gr.name,
                gr.full_name,
                gr.description,
                gr.language,
                gr.stars,
                gr.forks,
                gr.is_private,
                gr.default_branch,
                gr.last_synced_at as last_synced,
                gr.slug,
                gr.html_url,
                ga.avatar_url as owner_avatar_url,
                ga.github_username as owner_login
            FROM github_repos gr
            JOIN github_accounts ga ON gr.account_id = ga.id
            WHERE ga.user_id = $1
        """
        
        params = [user_id]
        param_count = 1
        
        if account_id:
            param_count += 1
            query += f" AND gr.account_id = ${param_count}"
            params.append(UUID(account_id))
        
        if language:
            param_count += 1
            query += f" AND gr.language = ${param_count}"
            params.append(language)
        
        if is_private is not None:
            param_count += 1
            query += f" AND gr.is_private = ${param_count}"
            params.append(is_private)
        
        param_count += 1
        query += f" ORDER BY gr.stars DESC, gr.name ASC LIMIT ${param_count}"
        params.append(limit)
        
        repos = await db.fetch(query, *params)
        
        return [
            GitHubRepo(
                id=str(r['id']),
                name=r['name'],
                full_name=r['full_name'],
                description=r['description'],
                language=r['language'],
                stars=r['stars'],
                forks=r['forks'],
                is_private=r['is_private'],
                default_branch=r['default_branch'],
                last_synced=r['last_synced'],
                slug=r['slug'],
                html_url=r['html_url'],
                owner=r['owner_login'],
                owner_avatar_url=r['owner_avatar_url'],
                owner_login=r['owner_login']
            )
            for r in repos
        ]

@router.post("/repos/sync")
async def sync_repos(
    request: SyncReposRequest,
    account_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Sync repositories from GitHub"""
    
    # For development/demo, check for temp user accounts too
    user_id = current_user.id if current_user else "temp-user-for-oauth"
    
    github_service = GitHubService()
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        # Get accounts to sync
        if account_id:
            accounts = await db.fetch("""
                SELECT id, access_token_encrypted, access_token_nonce
                FROM github_accounts
                WHERE id = $1 AND user_id = $2
            """, UUID(account_id), user_id)
        else:
            accounts = await db.fetch("""
                SELECT id, access_token_encrypted, access_token_nonce
                FROM github_accounts
                WHERE user_id = $1
            """, user_id)
        
        if not accounts:
            raise HTTPException(status_code=404, detail="No GitHub accounts found")
        
        total_synced = 0
        
        for account in accounts:
            try:
                # Decrypt access token
                access_token = github_service._decrypt_token(
                    account['access_token_encrypted'],
                    account['access_token_nonce']
                )
                
                # Fetch and sync repos
                repos = await github_service.fetch_user_repos(access_token)
                
                for repo in repos:
                    # Check if repo exists
                    existing = await db.fetchrow("""
                        SELECT id FROM github_repos
                        WHERE account_id = $1 AND github_id = $2
                    """, account['id'], repo['id'])
                    
                    if existing:
                        # Update existing repo
                        await db.execute("""
                            UPDATE github_repos SET
                                name = $3,
                                full_name = $4,
                                description = $5,
                                language = $6,
                                stars = $7,
                                forks = $8,
                                is_private = $9,
                                default_branch = $10,
                                html_url = $11,
                                slug = $12,
                                last_synced_at = NOW()
                            WHERE id = $1
                        """, 
                            existing['id'],
                            repo['name'],
                            repo['full_name'],
                            repo['description'],
                            repo['language'],
                            repo['stargazers_count'],
                            repo['forks_count'],
                            repo['private'],
                            repo['default_branch'],
                            repo['html_url'],
                            repo['name'].lower().replace(' ', '-')
                        )
                    else:
                        # Insert new repo
                        await db.execute("""
                            INSERT INTO github_repos (
                                account_id, github_id, name, full_name,
                                description, language, stars, forks,
                                is_private, default_branch, html_url, slug
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        """,
                            account['id'],
                            repo['id'],
                            repo['name'],
                            repo['full_name'],
                            repo['description'],
                            repo['language'],
                            repo['stargazers_count'],
                            repo['forks_count'],
                            repo['private'],
                            repo['default_branch'],
                            repo['html_url'],
                            repo['name'].lower().replace(' ', '-')
                        )
                    
                    total_synced += 1
                
            except Exception as e:
                logger.error(f"Error syncing repos for account {account['id']}: {str(e)}")
                continue
        
        return {
            "message": f"Synced {total_synced} repositories",
            "repos_synced": total_synced
        }

@router.get("/repos/{repo_id}")
async def get_repo_details(
    repo_id: str,
    current_user = Depends(get_current_user)
) -> GitHubRepo:
    """Get detailed repository information"""
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        repo = await db.fetchrow("""
            SELECT 
                gr.*,
                ga.user_id
            FROM github_repos gr
            JOIN github_accounts ga ON gr.account_id = ga.id
            WHERE gr.id = $1 AND ga.user_id = $2
        """, UUID(repo_id), current_user.id)
        
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        return GitHubRepo(
            id=str(repo['id']),
            name=repo['name'],
            full_name=repo['full_name'],
            description=repo['description'],
            language=repo['language'],
            stars=repo['stars'],
            forks=repo['forks'],
            is_private=repo['is_private'],
            default_branch=repo['default_branch'],
            last_synced=repo['last_synced_at']
        )

@router.get("/languages")
async def get_languages(
    current_user = Depends(get_current_user)
):
    """Get all programming languages from user's repos"""
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        languages = await db.fetch("""
            SELECT DISTINCT language, COUNT(*) as repo_count
            FROM github_repos gr
            JOIN github_accounts ga ON gr.account_id = ga.id
            WHERE ga.user_id = $1 AND language IS NOT NULL
            GROUP BY language
            ORDER BY repo_count DESC
        """, current_user.id)
        
        return [
            {"language": l['language'], "repo_count": l['repo_count']}
            for l in languages
        ]

@router.get("/repos/by-slug/{slug}")
async def get_repo_by_slug(
    slug: str,
    current_user = Depends(get_current_user)
) -> GitHubRepo:
    """Get repository by slug"""
    
    pool = await get_db_pool()
    async with pool.acquire() as db:
        repo = await db.fetchrow("""
            SELECT gr.* FROM github_repos gr
            JOIN github_accounts ga ON gr.account_id = ga.id
            WHERE gr.slug = $1 AND ga.user_id = $2
        """, slug, current_user.id)
        
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        return GitHubRepo(
            id=str(repo['id']),
            name=repo['name'],
            full_name=repo['full_name'],
            description=repo['description'],
            language=repo['language'],
            stars=repo['stars'],
            forks=repo['forks'],
            is_private=repo['is_private'],
            default_branch=repo['default_branch'],
            last_synced=repo['last_synced_at']
        )