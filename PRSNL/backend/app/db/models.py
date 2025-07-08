"""
SQLAlchemy models for PRSNL database
"""
from sqlalchemy import Column, String, Text, JSON, TIMESTAMP, Integer, Float, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
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
    extend_existing=True
)

class Item(Base):
    __tablename__ = 'items'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(Text, nullable=True)  # Made nullable based on migration
    title = Column(Text, nullable=False)
    summary = Column(Text)
    raw_content = Column(Text)
    processed_content = Column(Text)
    status = Column(String(20), nullable=False, default='pending')
    item_metadata = Column('metadata', JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    accessed_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    access_count = Column(Integer, default=0)
    embedding = Column(Vector(1536))
    transcription = Column(Text)
    
    # Relationships
    tags = relationship('Tag', secondary=item_tags, back_populates='items')

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    items = relationship('Item', secondary=item_tags, back_populates='tags')

# ItemTag is handled through the association table above