from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from app.schemas.base import TimestampMixin


class DocumentStatus(str, Enum):
    """Status of document processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentBase(BaseModel):
    """Base document attributes"""
    filename: str
    file_type: str


class DocumentCreate(DocumentBase):
    """Attributes for creating a document"""
    pass


class DocumentUpdate(BaseModel):
    """Attributes for updating a document"""
    status: Optional[DocumentStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase, TimestampMixin):
    """Document response model"""
    id: str
    status: DocumentStatus
    metadata: Optional[Dict[str, Any]] = None
    chunks_count: Optional[int] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentStats(BaseModel):
    """Statistics about a processed document"""
    total_chunks: int
    total_tokens: int
    chapters: Optional[List[str]] = None
    knowledge_graph_nodes: Optional[int] = None
    knowledge_graph_relationships: Optional[int] = None