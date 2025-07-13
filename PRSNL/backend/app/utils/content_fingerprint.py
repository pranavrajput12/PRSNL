"""
Content Fingerprinting Utilities for PRSNL

Provides SHA-256 fingerprinting for content deduplication and versioning.
"""

import hashlib
import json
from typing import Any, Dict, Optional


def generate_content_fingerprint(raw_content: Optional[str]) -> Optional[str]:
    """
    Generate SHA-256 hash of raw content for deduplication.
    
    Args:
        raw_content: The raw content string to hash
        
    Returns:
        SHA-256 hash string (64 characters) or None if content is empty
    """
    if not raw_content or not raw_content.strip():
        return None
    
    # Normalize content for consistent hashing
    normalized_content = raw_content.strip()
    
    # Generate SHA-256 hash
    content_hash = hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
    
    return content_hash


def generate_metadata_fingerprint(metadata: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Generate SHA-256 hash of metadata for versioning.
    
    Args:
        metadata: The metadata dict to hash
        
    Returns:
        SHA-256 hash string or None if metadata is empty
    """
    if not metadata:
        return None
    
    # Sort metadata keys for consistent hashing
    normalized_metadata = json.dumps(metadata, sort_keys=True, separators=(',', ':'))
    
    # Generate SHA-256 hash
    metadata_hash = hashlib.sha256(normalized_metadata.encode('utf-8')).hexdigest()
    
    return metadata_hash


def is_content_duplicate(existing_fingerprint: Optional[str], new_content: Optional[str]) -> bool:
    """
    Check if content is duplicate based on fingerprints.
    
    Args:
        existing_fingerprint: Existing content fingerprint
        new_content: New content to check
        
    Returns:
        True if content is duplicate, False otherwise
    """
    if not existing_fingerprint or not new_content:
        return False
    
    new_fingerprint = generate_content_fingerprint(new_content)
    return existing_fingerprint == new_fingerprint


def should_update_content(
    existing_fingerprint: Optional[str], 
    new_content: Optional[str],
    force_update: bool = False
) -> bool:
    """
    Determine if content should be updated based on fingerprint comparison.
    
    Args:
        existing_fingerprint: Current content fingerprint
        new_content: New content to potentially update to
        force_update: Force update regardless of fingerprint
        
    Returns:
        True if content should be updated, False otherwise
    """
    if force_update:
        return True
    
    if not new_content:
        return False
    
    # If no existing fingerprint, we should update
    if not existing_fingerprint:
        return True
    
    # Update only if content has changed
    return not is_content_duplicate(existing_fingerprint, new_content)


class ContentFingerprintManager:
    """Manager for content fingerprinting operations."""
    
    @staticmethod
    def process_item_content(item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process item data and add content fingerprint.
        
        Args:
            item_data: Item data dictionary
            
        Returns:
            Updated item data with content_fingerprint
        """
        raw_content = item_data.get('raw_content') or item_data.get('content')
        
        if raw_content:
            fingerprint = generate_content_fingerprint(raw_content)
            item_data['content_fingerprint'] = fingerprint
        
        return item_data
    
    @staticmethod
    def detect_duplicates_by_fingerprint(fingerprint: str, exclude_id: Optional[str] = None) -> str:
        """
        Generate SQL query to find duplicates by content fingerprint.
        
        Args:
            fingerprint: Content fingerprint to search for
            exclude_id: Item ID to exclude from search
            
        Returns:
            SQL query string
        """
        base_query = """
            SELECT id, title, url, created_at 
            FROM items 
            WHERE content_fingerprint = $1
        """
        
        if exclude_id:
            base_query += " AND id != $2"
        
        base_query += " ORDER BY created_at ASC"
        
        return base_query
    
    @staticmethod
    def get_content_versions_query(fingerprint: str) -> str:
        """
        Generate SQL query to get all versions of content with same fingerprint.
        
        Args:
            fingerprint: Content fingerprint to search for
            
        Returns:
            SQL query string
        """
        return """
            SELECT 
                id, 
                title, 
                url, 
                created_at, 
                updated_at,
                metadata->>'ai_analysis' as ai_analysis,
                (metadata->>'processing_version')::text as processing_version
            FROM items 
            WHERE content_fingerprint = $1
            ORDER BY created_at DESC
        """