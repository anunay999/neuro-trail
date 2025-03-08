from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.base_class import Base


class Conversation(Base):
    """Model for storing conversation information"""
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False, default="New Conversation")
    conv_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_conversation_user_id", "user_id"),
    )


class Message(Base):
    """Model for storing message information"""
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    references = relationship("MessageReference", back_populates="message", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_message_conversation_id", "conversation_id"),
    )


class MessageReference(Base):
    """Model for storing message references to source documents"""
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("message.id", ondelete="CASCADE"), nullable=False)
    reference_type = Column(String, nullable=False)  # document, knowledge_graph, etc.
    reference_id = Column(String, nullable=False)
    context = Column(Text)
    
    # Relationships
    message = relationship("Message", back_populates="references")
    
    # Indexes
    __table_args__ = (
        Index("ix_messagereference_message_id", "message_id"),
        Index("ix_messagereference_reference_id", "reference_id"),
    )