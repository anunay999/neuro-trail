import logging
from datetime import datetime
from typing import Dict, Generator, List

import streamlit as st
from .memory_client import create_memory_client_from_settings
from .user_memory import UserMemory
from llm import get_llm
from core.learning_canvas import canvas


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MemoryAugmentedChat:
    """
    Class to integrate memory capabilities with the Neuro Trail chat interface.
    """

    def __init__(self):
        """Initialize with application settings."""
        logger.info("Initializing MemoryAugmentedChat")
        self.memory_client = create_memory_client_from_settings()
        self.user_memory = UserMemory(self.memory_client)
        logger.info("MemoryAugmentedChat initialized successfully")

    def answer_query(self, query: str, user_id: str = None) -> Generator[str, None, None]:
        """
        Process user query and generate a response with memory-augmented context.

        Args:
            query: The user's question or prompt
            user_id: Unique identifier for the user, defaults to session ID if None

        Returns:
            Generator yielding response tokens
        """
        logger.info(f"Answering query: '{query}' for user_id: {user_id}")

        # Use session ID if user_id not provided
        if user_id is None:
            user_id = st.session_state.get("session_id", "anonymous")
            logger.info(f"Using session_id as user_id: {user_id}")

        # Get current personalization settings
        length = st.session_state.get("response_length", "Balanced")
        expertise = st.session_state.get("expertise_level", "Intermediate")
        logger.info(
            f"Current personalization settings: Length={length}, Expertise={expertise}")

        # Retrieve relevant chat history
        relevant_history = self.user_memory.get_chat_history(
            user_id)
        logger.info(
            f"Retrieved {len(relevant_history)} relevant chat history entries")

        # Create context from relevant history and preferences
        context = self._build_context_from_memory(
            relevant_history)
        logger.debug(f"Built context from memory: {context}")

        # Format the query with personalization and context
        personalized_query = self._format_query_with_context(
            query, context, length, expertise)
        logger.info(f"Formatted query with context: {personalized_query}")

        # Get response tokens from the canvas
        response_tokens = canvas.answer_query(personalized_query)

        # Store the interaction in memory
        messages = [
            {"role": "user", "content": query}
        ]

        accumulated_response = ""
        for token in response_tokens:
            accumulated_response += token
            yield token

        # Add the full response to messages
        messages.append({"role": "assistant", "content": accumulated_response})

        # Store the interaction asynchronously (in a real app, you'd use async)
        self._store_interaction(messages, user_id, query)

        # Analyze the interaction for preference inference (could be done periodically instead)
        logger.info(f"Finished answering query: '{query}'")

    def _build_context_from_memory(self,
                                   relevant_history: List[Dict]) -> str:
        """Build context string from memory components."""
        logger.info("Building context from memory...")
        context_parts = []

        # Add relevant history
        if relevant_history:
            context_parts.append("Relevant prior conversations:")
            # Limit to 3 most relevant
            for i, history in enumerate(relevant_history[:3]):
                memory_content = history.get('memory', '')
                logger.debug(
                    f"Processing history entry {i+1}: {memory_content}")
                if isinstance(memory_content, list):
                    # Format message list
                    conversation = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}"
                                             for msg in memory_content if isinstance(msg, dict)])
                    context_parts.append(f"{i+1}. {conversation}")
                else:
                    context_parts.append(f"{i+1}. {memory_content}")

        context = "\n".join(context_parts)
        logger.info(f"Context built: {context}")
        return context

    def _format_query_with_context(self,
                                   query: str,
                                   context: str,
                                   length: str = "balanced",
                                   expertise: str = "intermediate") -> str:
        """Format the query with context and personalization."""
        logger.info("Formatting query with context and preferences...")
        from core.prompt_templates import prompt_template_manager

        logger.debug(
            f"Using length: {length}, expertise: {expertise} for formatting")

        # Use your existing template manager
        context = f"""
                    {context}\nPreferred Response Length: {length}\nPreferred Expertise Level:{expertise}
                """
        formatted_prompt = prompt_template_manager.format_prompt(
            context=context,
            question=query
        )
        logger.info(f"Formatted prompt: {formatted_prompt}")
        return formatted_prompt

    def _store_interaction(self, messages: List[Dict[str, str]], user_id: str, query: str):
        """Store the interaction in memory."""
        logger.info(f"Storing interaction for user {user_id}: {messages}")
        try:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'query_intent': self._categorize_query(query)
            }
            logger.debug(f"Interaction metadata: {metadata}")

            self.user_memory.store_chat_interaction(
                messages, user_id, metadata)
            logger.info(f"Stored chat interaction for user {user_id}")
        except Exception as e:
            logger.error(f"Error storing chat interaction: {str(e)}")

    def _categorize_query(self, query: str) -> str:
        prompt = f"""Categorize Query: {query}
            only return the cateogry in one word.
            Example Query: Categorize Query: What is llm\Response:question"""

        llm = get_llm(streaming=False)
        response = llm(prompt)
        logger.info(f"Cateogrized Query: {query} as category: {response}")
        return response


# Function to initialize memory system in Streamlit
def initialize_memory_system():
    """Initialize the memory system and store in session state."""
    logger.info("Initializing memory system in Streamlit...")
    if "memory_system" not in st.session_state:
        st.session_state.memory_system = MemoryAugmentedChat()

        # Generate a session ID if not present
        if "session_id" not in st.session_state:
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
            logger.info(
                f"Generated new session ID: {st.session_state.session_id}")

        # Set default user (in a real app, this would come from authentication)
        st.session_state.user_id = st.session_state.session_id

        logger.info(
            f"Memory system initialized with session ID: {st.session_state.session_id}")
