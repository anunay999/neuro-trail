from fastapi import Depends
from sqlalchemy.orm import Session
import uuid
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

from app.db.session import get_db
from app.models.chat import Conversation, Message, MessageReference
from app.schemas.chat import MessageRole, ContextSource
from app.schemas.user import UserPreferences
from app.services.plugin_manager import plugin_manager
from app.services.template_service import TemplateService
from app.core.plugin_base import LLMPlugin, VectorStorePlugin, EmbeddingPlugin
from app.core.exceptions import ServiceUnavailableError
from app.crud.chat import conversation, message


# Configure logging
logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat interaction and conversation management"""
    
    def __init__(self, db: Session):
        """
        Initialize chat service
        
        Args:
            db: Database session
        """
        self.db = db
        self.template_service = TemplateService(db)
    
    def get_or_create_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Conversation:
        """
        Get or create a conversation
        
        Args:
            user_id: User ID
            conversation_id: Optional conversation ID (if None, creates new)
            title: Optional conversation title
            
        Returns:
            Conversation: Conversation object
        """
        # If conversation ID provided, try to get existing
        conv = conversation.get_or_create(
            db=self.db,
            user_id=user_id,
            conversation_id=conversation_id,
            title=title
        )
        
        logger.info(f"Created new conversation: {conversation.id} for user: {user_id}")
        
        return conv
    
    def get_conversations(self, user_id: str) -> List[Conversation]:
        """
        Get all conversations for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List[Conversation]: List of conversations
        """
        return conversation.get_by_user(
                                db=self.db,
                                user_id=user_id
                            )

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Add a message to a conversation
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            Message: Created message
        """
        return message.create_message(
                    db=self.db,
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                    metadata=metadata
                )
    
    def add_message_reference(
        self,
        message_id: str,
        reference_type: str,
        reference_id: str,
        context: Optional[str] = None
    ) -> MessageReference:
        """
        Add a reference to a message
        
        Args:
            message_id: Message ID
            reference_type: Reference type (document, knowledge_graph, etc.)
            reference_id: Reference ID
            context: Optional context excerpt
            
        Returns:
            MessageReference: Created reference
        """
        return message.add_reference(
                        db=self.db,
                        message_id=message_id,
                        reference_type=reference_type,
                        reference_id=reference_id,
                        context=context
                    )
    
    def get_messages(self, conversation_id: str) -> List[Message]:
        """
        Get all messages in a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List[Message]: List of messages
        """
        return message.get_by_conversation(
                db=self.db,
                conversation_id=conversation_id
            )
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for context
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of previous messages
            
        Returns:
            List[Dict[str, Any]]: List of message dicts for LLM context
        """
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        # Format for LLM
        history = []
        for message in messages:
            history.append({
                "role": message.role,
                "content": message.content
            })
        
        return history
    
    async def process_query(
        self,
        query: str,
        conversation_id: str,
        user_preferences: UserPreferences
    ) -> Dict[str, Any]:
        """
        Process a chat query
        
        Args:
            query: User query
            conversation_id: Conversation ID
            user_preferences: User preferences
            
        Returns:
            Dict[str, Any]: Response with message and context
        """
        try:
            # Add user message to conversation
            self.add_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=query
            )
            
            # Get relevant context
            context_results = await self._get_context(query)
            
            # Format context for response
            context_sources = []
            context_text = ""
            
            if context_results:
                for result in context_results:
                    context_sources.append(
                        ContextSource(
                            id=result.get("id", ""),
                            document_id=result.get("document_id", ""),
                            document_name=result.get("title", "Unknown Document"),
                            content=result.get("text", "")[:200] + "...",
                            relevance_score=result.get("score", 0.0)
                        )
                    )
                    context_text += result.get("text", "") + "\n\n"
            
            # Get conversation history
            history = self.get_conversation_history(conversation_id)
            
            # Format prompt with template
            prompt = await self._format_prompt(
                query=query,
                context=context_text,
                history=history,
                user_preferences=user_preferences
            )
            
            # Get response from LLM
            llm_response = await self._get_llm_response(
                prompt=prompt,
                temperature=0.0,  # Could use preferences for this
                max_tokens=2000
            )
            
            # Add assistant message to conversation
            assistant_message = self.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=llm_response,
                metadata={
                    "context_count": len(context_sources),
                    "template_id": user_preferences.active_template_id
                }
            )
            
            # Add references
            for context in context_results:
                self.add_message_reference(
                    message_id=assistant_message.id,
                    reference_type="document",
                    reference_id=context.get("document_id", ""),
                    context=context.get("text", "")[:500]  # Limit context length
                )
            
            # Construct response
            response = {
                "content": llm_response,
                "context_sources": context_sources,
                "message_id": assistant_message.id
            }
            
            return response
            
        except Exception as e:
            logger.exception(f"Error processing query: {e}")
            
            # Add error message to conversation
            self.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=f"I apologize, but I encountered an error while processing your request: {str(e)}",
                metadata={"error": str(e)}
            )
            
            # Return error response
            return {
                "content": f"Error: {str(e)}",
                "context_sources": [],
                "error": str(e)
            }
    
    async def stream_response(
        self,
        query: str,
        conversation_id: str,
        user_preferences: UserPreferences
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response to a chat query
        
        Args:
            query: User query
            conversation_id: Conversation ID
            user_preferences: User preferences
            
        Yields:
            str: Chunks of the response
        """
        try:
            # Add user message to conversation
            self.add_message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=query
            )
            
            # Get relevant context
            context_results = await self._get_context(query)
            
            # Format context
            context_text = ""
            if context_results:
                for result in context_results:
                    context_text += result.get("text", "") + "\n\n"
            
            # Get conversation history
            history = self.get_conversation_history(conversation_id)
            
            # Format prompt with template
            prompt = await self._format_prompt(
                query=query,
                context=context_text,
                history=history,
                user_preferences=user_preferences
            )
            
            # Stream response from LLM
            full_response = ""
            llm_plugin = await plugin_manager.get_plugin(
                plugin_type="llm",
                plugin_name=self._get_llm_plugin_name()
            )

            async for chunk in llm_plugin.generate_stream(
                prompt=prompt,
                temperature=0.0,  # Could use preferences for this
                max_tokens=2000
            ):
                full_response += chunk
                yield chunk
            
            # Add assistant message to conversation
            assistant_message = self.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                metadata={
                    "context_count": len(context_results),
                    "template_id": user_preferences.active_template_id
                }
            )
            
            # Add references
            for context in context_results:
                self.add_message_reference(
                    message_id=assistant_message.id,
                    reference_type="document",
                    reference_id=context.get("document_id", ""),
                    context=context.get("text", "")[:500]  # Limit context length
                )
        
        except Exception as e:
            logger.exception(f"Error streaming response: {e}")
            error_message = f"I apologize, but I encountered an error: {str(e)}"
            
            # Add error message to conversation
            self.add_message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=error_message,
                metadata={"error": str(e)}
            )
            
            yield error_message
    
    async def _get_context(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Get relevant context for a query"""
        try:
            # Get plugin manager
            
            # Get embedding plugin
            embedding_plugin = await plugin_manager.get_plugin(
                plugin_type="embedding",
                plugin_name="ollama"
            )
            
            # Get vector store plugin
            vector_store_plugin = await plugin_manager.get_plugin(
                plugin_type="vector_store",
                plugin_name="chroma"
            )
            
            # Generate query embedding
            query_embedding = await embedding_plugin.embed_query(query)
            
            # Search vector store
            results = await vector_store_plugin.search(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            logger.info(f"Found {len(results)} context chunks for query")
            
            return results
        
        except Exception as e:
            logger.exception(f"Error getting context: {e}")
            return []
    
    async def _format_prompt(
        self,
        query: str,
        context: str,
        history: List[Dict[str, str]],
        user_preferences: UserPreferences
    ) -> str:
        """
        Format prompt using a template
        
        Args:
            query: User query
            context: Context text
            history: Conversation history
            user_preferences: User preferences
            
        Returns:
            str: Formatted prompt
        """
        # Get template ID from preferences or use default
        template_id = user_preferences.active_template_id or "default"
        
        
        # Format history for inclusion in prompt
        history_text = ""
        for msg in history:
            role = msg["role"].capitalize()
            history_text += f"{role}: {msg['content']}\n\n"
        
        # Prepare variables
        variables = {
            "question": query,
            "context": context,
            "history": history_text,
            "style": user_preferences.response_style.value,
            "length": user_preferences.response_length.value,
            "expertise": user_preferences.expertise_level.value,
        }
        
        # Format template
        formatted_prompt = self.template_service.format_template(
            template_id=template_id,
            variables=variables
        )
        
        return formatted_prompt
    
    def _get_llm_plugin_name(self) -> str:
        """
        Get the name of the LLM plugin to use
        
        Returns:
            str: Plugin name
        """
        # This could be configurable, for now hardcoded
        return "ollama"
    
    async def _get_llm_response(
    self,
    prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 2000
    ) -> str:
        """Get a response from the LLM"""
        try:
            # Get plugin manager
            
            # Get LLM plugin
            llm_plugin = await plugin_manager.get_plugin(
                plugin_type="llm",
                plugin_name=self._get_llm_plugin_name()
            )
            
            # Generate response
            response = await llm_plugin.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response
        
        except Exception as e:
            logger.exception(f"Error getting LLM response: {e}")
            raise ServiceUnavailableError(f"LLM service unavailable: {str(e)}")