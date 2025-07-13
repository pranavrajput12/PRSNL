"""
SQLAlchemy model for Synaptic Echo audio journaling system
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import POINT, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.models import Base


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private" 
    CONFIDENTIAL = "confidential"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TranscriptionService(str, Enum):
    WHISPER_CLOUD = "whisper_cloud"
    WHISPER_CPP = "whisper_cpp"
    VOSK = "vosk"

class AudioJournal(Base):
    """
    Synaptic Echo: Audio Journal entries for neural voice processing
    
    This model extends the existing items/files system to provide
    audio journaling capabilities with AI analysis and knowledge base integration.
    """
    __tablename__ = 'audio_journals'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys to existing system
    item_id = Column(UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'), nullable=False)
    
    # Audio session metadata
    session_title = Column(String(255), nullable=True)
    session_description = Column(Text, nullable=True)
    duration_seconds = Column(Integer, default=0)
    
    # Privacy and mood
    privacy_level = Column(String(20), default=PrivacyLevel.PRIVATE)
    mood_tags = Column(JSON, default=list)  # List of mood descriptors
    emotional_tone = Column(String(50), nullable=True)  # AI-detected emotion
    
    # Location and context
    location_name = Column(String(255), nullable=True)
    location_coordinates = Column(POINT, nullable=True)
    ambient_description = Column(Text, nullable=True)
    
    # Processing status
    transcription_status = Column(String(20), default=ProcessingStatus.PENDING)
    transcription_service = Column(String(20), nullable=True)
    ai_analysis_status = Column(String(20), default=ProcessingStatus.PENDING)
    
    # Content analysis
    transcript_quality_score = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    silence_duration_seconds = Column(Integer, default=0)
    speech_pace_wpm = Column(Integer, default=0)  # Words per minute
    
    # Knowledge base integration
    related_items = Column(JSON, default=list)  # IDs of related items
    auto_tags = Column(JSON, default=list)  # AI-generated tags
    key_topics = Column(JSON, default=list)  # Extracted themes
    action_items = Column(JSON, default=list)  # Detected todos
    
    # Neural interface metadata (for future features)
    neural_patterns = Column(JSON, default=dict)  # Advanced audio analysis
    synaptic_connections = Column(JSON, default=list)  # Memory trace links
    
    # Timestamps
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    processed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    item = relationship("Item", back_populates="audio_journal")
    file = relationship("File", back_populates="audio_journal")
    
    def __repr__(self):
        return f"<AudioJournal(id={self.id}, title='{self.session_title}', duration={self.duration_seconds}s)>"
    
    @property
    def is_private(self) -> bool:
        """Check if this journal entry is private"""
        return self.privacy_level in [PrivacyLevel.PRIVATE, PrivacyLevel.CONFIDENTIAL]
    
    @property
    def is_processed(self) -> bool:
        """Check if transcription and AI analysis are complete"""
        return (
            self.transcription_status == ProcessingStatus.COMPLETED and 
            self.ai_analysis_status == ProcessingStatus.COMPLETED
        )
    
    @property
    def processing_progress(self) -> float:
        """Get overall processing progress as percentage"""
        transcription_weight = 0.6
        ai_weight = 0.4
        
        transcription_progress = {
            ProcessingStatus.PENDING: 0.0,
            ProcessingStatus.PROCESSING: 0.5,
            ProcessingStatus.COMPLETED: 1.0,
            ProcessingStatus.FAILED: 0.0
        }.get(self.transcription_status, 0.0)
        
        ai_progress = {
            ProcessingStatus.PENDING: 0.0,
            ProcessingStatus.PROCESSING: 0.5,
            ProcessingStatus.COMPLETED: 1.0,
            ProcessingStatus.FAILED: 0.0
        }.get(self.ai_analysis_status, 0.0)
        
        return (transcription_progress * transcription_weight + ai_progress * ai_weight) * 100
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string (MM:SS)"""
        if self.duration_seconds <= 0:
            return "0:00"
        
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def add_mood_tag(self, mood: str) -> None:
        """Add a mood tag to this journal entry"""
        if self.mood_tags is None:
            self.mood_tags = []
        if mood.lower() not in [tag.lower() for tag in self.mood_tags]:
            self.mood_tags.append(mood.lower())
    
    def add_related_item(self, item_id: str, relevance_score: float = 1.0) -> None:
        """Add a related item with relevance score"""
        if self.related_items is None:
            self.related_items = []
        
        # Check if item already exists
        for item in self.related_items:
            if item.get('item_id') == item_id:
                # Update relevance score if higher
                if relevance_score > item.get('relevance_score', 0):
                    item['relevance_score'] = relevance_score
                return
        
        # Add new related item
        self.related_items.append({
            'item_id': item_id,
            'relevance_score': relevance_score,
            'added_at': datetime.now().isoformat()
        })
    
    def add_action_item(self, action: str, priority: str = 'medium') -> None:
        """Add an action item detected from the audio"""
        if self.action_items is None:
            self.action_items = []
        
        self.action_items.append({
            'action': action,
            'priority': priority,
            'detected_at': datetime.now().isoformat(),
            'completed': False
        })
    
    def get_status_message(self) -> str:
        """Get human-readable status message"""
        if self.transcription_status == ProcessingStatus.FAILED:
            return "Transcription failed"
        elif self.ai_analysis_status == ProcessingStatus.FAILED:
            return "AI analysis failed"
        elif not self.is_processed:
            if self.transcription_status == ProcessingStatus.PROCESSING:
                return "Transcribing audio..."
            elif self.ai_analysis_status == ProcessingStatus.PROCESSING:
                return "Analyzing content..."
            else:
                return "Processing..."
        else:
            return "Ready"
    
    def to_dict(self, include_transcript: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'item_id': str(self.item_id),
            'file_id': str(self.file_id),
            'session_title': self.session_title,
            'session_description': self.session_description,
            'duration_seconds': self.duration_seconds,
            'duration_formatted': self.duration_formatted,
            'privacy_level': self.privacy_level,
            'mood_tags': self.mood_tags or [],
            'emotional_tone': self.emotional_tone,
            'location_name': self.location_name,
            'transcription_status': self.transcription_status,
            'transcription_service': self.transcription_service,
            'ai_analysis_status': self.ai_analysis_status,
            'transcript_quality_score': self.transcript_quality_score,
            'word_count': self.word_count,
            'speech_pace_wpm': self.speech_pace_wpm,
            'related_items': self.related_items or [],
            'auto_tags': self.auto_tags or [],
            'key_topics': self.key_topics or [],
            'action_items': self.action_items or [],
            'processing_progress': self.processing_progress,
            'status_message': self.get_status_message(),
            'is_processed': self.is_processed,
            'is_private': self.is_private,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

# Update existing models to add relationship (add to the end of models.py)
def add_audio_journal_relationships():
    """
    Add relationships to existing Item and File models.
    This should be called after all models are defined.
    """
    from app.db.models import File, Item

    # Add relationship to Item model
    if not hasattr(Item, 'audio_journal'):
        Item.audio_journal = relationship("AudioJournal", back_populates="item", uselist=False)
    
    # Add relationship to File model  
    if not hasattr(File, 'audio_journal'):
        File.audio_journal = relationship("AudioJournal", back_populates="file", uselist=False)