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
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
import sentry_sdk.profiler

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
                HttpxIntegration(),  # New in 2.33.0 - Better HTTP client tracking
                AioHttpIntegration(),  # New in 2.33.0 - Async HTTP client tracking
            ],
            # Profiling configuration (Enhanced in 2.33.0)
            profiles_sampler=profiles_sampler,  # Dynamic profile sampling
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


def profiles_sampler(sampling_context):
    """
    Dynamic profiling sampler for Sentry 2.33.0
    Allows conditional profiling based on transaction characteristics
    """
    # Always profile slow transactions
    if sampling_context.get("transaction_context", {}).get("op") == "http.server":
        # Get transaction name
        transaction_name = sampling_context.get("transaction_context", {}).get("name", "")
        
        # High-priority endpoints get higher sampling
        if any(endpoint in transaction_name for endpoint in ["/api/ai/", "/api/rag/", "/api/codemirror/"]):
            return 0.5  # 50% sampling for AI endpoints
        elif "/api/" in transaction_name:
            return 0.1  # 10% sampling for other API endpoints
        else:
            return 0.01  # 1% sampling for static content
    
    # Default sampling rate
    return settings.SENTRY_PROFILES_SAMPLE_RATE


def set_transaction_tag(key: str, value: str):
    """
    Set a tag on the current transaction for better profiling insights
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag(key, value)


def profile_function(func):
    """
    Decorator to profile specific functions with Sentry 2.33.0
    """
    def wrapper(*args, **kwargs):
        with sentry_sdk.start_transaction(op="function", name=func.__name__) as transaction:
            transaction.set_tag("function.module", func.__module__)
            try:
                result = func(*args, **kwargs)
                transaction.set_status("ok")
                return result
            except Exception as e:
                transaction.set_status("internal_error")
                raise
    return wrapper