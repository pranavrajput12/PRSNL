"""
Simple auth placeholder for video streaming endpoints
"""

from typing import Optional


async def get_current_user(token: Optional[str] = None) -> Optional[dict]:
    """
    Placeholder auth function - returns None (no auth required)
    In production, this would validate the token and return user info
    """
    return None


async def get_current_user_optional(token: Optional[str] = None) -> Optional[dict]:
    """
    Optional auth function - same as get_current_user but explicitly optional
    """
    return None