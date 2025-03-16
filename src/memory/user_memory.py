from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import json
from enum import Enum
from .memory_client import AbstractMemoryClient, MemoryType
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s"
)
logger = logging.getLogger(__name__)


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    HUMAN = "human"


class UserPreference(BaseModel):
    """Model for user preferences derived from interactions."""

    role: Optional[str] = Role.USER.value
    content: Optional[str] = None


class UserMetadata(BaseModel):
    learning_style: Optional[str] = None  # Visual, auditory, kinesthetic, etc.
    expertise_level: Optional[str] = None  # Beginner, intermediate, advanced
    interests: List[str] = Field(default_factory=list)  # Topics of interest
    response_length_preference: Optional[str] = None  # Concise, detailed, etc.
    pace_preference: Optional[str] = None  # Fast, moderate, slow


class UserProgress(BaseModel):
    """Model for tracking user progress towards goals."""

    goal_id: str
    goal_description: str
    start_date: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    completion_percentage: float = 0.0
    status: str = "in_progress"  # in_progress, completed, paused


class UserMemory:
    """
    Implementation of user memory functionality using the memory client.
    Focuses on storing and retrieving user-specific information like:
    - Chat history
    - User preferences
    - Learning progress
    """

    def __init__(self, memory_client: AbstractMemoryClient):
        logger.info("Initializing UserMemory")
        self.memory_client = memory_client
        logger.info("UserMemory initialized with memory client.")

    def store_chat_interaction(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        Store a chat interaction between user and system.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            user_id: Unique identifier for the user
            metadata: Additional metadata like context, timestamp, etc.

        Returns:
            Response from memory client
        """
        logger.info(f"Storing chat interaction for user {user_id}")
        logger.debug(f"Messages: {messages}")
        if metadata is None:
            metadata = {}
            logger.debug("Metadata is None, initializing empty metadata.")

        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
            logger.debug(f"Added timestamp to metadata: {metadata['timestamp']}")

        # Add memory type
        metadata["memory_type"] = MemoryType.USER.value
        metadata["interaction_type"] = "chat"
        logger.debug(f"Added memory_type and interaction_type to metadata: {metadata}")

        response = self.memory_client.add(messages, user_id=user_id, metadata=metadata)
        logger.info(f"Chat interaction stored. Response from memory client: {response}")
        return response

    def get_user_profile(self, user_id: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve relevant chat history based on a query.

        Args:
            query: The query to search for relevant history
            user_id: Unique identifier for the user
            limit: Maximum number of relevant history items to return

        Returns:
            List of relevant chat interactions
        """

        # Search with a narrowed query that focuses on chat interactions
        search_results = self.memory_client.search(
            "user profile interaction_type:chat", user_id=user_id, limit=limit
        )
        logger.info(f"Search results for relevant chat history: {search_results}")

        if search_results and search_results.get("results"):
            logger.info(
                f"Found {len(search_results['results'])} relevant chat history entries."
            )
            return search_results["results"]

        return []
