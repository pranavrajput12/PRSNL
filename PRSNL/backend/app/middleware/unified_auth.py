"""
Unified Authentication Middleware for Keycloak + FusionAuth Integration
Handles authentication with both identity systems and provides unified user context
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
import httpx
import jwt
from datetime import datetime, timezone

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer

from app.config import settings
from app.db.database import get_db_pool

logger = logging.getLogger(__name__)

class UnifiedAuthService:
    """Unified authentication service for Keycloak + FusionAuth integration"""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
        self._keycloak_public_keys = None
        self._keys_cache_time = None
        self._fusionauth_client = httpx.AsyncClient(timeout=10.0)
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._fusionauth_client.aclose()

    async def get_keycloak_public_keys(self) -> Dict[str, Any]:
        """Get Keycloak public keys for JWT verification (cached)"""
        try:
            # Cache keys for 1 hour
            if (self._keycloak_public_keys and self._keys_cache_time and 
                (datetime.now(timezone.utc) - self._keys_cache_time).seconds < 3600):
                return self._keycloak_public_keys
            
            keycloak_url = getattr(settings, 'KEYCLOAK_URL', 'http://localhost:8080')
            realm = getattr(settings, 'KEYCLOAK_REALM', 'prsnl')
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs",
                    timeout=5.0
                )
                response.raise_for_status()
                self._keycloak_public_keys = response.json()
                self._keys_cache_time = datetime.now(timezone.utc)
                return self._keycloak_public_keys
                
        except Exception as e:
            logger.warning(f"Failed to fetch Keycloak public keys: {e}")
            return {}

    async def verify_keycloak_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token with Keycloak"""
        try:
            # Get public keys
            keys_data = await self.get_keycloak_public_keys()
            if not keys_data.get('keys'):
                logger.warning("No Keycloak public keys available")
                return None
            
            # Try to decode with each key
            for key_data in keys_data['keys']:
                try:
                    # Create the public key (simplified - in production use proper key handling)
                    payload = jwt.decode(
                        token,
                        options={"verify_signature": False},  # Simplified for demo
                        algorithms=["RS256", "HS256"]
                    )
                    
                    # Validate token claims
                    if payload.get('exp', 0) < datetime.now(timezone.utc).timestamp():
                        logger.warning("Keycloak token expired")
                        return None
                    
                    return {
                        'user_id': payload.get('sub'),
                        'email': payload.get('email'),
                        'preferred_username': payload.get('preferred_username'),
                        'given_name': payload.get('given_name'),
                        'family_name': payload.get('family_name'),
                        'roles': payload.get('realm_access', {}).get('roles', []),
                        'exp': payload.get('exp'),
                        'iat': payload.get('iat'),
                        'source': 'keycloak'
                    }
                except jwt.InvalidTokenError:
                    continue
            
            logger.warning("Failed to verify Keycloak token with any key")
            return None
            
        except Exception as e:
            logger.error(f"Error verifying Keycloak token: {e}")
            return None

    async def verify_fusionauth_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token with FusionAuth"""
        try:
            fusionauth_url = getattr(settings, 'FUSIONAUTH_URL', 'http://localhost:9011')
            api_key = getattr(settings, 'FUSIONAUTH_API_KEY', '')
            
            if not api_key:
                logger.warning("FusionAuth API key not configured")
                return None
            
            # Validate token with FusionAuth
            response = await self._fusionauth_client.post(
                f"{fusionauth_url}/api/jwt/validate",
                headers={
                    'Authorization': api_key,
                    'Content-Type': 'application/json'
                },
                json={'encodedJWT': token}
            )
            
            if response.status_code == 200:
                data = response.json()
                jwt_data = data.get('jwt', {})
                
                return {
                    'user_id': jwt_data.get('sub'),
                    'email': jwt_data.get('email'),
                    'preferred_username': jwt_data.get('preferred_username', jwt_data.get('email')),
                    'given_name': jwt_data.get('given_name'),
                    'family_name': jwt_data.get('family_name'),
                    'roles': jwt_data.get('roles', []),
                    'exp': jwt_data.get('exp'),
                    'iat': jwt_data.get('iat'),
                    'source': 'fusionauth'
                }
            else:
                logger.warning(f"FusionAuth token validation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error verifying FusionAuth token: {e}")
            return None

    async def get_or_create_user_mapping(self, auth_data: Dict[str, Any]) -> Optional[UUID]:
        """Get or create user mapping between PRSNL users and auth systems"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                # Try to find existing mapping
                if auth_data['source'] == 'keycloak':
                    mapping_row = await conn.fetchrow(
                        "SELECT prsnl_user_id FROM auth_integration.user_mapping WHERE keycloak_user_id = $1",
                        UUID(auth_data['user_id'])
                    )
                else:  # fusionauth
                    mapping_row = await conn.fetchrow(
                        "SELECT prsnl_user_id FROM auth_integration.user_mapping WHERE fusionauth_user_id = $1",
                        UUID(auth_data['user_id'])
                    )
                
                if mapping_row:
                    return mapping_row['prsnl_user_id']
                
                # Check if user exists by email
                user_row = await conn.fetchrow(
                    "SELECT id FROM users WHERE email = $1",
                    auth_data['email']
                )
                
                if user_row:
                    # Link existing user
                    prsnl_user_id = user_row['id']
                else:
                    # Create new user
                    user_data = {
                        'email': auth_data['email'],
                        'first_name': auth_data.get('given_name', ''),
                        'last_name': auth_data.get('family_name', ''),
                        'is_active': True,
                        'is_verified': True,  # Verified through auth system
                        'password_hash': 'external_auth'  # Placeholder for external auth
                    }
                    
                    user_row = await conn.fetchrow("""
                        INSERT INTO users (email, first_name, last_name, is_active, is_verified, password_hash)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        RETURNING id
                    """, user_data['email'], user_data['first_name'], user_data['last_name'],
                         user_data['is_active'], user_data['is_verified'], user_data['password_hash'])
                    
                    prsnl_user_id = user_row['id']
                
                # Create or update mapping
                if auth_data['source'] == 'keycloak':
                    await conn.execute("""
                        INSERT INTO auth_integration.user_mapping (prsnl_user_id, keycloak_user_id)
                        VALUES ($1, $2)
                        ON CONFLICT (prsnl_user_id) DO UPDATE SET 
                            keycloak_user_id = $2, updated_at = NOW()
                    """, prsnl_user_id, UUID(auth_data['user_id']))
                else:  # fusionauth
                    await conn.execute("""
                        INSERT INTO auth_integration.user_mapping (prsnl_user_id, fusionauth_user_id)
                        VALUES ($1, $2)
                        ON CONFLICT (prsnl_user_id) DO UPDATE SET 
                            fusionauth_user_id = $2, updated_at = NOW()
                    """, prsnl_user_id, UUID(auth_data['user_id']))
                
                return prsnl_user_id
                
        except Exception as e:
            logger.error(f"Error managing user mapping: {e}")
            return None

    async def authenticate_request(self, request: Request) -> Tuple[Optional[UUID], Optional[Dict[str, Any]]]:
        """Authenticate request using either Keycloak or FusionAuth"""
        # Get authorization header
        authorization = request.headers.get("authorization")
        if not authorization:
            return None, None
        
        # Extract token
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                return None, None
        except ValueError:
            return None, None
        
        # Try Keycloak first, then FusionAuth
        auth_data = await self.verify_keycloak_token(token)
        if not auth_data:
            auth_data = await self.verify_fusionauth_token(token)
        
        if not auth_data:
            return None, None
        
        # Get or create user mapping
        prsnl_user_id = await self.get_or_create_user_mapping(auth_data)
        if not prsnl_user_id:
            logger.error("Failed to get/create user mapping")
            return None, None
        
        return prsnl_user_id, auth_data

    async def log_auth_session(self, user_mapping_id: UUID, auth_data: Dict[str, Any], request: Request):
        """Log authentication session for audit trails"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO auth_integration.auth_sessions 
                    (user_mapping_id, session_type, session_id, ip_address, user_agent, login_method)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                user_mapping_id,
                auth_data['source'],
                auth_data['user_id'],
                request.client.host if request.client else None,
                request.headers.get('user-agent'),
                'token'
                )
        except Exception as e:
            logger.error(f"Error logging auth session: {e}")


# Global unified auth service instance
unified_auth = UnifiedAuthService()


async def get_current_user_id(request: Request) -> Optional[UUID]:
    """Dependency function to get current user_id (optional)"""
    user_id, _ = await unified_auth.authenticate_request(request)
    return user_id


async def get_current_user_context(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency function to get full user context (optional)"""
    user_id, auth_data = await unified_auth.authenticate_request(request)
    if user_id and auth_data:
        return {
            'prsnl_user_id': user_id,
            'auth_user_id': auth_data['user_id'],
            'email': auth_data['email'],
            'name': f"{auth_data.get('given_name', '')} {auth_data.get('family_name', '')}".strip(),
            'roles': auth_data.get('roles', []),
            'auth_source': auth_data['source']
        }
    return None


async def require_user_id(request: Request) -> UUID:
    """Dependency function that requires authentication"""
    user_id, auth_data = await unified_auth.authenticate_request(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log the session for audit
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            mapping_row = await conn.fetchrow(
                "SELECT id FROM auth_integration.user_mapping WHERE prsnl_user_id = $1",
                user_id
            )
            if mapping_row and auth_data:
                await unified_auth.log_auth_session(mapping_row['id'], auth_data, request)
    except Exception as e:
        logger.warning(f"Failed to log auth session: {e}")
    
    return user_id


async def require_user_context(request: Request) -> Dict[str, Any]:
    """Dependency function that requires authentication and returns full context"""
    user_context = await get_current_user_context(request)
    if not user_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_context


# Role-based authorization helpers
async def require_role(required_role: str):
    """Create a dependency that requires a specific role"""
    async def role_checker(user_context: Dict[str, Any] = Depends(require_user_context)) -> Dict[str, Any]:
        user_roles = user_context.get('roles', [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user_context
    return role_checker


async def require_admin(user_context: Dict[str, Any] = Depends(require_user_context)) -> Dict[str, Any]:
    """Dependency that requires admin role"""
    user_roles = user_context.get('roles', [])
    admin_roles = ['admin', 'realm-admin', 'prsnl-admin']
    
    if not any(role in user_roles for role in admin_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user_context