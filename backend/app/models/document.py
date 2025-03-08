from sqlalchemy import Column, String, Enum, Text, Integer, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

from app.db.base_class import Base
from app.schemas.document import DocumentStatus


class Document(Base):
    """Model for storing document information"""
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    message = Column(Text)
    doc_metadata = Column(JSON, default={})
    chunks_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)