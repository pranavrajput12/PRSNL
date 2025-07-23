"""
Email service using Resend for PRSNL
Handles email verification and magic link authentication
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from uuid import UUID
import secrets
import json

import resend
from jinja2 import Template

from app.config import settings
from app.db.database import get_db_pool
from app.services.email.email_config import EmailType, EMAIL_CONFIG, SUBJECT_TEMPLATES

logger = logging.getLogger(__name__)

# Initialize Resend client
if settings.RESEND_API_KEY:
    resend.api_key = settings.RESEND_API_KEY
else:
    logger.warning("Resend API key not configured - emails will not be sent")


class EmailService:
    """Service for sending emails via Resend"""
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @classmethod
    async def send_email(
        cls,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Send an email using Resend
        
        Returns:
            Message ID if successful, None if failed
        """
        if not settings.RESEND_API_KEY:
            logger.warning(f"Email not sent (no API key): {subject} to {to}")
            return None
        
        try:
            params = {
                "from": f"{from_name or settings.EMAIL_FROM_NAME} <{from_email or settings.EMAIL_FROM_ADDRESS}>",
                "to": [to],
                "subject": subject,
                "html": html,
            }
            
            if text:
                params["text"] = text
            
            response = resend.Emails.send(params)
            
            # Log email sending
            await cls._log_email(
                email_to=to,
                email_type="custom",
                subject=subject,
                status="sent",
                provider_message_id=response.get("id")
            )
            
            logger.info(f"Email sent successfully: {subject} to {to}")
            return response.get("id")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            
            # Log failed email
            await cls._log_email(
                email_to=to,
                email_type="custom",
                subject=subject,
                status="failed",
                error_message=str(e)
            )
            
            return None
    
    @classmethod
    async def send_verification_email(cls, user_id: UUID, email: str, name: str) -> bool:
        """Send email verification link"""
        try:
            # Generate verification token
            token = cls.generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=24)
            
            pool = await get_db_pool()
            async with pool.acquire() as db:
                # Save token to user
                await db.execute("""
                    UPDATE users 
                    SET email_verification_token = $1,
                        email_verification_token_expires = $2
                    WHERE id = $3
                """, token, expires_at, user_id)
                
                # Get email template
                template = await db.fetchrow("""
                    SELECT subject, html_template, text_template 
                    FROM email_templates 
                    WHERE name = 'email_verification' AND is_active = true
                """)
                
                if not template:
                    logger.error("Email verification template not found")
                    return False
                
                # Build verification link
                verification_link = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"
                
                # Render templates
                html_template = Template(template["html_template"])
                text_template = Template(template["text_template"])
                
                html = html_template.render(
                    verification_link=verification_link,
                    user_name=name
                )
                text = text_template.render(
                    verification_link=verification_link,
                    user_name=name
                )
                
                # Send email with verification-specific from address
                config = EMAIL_CONFIG[EmailType.VERIFICATION]
                message_id = await cls.send_email(
                    to=email,
                    subject=SUBJECT_TEMPLATES[EmailType.VERIFICATION],
                    html=html,
                    text=text,
                    from_email=config["from"],
                    from_name=config["from_name"]
                )
                
                if message_id:
                    await cls._log_email(
                        user_id=user_id,
                        email_to=email,
                        email_type="verification",
                        template_name="email_verification",
                        subject=template["subject"],
                        status="sent",
                        provider_message_id=message_id,
                        metadata={"token": token[:8] + "..."}  # Log partial token for debugging
                    )
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            return False
    
    @classmethod
    async def send_magic_link(cls, email: str) -> Dict[str, Any]:
        """Send magic link for passwordless login"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as db:
                # Check if user exists
                user = await db.fetchrow(
                    "SELECT id, first_name, last_name FROM users WHERE email = $1",
                    email
                )
                
                if not user:
                    # Don't reveal if user exists or not for security
                    return {"success": True, "message": "If an account exists, a magic link has been sent"}
                
                # Generate magic link token
                token = cls.generate_token(48)
                expires_at = datetime.utcnow() + timedelta(minutes=15)
                
                # Save magic link
                await db.execute("""
                    INSERT INTO magic_links (user_id, email, token, expires_at)
                    VALUES ($1, $2, $3, $4)
                """, user["id"], email, token, expires_at)
                
                # Get email template
                template = await db.fetchrow("""
                    SELECT subject, html_template, text_template 
                    FROM email_templates 
                    WHERE name = 'magic_link' AND is_active = true
                """)
                
                if not template:
                    logger.error("Magic link template not found")
                    return {"success": False, "message": "Email template not configured"}
                
                # Build magic link
                magic_link = f"{settings.FRONTEND_URL}/auth/magic-link?token={token}"
                
                # Render templates
                html_template = Template(template["html_template"])
                text_template = Template(template["text_template"])
                
                html = html_template.render(
                    magic_link=magic_link,
                    user_email=email
                )
                text = text_template.render(
                    magic_link=magic_link,
                    user_email=email
                )
                
                # Send email with magic link-specific from address
                config = EMAIL_CONFIG[EmailType.MAGIC_LINK]
                message_id = await cls.send_email(
                    to=email,
                    subject=SUBJECT_TEMPLATES[EmailType.MAGIC_LINK],
                    html=html,
                    text=text,
                    from_email=config["from"],
                    from_name=config["from_name"]
                )
                
                if message_id:
                    await cls._log_email(
                        user_id=user["id"],
                        email_to=email,
                        email_type="magic_link",
                        template_name="magic_link",
                        subject=template["subject"],
                        status="sent",
                        provider_message_id=message_id,
                        metadata={"token": token[:8] + "...", "expires_at": expires_at.isoformat()}
                    )
                    
                    return {"success": True, "message": "Magic link sent successfully"}
                
                return {"success": False, "message": "Failed to send email"}
                
        except Exception as e:
            logger.error(f"Failed to send magic link: {e}")
            return {"success": False, "message": "An error occurred"}
    
    @classmethod
    async def send_password_reset_email(cls, user_id: UUID, email: str, name: str) -> bool:
        """Send password reset email with secure reset link"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as db:
                # Get the password reset token (should be created before calling this method)
                token_info = await db.fetchrow("""
                    SELECT token, expires_at 
                    FROM password_resets 
                    WHERE user_id = $1 AND used_at IS NULL
                    ORDER BY created_at DESC
                    LIMIT 1
                """, user_id)
                
                if not token_info:
                    logger.error(f"No password reset token found for user {user_id}")
                    return False
                
                # Get email template
                template = await db.fetchrow("""
                    SELECT subject, html_template, text_template 
                    FROM email_templates 
                    WHERE name = 'password_reset' AND is_active = true
                """)
                
                if not template:
                    logger.error("Password reset template not found")
                    return False
                
                # Build reset link
                reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={token_info['token']}"
                
                # Render templates
                html_template = Template(template["html_template"])
                text_template = Template(template["text_template"])
                
                html = html_template.render(
                    user_name=name,
                    reset_link=reset_link
                )
                text = text_template.render(
                    user_name=name,
                    reset_link=reset_link
                )
                
                # Get email config
                config = EMAIL_CONFIG[EmailType.PASSWORD_RESET]
                
                # Send email
                message_id = await cls.send_email(
                    to=email,
                    subject=template["subject"],
                    html=html,
                    text=text,
                    from_email=config["from"],
                    from_name=config["from_name"]
                )
                
                if message_id:
                    # Log successful email
                    await cls._log_email(
                        db=db,
                        user_id=user_id,
                        email_to=email,
                        email_type="password_reset",
                        template_name="password_reset",
                        subject=template["subject"],
                        status="sent",
                        provider_message_id=message_id,
                        metadata={
                            "token": token_info["token"][:8] + "...", 
                            "expires_at": token_info["expires_at"].isoformat()
                        }
                    )
                    
                    logger.info(f"Password reset email sent successfully to {email}")
                    return True
                
                # Log failed email
                await cls._log_email(
                    db=db,
                    user_id=user_id,
                    email_to=email,
                    email_type="password_reset",
                    template_name="password_reset",
                    subject=template["subject"],
                    status="failed",
                    metadata={"token": token_info["token"][:8] + "..."}
                )
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            return False
    
    @classmethod
    async def send_welcome_email(cls, user_id: UUID, email: str, name: str) -> bool:
        """Send welcome email after successful verification"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as db:
                # Get email template
                template = await db.fetchrow("""
                    SELECT subject, html_template, text_template 
                    FROM email_templates 
                    WHERE name = 'welcome' AND is_active = true
                """)
                
                if not template:
                    logger.warning("Welcome email template not found")
                    return False
                
                # Render templates
                html_template = Template(template["html_template"])
                text_template = Template(template["text_template"])
                
                html = html_template.render(
                    user_name=name,
                    app_link=settings.FRONTEND_URL
                )
                text = text_template.render(
                    user_name=name,
                    app_link=settings.FRONTEND_URL
                )
                
                # Send email with welcome-specific from address
                config = EMAIL_CONFIG[EmailType.WELCOME]
                message_id = await cls.send_email(
                    to=email,
                    subject=SUBJECT_TEMPLATES[EmailType.WELCOME],
                    html=html,
                    text=text,
                    from_email=config["from"],
                    from_name=config["from_name"]
                )
                
                if message_id:
                    await cls._log_email(
                        user_id=user_id,
                        email_to=email,
                        email_type="welcome",
                        template_name="welcome",
                        subject=template["subject"],
                        status="sent",
                        provider_message_id=message_id
                    )
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
    
    @classmethod
    async def verify_email_token(cls, token: str) -> Optional[UUID]:
        """Verify email verification token and mark user as verified"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as db:
                # Find user with valid token
                user = await db.fetchrow("""
                    SELECT id, email, first_name, last_name
                    FROM users 
                    WHERE email_verification_token = $1 
                    AND email_verification_token_expires > NOW()
                    AND is_verified = false
                """, token)
                
                if not user:
                    return None
                
                # Mark user as verified
                await db.execute("""
                    UPDATE users 
                    SET is_verified = true,
                        email_verified_at = NOW(),
                        email_verification_token = NULL,
                        email_verification_token_expires = NULL
                    WHERE id = $1
                """, user["id"])
                
                # Send welcome email
                name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or user["email"]
                await cls.send_welcome_email(user["id"], user["email"], name)
                
                return user["id"]
                
        except Exception as e:
            logger.error(f"Failed to verify email token: {e}")
            return None
    
    @classmethod
    async def verify_magic_link(cls, token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Verify magic link token and return user info"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as db:
                # Find valid magic link
                link = await db.fetchrow("""
                    SELECT ml.*, u.id as user_id, u.email, u.first_name, u.last_name, u.is_verified
                    FROM magic_links ml
                    JOIN users u ON ml.user_id = u.id
                    WHERE ml.token = $1 
                    AND ml.expires_at > NOW()
                    AND ml.used_at IS NULL
                """, token)
                
                if not link:
                    return None
                
                # Mark link as used
                await db.execute("""
                    UPDATE magic_links 
                    SET used_at = NOW(),
                        ip_address = $1,
                        user_agent = $2
                    WHERE id = $3
                """, ip_address, user_agent, link["id"])
                
                # Update last login
                await db.execute(
                    "UPDATE users SET last_login_at = NOW() WHERE id = $1",
                    link["user_id"]
                )
                
                return {
                    "user_id": str(link["user_id"]),
                    "email": link["email"],
                    "first_name": link["first_name"],
                    "last_name": link["last_name"],
                    "is_verified": link["is_verified"]
                }
                
        except Exception as e:
            logger.error(f"Failed to verify magic link: {e}")
            return None
    
    @classmethod
    async def _log_email(
        cls,
        email_to: str,
        email_type: str,
        subject: str,
        status: str,
        user_id: Optional[UUID] = None,
        template_name: Optional[str] = None,
        provider_message_id: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log email sending attempt"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as db:
                await db.execute("""
                    INSERT INTO email_logs (
                        user_id, email_to, email_type, template_name, 
                        subject, status, provider_message_id, 
                        error_message, metadata, sent_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
                """, 
                    user_id, email_to, email_type, template_name,
                    subject, status, provider_message_id,
                    error_message, json.dumps(metadata or {}),
                    datetime.utcnow() if status == "sent" else None
                )
        except Exception as e:
            logger.error(f"Failed to log email: {e}")
    
    @classmethod
    async def cleanup_expired_tokens(cls):
        """Clean up expired tokens and links"""
        try:
            pool = await get_db_pool()
            async with pool.acquire() as db:
                # Clean up expired magic links
                deleted_links = await db.fetchval(
                    "SELECT cleanup_expired_magic_links()"
                )
                
                # Clean up expired email verification tokens
                deleted_tokens = await db.fetchval(
                    "SELECT cleanup_expired_email_tokens()"
                )
                
                logger.info(f"Cleaned up expired tokens and links")
                
        except Exception as e:
            logger.error(f"Failed to clean up expired tokens: {e}")