"""
Simple auth placeholder for video streaming endpoints
"""

from typing import Optional
from uuid import UUID


class User:
    """Simple user class for development"""
    def __init__(self, id: str, email: str, name: str):
        # Handle both UUID and string IDs for flexibility
        try:
            self.id = UUID(id)
        except ValueError:
            # If not a valid UUID, keep as string (for temp-user-for-oauth)
            self.id = id
        self.email = email
        self.name = name


async def get_current_user(token: Optional[str] = None) -> Optional[User]:
    """
    Placeholder auth function - returns test user for development
    In production, this would validate the token and return user info
    """
    # Return a test user object with required id field
    # Using the user_id from the database that owns the test repos
    return User(
        id="temp-user-for-oauth",  # Actual user_id from database
        email="test@example.com",
        name="Test User"
    )


async def get_current_user_optional(token: Optional[str] = None) -> Optional[dict]:
    """
    Optional auth function - same as get_current_user but explicitly optional
    """
    return None