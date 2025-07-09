"""Pydantic models for request/response schemas with validation"""
from pydantic import BaseModel, HttpUrl, Field, validator, constr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
import re


# Constants for validation
MAX_TITLE_LENGTH = 500
MAX_SUMMARY_LENGTH = 5000
MAX_CONTENT_LENGTH = 50000
MAX_TAG_LENGTH = 50
MAX_TAGS_COUNT = 20
MAX_QUERY_LENGTH = 1000


# Enums
class ItemStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    BOOKMARK = "bookmark"


class VideoQuality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ORIGINAL = "original"


# Custom types
TagStr = constr(strip_whitespace=True, min_length=1, max_length=MAX_TAG_LENGTH)
TitleStr = constr(strip_whitespace=True, min_length=1, max_length=MAX_TITLE_LENGTH)


# Base validators
def validate_tags(tags: Optional[List[str]]) -> List[str]:
    """Validate and clean tags"""
    if not tags:
        return []
    
    # Remove duplicates and empty tags
    cleaned_tags = []
    seen = set()
    
    for tag in tags:
        if tag and isinstance(tag, str):
            # Strip whitespace and convert to lowercase
            clean_tag = tag.strip().lower()
            
            # Skip if empty after stripping
            if not clean_tag:
                continue
                
            # Validate tag format (alphanumeric, spaces, hyphens only)
            if not re.match(r'^[a-z0-9\s\-]+$', clean_tag):
                continue
                
            # Check length
            if len(clean_tag) > MAX_TAG_LENGTH:
                clean_tag = clean_tag[:MAX_TAG_LENGTH]
            
            # Add if not duplicate
            if clean_tag not in seen:
                seen.add(clean_tag)
                cleaned_tags.append(clean_tag)
                
            # Limit total tags
            if len(cleaned_tags) >= MAX_TAGS_COUNT:
                break
    
    return cleaned_tags


def sanitize_text(text: Optional[str]) -> Optional[str]:
    """Basic text sanitization to prevent XSS"""
    if not text:
        return text
    
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove any script tags content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous characters
    text = text.replace('\x00', '')  # Null bytes
    
    return text.strip()


# Capture schemas
class CaptureRequest(BaseModel):
    url: Optional[HttpUrl] = Field(None, description="URL to capture")
    content: Optional[str] = Field(None, max_length=MAX_CONTENT_LENGTH, description="Direct content to save")
    title: Optional[TitleStr] = Field(None, description="Title of the item")
    highlight: Optional[str] = Field(None, max_length=1000, description="Highlighted text")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    enable_summarization: bool = Field(default=False, description="Enable AI summarization for this item")
    content_type: str = Field(default="auto", description="Content type: auto, document, video, article, tutorial, image, note, link")
    uploaded_files: Optional[List[Any]] = Field(default_factory=list, description="Uploaded files for processing")
    
    @validator('content')
    def validate_url_or_content(cls, v, values):
        """Ensure either URL, content, or files are provided"""
        url = values.get('url')
        content = v
        highlight = values.get('highlight')
        uploaded_files = values.get('uploaded_files')
        
        # Check if we have any content source
        has_url = url is not None and url != ''
        has_content = content is not None and content != ''
        has_highlight = highlight is not None and highlight != ''
        has_files = uploaded_files is not None and len(uploaded_files) > 0
        
        if not (has_url or has_content or has_highlight or has_files):
            raise ValueError('Either URL, content, highlight, or files must be provided')
        return v
    
    @validator('title', 'highlight')
    def sanitize_text_fields(cls, v):
        return sanitize_text(v)
    
    @validator('tags')
    def validate_tags_field(cls, v):
        return validate_tags(v)
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type is one of the allowed values"""
        if v is None:
            return "auto"
        
        allowed_types = ["auto", "document", "video", "article", "tutorial", "image", "note", "link"]
        if v.lower() not in allowed_types:
            raise ValueError(f"Content type must be one of: {', '.join(allowed_types)}")
        
        return v.lower()


class CaptureResponse(BaseModel):
    id: UUID
    status: ItemStatus
    message: str
    duplicate_info: Optional[Dict[str, Any]] = None


# Search schemas
class SearchRequest(BaseModel):
    query: constr(strip_whitespace=True, min_length=1, max_length=MAX_QUERY_LENGTH)
    tags: Optional[List[str]] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    @validator('query')
    def sanitize_query(cls, v):
        return sanitize_text(v)
    
    @validator('tags')
    def validate_tags_field(cls, v):
        return validate_tags(v)


class SearchResult(BaseModel):
    id: UUID
    title: str
    url: Optional[str]
    snippet: str
    tags: List[str]
    created_at: datetime
    score: Optional[float] = Field(None, ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int = Field(ge=0)
    took_ms: int = Field(ge=0)


# Timeline schemas
class TimelineItem(BaseModel):
    id: UUID
    title: str
    url: Optional[str]
    snippet: str
    tags: List[str]
    created_at: datetime


class TimelineRequest(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @validator('tags')
    def validate_tags_field(cls, v):
        return validate_tags(v)


class TimelineResponse(BaseModel):
    items: List[TimelineItem]
    hasMore: bool


# Item schemas
class ItemBase(BaseModel):
    url: Optional[HttpUrl] = None
    title: TitleStr
    summary: Optional[constr(max_length=MAX_SUMMARY_LENGTH)] = None
    tags: List[str] = Field(default_factory=list)
    
    @validator('title', 'summary')
    def sanitize_text_fields(cls, v):
        return sanitize_text(v)
    
    @validator('tags')
    def validate_tags_field(cls, v):
        return validate_tags(v)


class ItemCreate(ItemBase):
    type: str = 'bookmark'
    content: Optional[str] = None


class ItemUpdate(BaseModel):
    title: Optional[TitleStr] = None
    summary: Optional[constr(max_length=MAX_SUMMARY_LENGTH)] = None
    tags: Optional[List[str]] = None
    
    @validator('title', 'summary')
    def sanitize_text_fields(cls, v):
        return sanitize_text(v)
    
    @validator('tags')
    def validate_tags_field(cls, v):
        if v is None:
            return None
        return validate_tags(v)


class Item(ItemBase):
    id: UUID
    content: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime
    access_count: int = Field(ge=0)
    status: ItemStatus
    item_type: Optional[str] = None
    platform: Optional[str] = None
    duration: Optional[int] = None
    file_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


# Video schemas
class VideoTranscodeRequest(BaseModel):
    target_quality: VideoQuality


# Admin schemas
class CleanupRequest(BaseModel):
    hours: int = Field(default=24, ge=1, le=720)  # Max 30 days


