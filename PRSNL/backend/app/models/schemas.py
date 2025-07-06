"""Pydantic models for request/response schemas"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Capture schemas
class CaptureRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    highlight: Optional[str] = None
    tags: Optional[List[str]] = []


class CaptureResponse(BaseModel):
    id: UUID
    status: str
    message: str


# Search schemas
class SearchResult(BaseModel):
    id: UUID
    title: str
    url: str
    snippet: str
    tags: List[str]
    created_at: datetime
    score: Optional[float] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    took_ms: int


# Timeline schemas
class TimelineItem(BaseModel):
    id: UUID
    title: str
    url: Optional[str]
    snippet: str
    tags: List[str]
    created_at: datetime


class TimelineResponse(BaseModel):
    items: List[TimelineItem]
    hasMore: bool


# Item schemas
class ItemBase(BaseModel):
    url: str
    title: str
    summary: Optional[str] = None
    tags: List[str] = []


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


class Item(ItemBase):
    id: UUID
    content: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime
    access_count: int
    status: str

    class Config:
        from_attributes = True