"""
User Profile API endpoints
Handles user profile management, settings, and preferences
"""

from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from app.db.database import get_db_pool
from app.middleware.user_context import require_user, require_user_id
from app.core.exceptions import InternalServerError

router = APIRouter()


class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_type: str = "individual"
    is_active: bool = True
    is_verified: bool = False
    onboarding_completed: bool = False
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserStats(BaseModel):
    total_items: int
    total_tags: int
    items_this_month: int
    last_capture: Optional[datetime] = None


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(user_id: UUID = Depends(require_user_id)):
    """Get the current user's profile information."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            user_row = await conn.fetchrow("""
                SELECT 
                    id, email, name, first_name, last_name, user_type,
                    is_active, is_verified, onboarding_completed,
                    created_at, updated_at, last_login_at
                FROM users 
                WHERE id = $1
            """, user_id)
            
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserProfile(**dict(user_row))
            
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve user profile: {e}")


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    update_data: UpdateProfileRequest,
    user_id: UUID = Depends(require_user_id)
):
    """Update the current user's profile information."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Build dynamic update query
            update_fields = []
            params = [user_id]
            param_count = 1
            
            if update_data.name is not None:
                param_count += 1
                update_fields.append(f"name = ${param_count}")
                params.append(update_data.name)
            
            if update_data.first_name is not None:
                param_count += 1
                update_fields.append(f"first_name = ${param_count}")
                params.append(update_data.first_name)
            
            if update_data.last_name is not None:
                param_count += 1
                update_fields.append(f"last_name = ${param_count}")
                params.append(update_data.last_name)
            
            if not update_fields:
                # No updates provided, just return current profile
                return await get_user_profile(user_id)
            
            # Add updated_at
            param_count += 1
            update_fields.append(f"updated_at = ${param_count}")
            params.append(datetime.now())
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = $1
                RETURNING 
                    id, email, name, first_name, last_name, user_type,
                    is_active, is_verified, onboarding_completed,
                    created_at, updated_at, last_login_at
            """
            
            user_row = await conn.fetchrow(query, *params)
            
            if not user_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserProfile(**dict(user_row))
            
    except Exception as e:
        raise InternalServerError(f"Failed to update user profile: {e}")


@router.post("/profile/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    user_id: UUID = Depends(require_user_id)
):
    """Change the current user's password."""
    try:
        import bcrypt
        
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get current password hash
            current_hash = await conn.fetchval(
                "SELECT password_hash FROM users WHERE id = $1",
                user_id
            )
            
            if not current_hash:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not bcrypt.checkpw(password_data.current_password.encode('utf-8'), current_hash.encode('utf-8')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Hash new password
            new_hash = bcrypt.hashpw(password_data.new_password.encode('utf-8'), bcrypt.gensalt())
            
            # Update password
            await conn.execute("""
                UPDATE users 
                SET password_hash = $1, updated_at = $2
                WHERE id = $3
            """, new_hash.decode('utf-8'), datetime.now(), user_id)
            
            return {"message": "Password changed successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        raise InternalServerError(f"Failed to change password: {e}")


@router.get("/profile/stats", response_model=UserStats)
async def get_user_stats(user_id: UUID = Depends(require_user_id)):
    """Get user statistics for dashboard."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Get user statistics
            stats_row = await conn.fetchrow("""
                SELECT 
                    COUNT(i.id) as total_items,
                    COUNT(DISTINCT t.id) as total_tags,
                    COUNT(CASE WHEN i.created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as items_this_month,
                    MAX(i.created_at) as last_capture
                FROM items i
                LEFT JOIN item_tags it ON i.id = it.item_id
                LEFT JOIN tags t ON it.tag_id = t.id AND t.user_id = $1
                WHERE i.user_id = $1
            """, user_id)
            
            return UserStats(**dict(stats_row))
            
    except Exception as e:
        raise InternalServerError(f"Failed to retrieve user stats: {e}")


@router.delete("/profile")
async def delete_user_account(user_id: UUID = Depends(require_user_id)):
    """Delete the current user's account and all associated data."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Start transaction
            async with conn.transaction():
                # Delete all user data (cascade should handle most of this)
                await conn.execute("DELETE FROM users WHERE id = $1", user_id)
            
            return {"message": "Account deleted successfully"}
            
    except Exception as e:
        raise InternalServerError(f"Failed to delete account: {e}")


@router.post("/profile/complete-onboarding")
async def complete_onboarding(user_id: UUID = Depends(require_user_id)):
    """Mark the user's onboarding as completed."""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE users 
                SET onboarding_completed = true, updated_at = $1
                WHERE id = $2
            """, datetime.now(), user_id)
            
            return {"message": "Onboarding completed successfully"}
            
    except Exception as e:
        raise InternalServerError(f"Failed to complete onboarding: {e}")