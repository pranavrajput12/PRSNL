"""
PRSNL CodeMirror Workers Package

Enterprise-grade distributed task processing using Celery.
"""

from .celery_app import celery_app

__all__ = ['celery_app']