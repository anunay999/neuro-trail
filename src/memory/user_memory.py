from datetime import datetime
from typing import Any, Dict, List, Optional

from .memory_client import AbstractMemoryClient, MemoryType
from pydantic import BaseModel, Field


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
        self.memory_client = memory_client

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
        if metadata is None:
            metadata = {}

        # Add timestamp if not present
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()

        # Add memory type
        metadata['memory_type'] = MemoryType.USER.value
        metadata['interaction_type'] = 'chat'

        return self.memory_client.add(messages, user_id=user_id, metadata=metadata)

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
        # First try to get existing preferences
        preferences_search = self.memory_client.search(
            "user preferences",
            user_id=user_id,
            limit=1
        )

        metadata = {
            'memory_type': MemoryType.USER.value,
            'data_type': 'preferences',
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }

        # If preferences exist, update them
        if preferences_search and preferences_search.get('memories') and len(preferences_search['memories']) > 0:
            memory_id = preferences_search['memories'][0]['id']
            existing_data = preferences_search['memories'][0].get('memory', {})

            # If existing data is a string, try to parse it as a dict
            if isinstance(existing_data, str):
                try:
                    import json
                    existing_data = json.loads(existing_data)
                except Exception:
                    # If parsing fails, start fresh
                    existing_data = {}

            # Merge existing preferences with new ones, only updating non-None values
            for field, value in preferences.dict(exclude_none=True).items():
                # For lists, extend instead of replace if field exists
                if isinstance(value, list) and field in existing_data and isinstance(existing_data[field], list):
                    # Add only unique items
                    existing_data[field] = list(
                        set(existing_data[field] + value))
                else:
                    existing_data[field] = value

            return self.memory_client.update(memory_id, existing_data, metadata=metadata)

        # Otherwise create new preferences
        return self.memory_client.add(
            preferences.dict(exclude_none=True),
            user_id=user_id,
            metadata=metadata
        )

    def get_user_preferences(self, user_id: str) -> Optional[UserPreference]:
        """Get stored user preferences."""
        preferences_search = self.memory_client.search(
            "user preferences",
            user_id=user_id,
            limit=1
        )

        if preferences_search and preferences_search.get('memories') and len(preferences_search['memories']) > 0:
            pref_data = preferences_search['memories'][0].get('memory', {})

            # If data is a string, parse it
            if isinstance(pref_data, str):
                try:
                    import json
                    pref_data = json.loads(pref_data)
                except Exception:
                    return UserPreference()

            return UserPreference(**pref_data)

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
        # Check if goal already exists
        goal_search = self.memory_client.search(
            f"goal {goal_progress.goal_id}",
            user_id=user_id,
            limit=1
        )

        metadata = {
            'memory_type': MemoryType.USER.value,
            'data_type': 'progress',
            'goal_id': goal_progress.goal_id,
            'timestamp': datetime.now().isoformat()
        }

        # Update goal if it exists
        if goal_search and goal_search.get('memories') and len(goal_search['memories']) > 0:
            memory_id = goal_search['memories'][0]['id']

            # Update the last_update timestamp
            goal_progress.last_update = datetime.now()

            return self.memory_client.update(
                memory_id,
                goal_progress.dict(),
                metadata=metadata
            )

        # Create new goal tracking
        return self.memory_client.add(
            goal_progress.dict(),
            user_id=user_id,
            metadata=metadata
        )

    def get_goal_progress(self, user_id: str, goal_id: str) -> Optional[UserProgress]:
        """Get progress for a specific user goal."""
        goal_search = self.memory_client.search(
            f"goal {goal_id}",
            user_id=user_id,
            limit=1
        )

        if goal_search and goal_search.get('memories') and len(goal_search['memories']) > 0:
            goal_data = goal_search['memories'][0].get('memory', {})

            # If data is a string, parse it
            if isinstance(goal_data, str):
                try:
                    import json
                    goal_data = json.loads(goal_data)
                except Exception:
                    return None

            return UserProgress(**goal_data)

        return None

    def get_all_goals(self, user_id: str) -> List[UserProgress]:
        """Get all goals for a user."""
        # Search for all progress records
        progress_search = self.memory_client.search(
            "data_type:progress",
            user_id=user_id,
            limit=100  # Adjust limit based on expected number of goals
        )

        goals = []
        if progress_search and progress_search.get('memories'):
            for memory in progress_search['memories']:
                goal_data = memory.get('memory', {})

                # If data is a string, parse it
                if isinstance(goal_data, str):
                    try:
                        import json
                        goal_data = json.loads(goal_data)
                    except Exception:
                        continue

                goals.append(UserProgress(**goal_data))

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
        # Search with a narrowed query that focuses on chat interactions
        search_results = self.memory_client.search(
            f"{query} interaction_type:chat",
            user_id=user_id,
            limit=limit
        )

        if search_results and search_results.get('memories'):
            return search_results['memories']

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
        # This method would use the LLM to analyze chat history and extract preferences
        # We'll get the most recent chat interactions
        chat_history = self.memory_client.get_all(user_id=user_id)

        if not chat_history or not chat_history.get('memories'):
            return UserPreference()

        # Filter for chat interactions only
        chat_interactions = [
            memory for memory in chat_history['memories']
            if memory.get('metadata', {}).get('interaction_type') == 'chat'
        ]

        if not chat_interactions:
            return UserPreference()

        # Here you would use the LLM to analyze the interactions and infer preferences
        # For now, we'll return an empty preference object
        # In a real implementation, you would:
        # 1. Extract the chat messages
        # 2. Send them to the LLM with a prompt to analyze preferences
        # 3. Parse the response into a UserPreference object

        return UserPreference()
