from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.services.chat_service import ChatService
from app.services.user_service import UserService
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process a chat query:
    1. Retrieve relevant context from vector store
    2. Apply user preferences and prompt template
    3. Send to LLM for processing
    4. Store the interaction
    """
    # Get user preferences (simplified for now - using default user)
    user_service = UserService(db)
    user_preferences = user_service.get_user_preferences(user_id="default")
    
    # Initialize chat service
    chat_service = ChatService(db)
    
    # Get conversation (create if not exists)
    conversation = chat_service.get_or_create_conversation(
        conversation_id=request.conversation_id,
        user_id="default"
    )
    
    # Process query and get response
    response = chat_service.process_query(
        query=request.message,
        conversation_id=conversation.id,
        user_preferences=user_preferences
    )
    
    return {
        "conversation_id": str(conversation.id),
        "message": response.content,
        "context_sources": response.context_sources
    }

@router.post("/query/stream")
async def chat_query_stream(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Stream the response for better UX with longer responses"""
    # Get user preferences (simplified for now - using default user)
    user_service = UserService(db)
    user_preferences = user_service.get_user_preferences(user_id="default")
    
    # Initialize chat service
    chat_service = ChatService(db)
    
    # Get conversation (create if not exists)
    conversation = chat_service.get_or_create_conversation(
        conversation_id=request.conversation_id,
        user_id="default"
    )
    
    # Create streaming response
    return StreamingResponse(
        chat_service.stream_response(
            query=request.message,
            conversation_id=conversation.id,
            user_preferences=user_preferences
        ),
        media_type="text/event-stream"
    )

@router.get("/history/{conversation_id}", response_model=List[MessageResponse])
async def get_chat_history(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """Get chat history for a conversation"""
    chat_service = ChatService(db)
    messages = chat_service.get_messages(conversation_id)
    return messages

@router.get("/conversations", response_model=List[dict])
async def get_conversations(
    db: Session = Depends(get_db)
):
    """Get all conversations for the user"""
    chat_service = ChatService(db)
    conversations = chat_service.get_conversations(user_id="default")
    return conversations