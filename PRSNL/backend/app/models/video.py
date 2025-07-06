from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID

class VideoMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    upload_date: Optional[str] = None
    codec: Optional[str] = None
    audio_codec: Optional[str] = None
    average_bitrate: Optional[float] = None
    filesize: Optional[int] = None

class VideoItem(BaseModel):
    id: UUID
    url: HttpUrl
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    duration: Optional[int] = None
    video_path: str
    thumbnail_path: Optional[str] = None
    platform: str
    metadata: VideoMetadata
    downloaded_at: datetime
    status: str

    class Config:
        from_attributes = True

class VideoStreamResponse(BaseModel):
    message: str
    stream_url: str

class VideoTranscodeRequest(BaseModel):
    quality: str = Field(..., description="Desired quality for transcoding (e.g., 'low', 'medium', 'high')")

class VideoTranscodeResponse(BaseModel):
    message: str
    task_id: UUID
    status: str

class VideoDeleteResponse(BaseModel):
    message: str
    item_id: UUID
