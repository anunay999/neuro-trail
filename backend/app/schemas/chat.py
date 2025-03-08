from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from app.schemas.base import TimestampMixin


class MessageRole(str):
    """Message role enum as string"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[str] = None
    references: Optional[bool] = True
    stream: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None


class ContextSource(BaseModel):
    """Source of context used in a response"""
    id: str
    document_id: str
    document_name: str
    content: str
    relevance_score: float
    

class ChatResponse(BaseModel):
    """Chat response model"""
    conversation_id: str
    message: str
    context_sources: Optional[List[ContextSource]] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageBase(BaseModel):
    """Base message attributes"""
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MessageCreate(MessageBase):
    """Attributes for creating a message"""
    conversation_id: str


class MessageResponse(MessageBase, TimestampMixin):
    """Message response model"""
    id: str
    conversation_id: str

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base conversation attributes"""
    title: Optional[str] = "New Conversation"
    metadata: Optional[Dict[str, Any]] = None


class ConversationCreate(ConversationBase):
    """Attributes for creating a conversation"""
    user_id: str


class ConversationResponse(ConversationBase, TimestampMixin):
    """Conversation response model"""
    id: str
    user_id: str
    message_count: Optional[int] = 0
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True