"""
Content fingerprinting utilities for duplicate detection
"""
import hashlib
from typing import Optional


def calculate_content_fingerprint(content: str) -> str:
    """
    Calculate SHA-256 fingerprint of content.
    
    Args:
        content: The raw content to fingerprint
        
    Returns:
        SHA-256 hash as hex string (64 characters)
    """
    if not content:
        return ""
    
    # Normalize content for consistent fingerprinting
    # Remove extra whitespace and convert to lowercase
    normalized = " ".join(content.lower().split())
    
    # Calculate SHA-256 hash
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def content_has_changed(old_content: Optional[str], new_content: str, old_fingerprint: Optional[str]) -> bool:
    """
    Check if content has changed by comparing fingerprints.
    
    Args:
        old_content: Previous content (if available)
        new_content: New content to check
        old_fingerprint: Previous fingerprint (if available)
        
    Returns:
        True if content has changed, False otherwise
    """
    if not old_fingerprint and not old_content:
        # No previous content to compare
        return True
    
    new_fingerprint = calculate_content_fingerprint(new_content)
    
    if old_fingerprint:
        # Compare fingerprints if available
        return new_fingerprint != old_fingerprint
    else:
        # Calculate old fingerprint and compare
        old_fingerprint = calculate_content_fingerprint(old_content or "")
        return new_fingerprint != old_fingerprint


def is_duplicate(new_content: str, existing_fingerprint: str) -> bool:
    """
    Check if content is a duplicate of existing content.
    
    Args:
        new_content: New content to check
        existing_fingerprint: Fingerprint of existing content
        
    Returns:
        True if content is a duplicate, False otherwise
    """
    new_fingerprint = calculate_content_fingerprint(new_content)
    return new_fingerprint == existing_fingerprint