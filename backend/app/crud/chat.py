from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import uuid
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.chat import Conversation, Message, MessageReference
from app.schemas.chat import ConversationCreate, MessageCreate


class CRUDConversation(CRUDBase[Conversation, ConversationCreate, Dict[str, Any]]):
    """CRUD for conversation operations"""
    
    def get_by_user(
        self, db: Session, *, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[Conversation]:
        """
        Get conversations by user ID
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Conversation]: List of conversations
        """
        return db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    
    def get_or_create(
        self, db: Session, *, user_id: str, conversation_id: Optional[str] = None, title: Optional[str] = None
    ) -> Conversation:
        """
        Get or create a conversation
        
        Args:
            db: Database session
            user_id: User ID
            conversation_id: Optional conversation ID
            title: Optional conversation title
            
        Returns:
            Conversation: Retrieved or created conversation
        """
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            ).first()
            
            if conversation:
                return conversation
        
        # Create new conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title or "New Conversation",
            conv_metadata={}
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    def update_timestamp(self, db: Session, *, conversation_id: str) -> Optional[Conversation]:
        """
        Update conversation timestamp
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            Optional[Conversation]: Updated conversation or None if not found
        """
        conversation = self.get(db, id=conversation_id)
        if not conversation:
            return None
        
        conversation.updated_at = datetime.now()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    def get_with_message_count(self, db: Session, *, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation with message count
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            
        Returns:
            Optional[Dict[str, Any]]: Conversation with message count or None if not found
        """
        result = db.query(
            Conversation, 
            func.count(Message.id).label("message_count")
        ).outerjoin(
            Message, Conversation.id == Message.conversation_id
        ).filter(
            Conversation.id == conversation_id
        ).group_by(
            Conversation.id
        ).first()
        
        if not result:
            return None
        
        conversation, message_count = result
        
        return {
            "conversation": conversation,
            "message_count": message_count
        }


class CRUDMessage(CRUDBase[Message, MessageCreate, Dict[str, Any]]):
    """CRUD for message operations"""
    
    def get_by_conversation(
        self, db: Session, *, conversation_id: str, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        """
        Get messages by conversation ID
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Message]: List of messages
        """
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).offset(skip).limit(limit).all()
    
    def create_message(
        self, 
        db: Session, 
        *, 
        conversation_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Create a message
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            Message: Created message
        """
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata or {}
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Update conversation timestamp
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.updated_at = message.created_at
            db.add(conversation)
            db.commit()
        
        return message
    
    def add_reference(
        self,
        db: Session,
        *,
        message_id: str,
        reference_type: str,
        reference_id: str,
        context: Optional[str] = None
    ) -> MessageReference:
        """
        Add a reference to a message
        
        Args:
            db: Database session
            message_id: Message ID
            reference_type: Reference type
            reference_id: Reference ID
            context: Optional context excerpt
            
        Returns:
            MessageReference: Created reference
        """
        reference = MessageReference(
            id=str(uuid.uuid4()),
            message_id=message_id,
            reference_type=reference_type,
            reference_id=reference_id,
            context=context
        )
        
        db.add(reference)
        db.commit()
        db.refresh(reference)
        
        return reference
    
    def get_with_references(self, db: Session, *, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get message with references
        
        Args:
            db: Database session
            message_id: Message ID
            
        Returns:
            Optional[Dict[str, Any]]: Message with references or None if not found
        """
        message = self.get(db, id=message_id)
        if not message:
            return None
        
        references = db.query(MessageReference).filter(
            MessageReference.message_id == message_id
        ).all()
        
        return {
            "message": message,
            "references": references
        }


conversation = CRUDConversation(Conversation)
message = CRUDMessage(Message)