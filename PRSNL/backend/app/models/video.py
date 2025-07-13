from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class VideoMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    upload_date: Optional[str] = None # YYYYMMDD format
    codec: Optional[str] = None
    audio_codec: Optional[str] = None
    average_bitrate: Optional[float] = None
    filesize: Optional[int] = None # in bytes

class VideoBase(BaseModel):
    url: HttpUrl
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    platform: str
    metadata: Optional[VideoMetadata] = None

class VideoInDB(VideoBase):
    id: UUID
    video_path: str
    thumbnail_path: Optional[str] = None
    downloaded_at: datetime
    status: str = "completed"

    class Config:
        from_attributes = True