"""
Unified SQLAlchemy models for PRSNL database
This matches the unified schema exactly to prevent column mismatch errors
"""
from sqlalchemy import Column, String, Text, JSON, TIMESTAMP, Integer, Float, ForeignKey, Table, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

Base = declarative_base()

# Association table for many-to-many relationship between items and tags
item_tags = Table(
    'item_tags',
    Base.metadata,
    Column('item_id', UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    Column('confidence', Float, default=1.0),
    Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    extend_existing=True
)

class Item(Base):
    __tablename__ = 'items'
    
    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=True)  # Made nullable per migration
    title = Column(Text, nullable=False)
    summary = Column(Text)
    raw_content = Column(Text)
    processed_content = Column(Text)
    
    # Type and status fields (standardized names)
    type = Column(String(50), nullable=False, default='bookmark')  # Standardized to 'type'
    status = Column(String(20), nullable=False, default='pending')
    
    # Content classification (from enable_summarization feature)
    content_type = Column(String(50), default='auto')
    enable_summarization = Column(Boolean, default=False)
    
    # Video/media fields (from video support migrations)
    platform = Column(String(50))
    duration = Column(Integer)
    video_url = Column(Text)
    file_path = Column(Text)
    thumbnail_url = Column(Text)
    
    # File support fields (from add_file_support.sql)
    has_files = Column(Boolean, default=False)
    file_count = Column(Integer, default=0)
    
    # User highlight field (from frontend)
    highlight = Column(Text)
    
    # Metadata and search  
    metadata_ = Column('metadata', JSON, default={})  # Map to 'metadata' column, underscore to avoid SQLAlchemy conflict
    search_vector = Column(Text)  # Simplified for SQLAlchemy
    
    # Embedding support
    embedding = Column(Vector(1536))
    
    # Transcription support
    transcription = Column(Text)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    accessed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    access_count = Column(Integer, default=0)
    
    # Relationships
    tags = relationship('Tag', secondary=item_tags, back_populates='items')
    files = relationship('File', back_populates='item', cascade='all, delete-orphan')
    attachments = relationship('Attachment', back_populates='item', cascade='all, delete-orphan')
    jobs = relationship('Job', back_populates='item', cascade='all, delete-orphan')

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)
    color = Column(String(7))  # Hex color code
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('tags.id', ondelete='SET NULL'))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship('Item', secondary=item_tags, back_populates='tags')
    parent = relationship('Tag', remote_side=[id])
    children = relationship('Tag')

class File(Base):
    __tablename__ = 'files'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_extension = Column(String(10), nullable=False)
    file_category = Column(String(20), nullable=False)  # 'document', 'image', 'pdf', 'office', 'text'
    
    # Extracted content
    extracted_text = Column(Text)
    text_file_path = Column(Text)
    word_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    extraction_method = Column(String(50))
    
    # Image-specific fields
    thumbnail_path = Column(Text)
    image_width = Column(Integer)
    image_height = Column(Integer)
    
    # Processing metadata
    processing_status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processing_error = Column(Text)
    processed_at = Column(TIMESTAMP(timezone=True))
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relationships
    item = relationship('Item', back_populates='files')
    attachments = relationship('Attachment', back_populates='file')
    processing_logs = relationship('FileProcessingLog', back_populates='file', cascade='all, delete-orphan')

class Attachment(Base):
    __tablename__ = 'attachments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'))  # Link to files table
    filename = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(100))
    mime_type = Column(String(100))
    file_size = Column(BigInteger)
    thumbnail_path = Column(Text)
    metadata_ = Column('metadata', JSON, default={})  # Avoid SQLAlchemy conflict
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    item = relationship('Item', back_populates='attachments')
    file = relationship('File', back_populates='attachments')

class FileProcessingLog(Base):
    __tablename__ = 'file_processing_log'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'), nullable=False)
    processing_step = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # 'started', 'completed', 'failed'
    message = Column(Text)
    processing_time_ms = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    
    # Relationships
    file = relationship('File', back_populates='processing_logs')

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    item_id = Column(UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'))
    payload = Column(JSON, default={})
    result = Column(JSON, default={})
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    scheduled_for = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    item = relationship('Item', back_populates='jobs')

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True, nullable=False)
    user_id = Column(UUID(as_uuid=True))  # Will reference users table when created
    ip_address = Column(INET)
    user_agent = Column(Text)
    user_data = Column(JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    last_activity = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

class ApiKey(Base):
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    permissions = Column(JSON, default={})
    rate_limit = Column(Integer, default=1000)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(TIMESTAMP(timezone=True))
    expires_at = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    user_id = Column(UUID(as_uuid=True))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    ip_address = Column(INET)
    user_agent = Column(Text)
    request_id = Column(UUID(as_uuid=True))
    metadata_ = Column('metadata', JSON, default={})  # Avoid SQLAlchemy conflict
    status = Column(String(20))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())