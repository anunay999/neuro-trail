from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import json

from .memory_client import AbstractMemoryClient, MemoryType
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class UserPreference(BaseModel):
    """Model for user preferences derived from interactions."""
    learning_style: Optional[str] = None  # Visual, auditory, kinesthetic, etc.
    expertise_level: Optional[str] = None  # Beginner, intermediate, advanced
    interests: List[str] = Field(default_factory=list)  # Topics of interest
    response_length_preference: Optional[str] = None  # Concise, detailed, etc.
    pace_preference: Optional[str] = None  # Fast, moderate, slow

    # This can be extended with more preference fields as needed


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

    def store_chat_interaction(self,
                               messages: List[Dict[str, str]],
                               user_id: str,
                               metadata: Optional[Dict[str, Any]] = None) -> Dict:
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
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
            logger.debug(
                f"Added timestamp to metadata: {metadata['timestamp']}")

        # Add memory type
        metadata['memory_type'] = MemoryType.USER.value
        metadata['interaction_type'] = 'chat'
        logger.debug(
            f"Added memory_type and interaction_type to metadata: {metadata}")

        response = self.memory_client.add(
            messages, user_id=user_id, metadata=metadata)
        logger.info(
            f"Chat interaction stored. Response from memory client: {response}")
        return response

    def update_user_preferences(self,
                                user_id: str,
                                preferences: UserPreference,
                                confidence: float = 1.0) -> Dict:
        """
        Update user preferences based on interactions or explicit settings.

        Args:
            user_id: Unique identifier for the user
            preferences: UserPreference object with preference data
            confidence: Confidence level for the preference update (0.0-1.0)

        Returns:
            Response from memory client
        """
        logger.info(f"Updating user preferences for user {user_id}")
        logger.debug(f"Preferences: {preferences}, Confidence: {confidence}")

        # First try to get existing preferences
        preferences_search = self.memory_client.search(
            "user preferences",
            user_id=user_id,
            limit=1
        )
        logger.debug(
            f"Search result for existing preferences: {preferences_search}")

        metadata = {
            'memory_type': MemoryType.USER.value,
            'data_type': 'preferences',
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        logger.debug(f"Metadata for preference update: {metadata}")

        # If preferences exist, update them
        if preferences_search and preferences_search.get('memories') and len(preferences_search['memories']) > 0:
            memory_id = preferences_search['memories'][0]['id']
            existing_data = preferences_search['memories'][0].get('memory', {})
            logger.debug(
                f"Existing preferences found. Memory ID: {memory_id}, Data: {existing_data}")

            # If existing data is a string, try to parse it as a dict
            if isinstance(existing_data, str):
                try:
                    existing_data = json.loads(existing_data)
                    logger.debug("Existing data was a string, parsed to JSON.")
                except Exception as e:
                    # If parsing fails, start fresh
                    existing_data = {}
                    logger.warning(
                        f"Failed to parse existing data as JSON: {e}.  Starting with empty existing_data.")

            # Merge existing preferences with new ones, only updating non-None values
            for field, value in preferences.dict(exclude_none=True).items():
                logger.debug(
                    f"Merging preference field: {field}, Value: {value}")
                # For lists, extend instead of replace if field exists
                if isinstance(value, list) and field in existing_data and isinstance(existing_data[field], list):
                    # Add only unique items
                    existing_data[field] = list(
                        set(existing_data[field] + value))
                    logger.debug(
                        f"Extended existing list for field {field}: {existing_data[field]}")
                else:
                    existing_data[field] = value
                    logger.debug(
                        f"Updated field {field}: {existing_data[field]}")

            response = self.memory_client.update(
                memory_id, existing_data, metadata=metadata)
            logger.info(
                f"User preferences updated. Response from memory client: {response}")
            return response

        # Otherwise create new preferences
        logger.info("No existing preferences found, creating new preferences.")
        response = self.memory_client.add(
            preferences.dict(exclude_none=True),
            user_id=user_id,
            metadata=metadata
        )
        logger.info(
            f"New user preferences created. Response from memory client: {response}")
        return response

    def get_user_preferences(self, user_id: str) -> Optional[UserPreference]:
        """Get stored user preferences."""
        logger.info(f"Getting user preferences for user {user_id}")
        preferences_search = self.memory_client.search(
            "user preferences",
            user_id=user_id,
            limit=1
        )
        logger.debug(
            f"Search result for user preferences: {preferences_search}")

        if preferences_search and preferences_search.get('memories') and len(preferences_search['memories']) > 0:
            pref_data = preferences_search['memories'][0].get('memory', {})
            logger.debug(f"Raw preference data: {pref_data}")

            # If data is a string, parse it
            if isinstance(pref_data, str):
                try:
                    pref_data = json.loads(pref_data)
                    logger.debug(
                        "Preference data was a string, parsed to JSON.")
                except Exception as e:
                    logger.warning(
                        f"Failed to parse preference data as JSON: {e}. Returning default UserPreference.")
                    return UserPreference()

            try:
                user_preference = UserPreference(**pref_data)
                logger.info(f"User preferences retrieved: {user_preference}")
                return user_preference
            except Exception as e:
                logger.error(
                    f"Error creating UserPreference object: {e}.  Data: {pref_data}. Returning default UserPreference")
                return UserPreference()  # Return default if parsing fails

        logger.info(
            "No user preferences found. Returning default UserPreference.")
        return UserPreference()

    def track_goal_progress(self,
                            user_id: str,
                            goal_progress: UserProgress) -> Dict:
        """
        Track user progress towards a specific goal.

        Args:
            user_id: Unique identifier for the user
            goal_progress: UserProgress object with progress data

        Returns:
            Response from memory client
        """
        logger.info(
            f"Tracking goal progress for user {user_id}, goal_id: {goal_progress.goal_id}")
        logger.debug(f"Goal progress data: {goal_progress}")

        # Check if goal already exists
        goal_search = self.memory_client.search(
            f"goal {goal_progress.goal_id}",
            user_id=user_id,
            limit=1
        )
        logger.debug(f"Search result for existing goal: {goal_search}")

        metadata = {
            'memory_type': MemoryType.USER.value,
            'data_type': 'progress',
            'goal_id': goal_progress.goal_id,
            'timestamp': datetime.now().isoformat()
        }
        logger.debug(f"Metadata for goal progress tracking: {metadata}")

        # Update goal if it exists
        if goal_search and goal_search.get('memories') and len(goal_search['memories']) > 0:
            memory_id = goal_search['memories'][0]['id']
            logger.info(f"Existing goal found. Memory ID: {memory_id}")

            # Update the last_update timestamp
            goal_progress.last_update = datetime.now()
            logger.debug(
                f"Updated last_update timestamp: {goal_progress.last_update}")

            response = self.memory_client.update(
                memory_id,
                goal_progress.dict(),
                metadata=metadata
            )
            logger.info(
                f"Goal progress updated. Response from memory client: {response}")
            return response

        # Create new goal tracking
        logger.info("No existing goal found, creating new goal tracking.")
        response = self.memory_client.add(
            goal_progress.dict(),
            user_id=user_id,
            metadata=metadata
        )
        logger.info(
            f"New goal progress tracked. Response from memory client: {response}")
        return response

    def get_goal_progress(self, user_id: str, goal_id: str) -> Optional[UserProgress]:
        """Get progress for a specific user goal."""
        logger.info(
            f"Getting goal progress for user {user_id}, goal_id: {goal_id}")
        goal_search = self.memory_client.search(
            f"goal {goal_id}",
            user_id=user_id,
            limit=1
        )
        logger.debug(f"Search result for goal progress: {goal_search}")

        if goal_search and goal_search.get('memories') and len(goal_search['memories']) > 0:
            goal_data = goal_search['memories'][0].get('memory', {})
            logger.debug(f"Raw goal data: {goal_data}")

            # If data is a string, parse it
            if isinstance(goal_data, str):
                try:
                    goal_data = json.loads(goal_data)
                    logger.debug("Goal data was a string, parsed to JSON.")
                except Exception as e:
                    logger.warning(
                        f"Failed to parse goal data as JSON: {e}. Returning None.")
                    return None

            try:
                user_progress = UserProgress(**goal_data)
                logger.info(f"Goal progress retrieved: {user_progress}")
                return user_progress
            except Exception as e:
                logger.error(
                    f"Error creating UserProgress from goal data: {e}, Data: {goal_data}. Returning None")
                return None  # Explicitly return None on failure.

        logger.info(
            f"No goal progress found for goal_id {goal_id}. Returning None.")
        return None

    def get_all_goals(self, user_id: str) -> List[UserProgress]:
        """Get all goals for a user."""
        logger.info(f"Getting all goals for user {user_id}")
        # Search for all progress records
        progress_search = self.memory_client.search(
            "data_type:progress",
            user_id=user_id,
            limit=100  # Adjust limit based on expected number of goals
        )
        logger.debug(f"Search results for all goals: {progress_search}")

        goals = []
        if progress_search and progress_search.get('memories'):
            for memory in progress_search['memories']:
                goal_data = memory.get('memory', {})
                logger.debug(f"Processing goal data: {goal_data}")

                # If data is a string, parse it
                if isinstance(goal_data, str):
                    try:
                        goal_data = json.loads(goal_data)
                        logger.debug("Goal data was a string, parsed to JSON.")
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse goal data as JSON: {e}. Skipping this goal.")
                        continue

                try:
                    goals.append(UserProgress(**goal_data))
                except Exception as e:
                    logger.error(
                        f"Error creating UserProgress from goal data: {e}, Data: {goal_data}. Skipping this goal.")
                    continue  # Skip to the next goal if parsing fails
            logger.info(f"Retrieved {len(goals)} goals for user {user_id}")

        else:
            logger.info(f"No goals found for user: {user_id}")
        return goals

    def get_relevant_chat_history(self, query: str, user_id: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve relevant chat history based on a query.

        Args:
            query: The query to search for relevant history
            user_id: Unique identifier for the user
            limit: Maximum number of relevant history items to return

        Returns:
            List of relevant chat interactions
        """
        logger.info(
            f"Getting relevant chat history for user {user_id}, query: '{query}', limit: {limit}")
        # Search with a narrowed query that focuses on chat interactions
        search_results = self.memory_client.search(
            f"{query} interaction_type:chat",
            user_id=user_id,
            limit=limit
        )
        logger.debug(
            f"Search results for relevant chat history: {search_results}")

        if search_results and search_results.get('memories'):
            logger.info(
                f"Found {len(search_results['memories'])} relevant chat history entries.")
            return search_results['memories']

        logger.info("No relevant chat history found.")
        return []

    def infer_preferences_from_interactions(self, user_id: str) -> UserPreference:
        """
        Analyze chat history to infer user preferences.
        Uses the memory client's LLM to analyze patterns and extract preferences.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Inferred UserPreference object
        """
        logger.info(
            f"Inferring preferences from interactions for user {user_id}")
        # This method would use the LLM to analyze chat history and extract preferences
        # We'll get the most recent chat interactions
        chat_history = self.memory_client.get_all(user_id=user_id)
        logger.debug(f"Retrieved chat history: {chat_history}")

        if not chat_history or not chat_history.get('memories'):
            logger.info(
                "No chat history found. Returning default UserPreference.")
            return UserPreference()

        # Filter for chat interactions only
        chat_interactions = [
            memory for memory in chat_history['memories']
            if memory.get('metadata', {}).get('interaction_type') == 'chat'
        ]
        logger.debug(f"Filtered chat interactions: {chat_interactions}")

        if not chat_interactions:
            logger.info(
                "No chat interactions found. Returning default UserPreference.")
            return UserPreference()

        # Here you would use the LLM to analyze the interactions and infer preferences
        # For now, we'll return an empty preference object
        # In a real implementation, you would:
        # 1. Extract the chat messages
        # 2. Send them to the LLM with a prompt to analyze preferences
        # 3. Parse the response into a UserPreference object
        logger.info(
            "Preference inference using LLM is not yet implemented. Returning default UserPreference.")
        return UserPreference()
