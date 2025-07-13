"""
Sentry error tracking and performance monitoring configuration
"""
import logging

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.config import settings

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize Sentry error tracking and performance monitoring"""
    
    # Skip initialization if no DSN is provided
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping Sentry initialization")
        return
    
    try:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",
                    failed_request_status_codes=[400, 401, 403, 404, 405, 500, 501, 502, 503, 504],
                ),
                StarletteIntegration(
                    transaction_style="endpoint",
                    failed_request_status_codes=[400, 401, 403, 404, 405, 500, 501, 502, 503, 504],
                ),
                SqlalchemyIntegration(),
                RedisIntegration(),
                AsyncioIntegration(),
                LoggingIntegration(
                    level=logging.INFO,        # Capture info and above as breadcrumbs
                    event_level=logging.ERROR   # Send errors as events
                ),
            ],
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
            request_bodies="medium",  # Capture request bodies for better debugging
            with_locals=True,         # Capture local variables in stack traces
            
            # Performance monitoring
            enable_tracing=True,
            
            # Release tracking
            release=f"prsnl-backend@{settings.VERSION}",
            
            # Before send hook for filtering
            before_send=before_send_filter,
            
            # Ignore certain errors
            ignore_errors=[
                KeyboardInterrupt,
                SystemExit,
                GeneratorExit,
            ],
        )
        
        logger.info(f"Sentry initialized successfully for environment: {settings.ENVIRONMENT}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """
    Filter or modify events before sending to Sentry
    """
    # Don't send events in development unless explicitly enabled
    if settings.ENVIRONMENT == "development" and not settings.SENTRY_ENABLE_IN_DEV:
        return None
    
    # Filter out health check endpoints
    if event.get("request", {}).get("url", "").endswith("/health"):
        return None
    
    # Filter out expected 404s for certain paths
    if event.get("exception", {}).get("values", [{}])[0].get("type") == "HTTPException":
        if event.get("extra", {}).get("status_code") == 404:
            path = event.get("request", {}).get("url", "")
            # Skip 404s for common bot paths
            if any(bot_path in path for bot_path in [".php", ".asp", "wp-admin", "robots.txt"]):
                return None
    
    return event


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture a custom message to Sentry
    """
    if settings.SENTRY_DSN:
        sentry_sdk.capture_message(message, level=level, **kwargs)


def capture_exception(exception: Exception, **kwargs):
    """
    Capture an exception to Sentry
    """
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exception, **kwargs)