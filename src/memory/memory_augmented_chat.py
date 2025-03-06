import logging
from datetime import datetime
from typing import Dict, Generator, List

import streamlit as st
from .memory_client import create_memory_client_from_settings
from .user_memory import UserMemory, UserPreference, UserProgress

from core.learning_canvas import canvas

logger = logging.getLogger(__name__)


class MemoryAugmentedChat:
    """
    Class to integrate memory capabilities with the Neuro Trail chat interface.
    """
    def __init__(self):
        """Initialize with application settings."""
        self.memory_client = create_memory_client_from_settings()
        self.user_memory = UserMemory(self.memory_client)
        
    def answer_query(self, query: str, user_id: str = None) -> Generator[str, None, None]:
        """
        Process user query and generate a response with memory-augmented context.
        
        Args:
            query: The user's question or prompt
            user_id: Unique identifier for the user, defaults to session ID if None
            
        Returns:
            Generator yielding response tokens
        """
        # Use session ID if user_id not provided
        if user_id is None:
            user_id = st.session_state.get("session_id", "anonymous")
        
        # Get current personalization settings
        length = st.session_state.get("response_length", "Balanced")
        expertise = st.session_state.get("expertise_level", "Intermediate")
        
        # Retrieve relevant chat history
        relevant_history = self.user_memory.get_relevant_chat_history(query, user_id)
        
        # Retrieve user preferences
        user_preferences = self.user_memory.get_user_preferences(user_id)
        
        # Update preferences based on current settings if different
        if user_preferences.response_length_preference != length.lower():
            user_preferences.response_length_preference = length.lower()
            self.user_memory.update_user_preferences(user_id, user_preferences)
            
        if user_preferences.expertise_level != expertise.lower():
            user_preferences.expertise_level = expertise.lower()
            self.user_memory.update_user_preferences(user_id, user_preferences)
        
        # Create context from relevant history and preferences
        context = self._build_context_from_memory(relevant_history, user_preferences)
        
        # Get response from the canvas (your LLM interface)
        # We'll simulate the response as a generator for this example
        
        # Format the query with personalization and context
        personalized_query = self._format_query_with_context(query, context, user_preferences)
        
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
        self._analyze_interaction_for_preferences(messages, user_id)
    
    def _build_context_from_memory(self, 
                                  relevant_history: List[Dict], 
                                  user_preferences: UserPreference) -> str:
        """Build context string from memory components."""
        context_parts = []
        
        # Add relevant history
        if relevant_history:
            context_parts.append("Relevant prior conversations:")
            for i, history in enumerate(relevant_history[:3]):  # Limit to 3 most relevant
                memory_content = history.get('memory', '')
                if isinstance(memory_content, list):
                    # Format message list
                    conversation = "\n".join([f"{msg.get('role', '')}: {msg.get('content', '')}" 
                                             for msg in memory_content if isinstance(msg, dict)])
                    context_parts.append(f"{i+1}. {conversation}")
                else:
                    context_parts.append(f"{i+1}. {memory_content}")
        
        # Add user preferences
        preferences_dict = user_preferences.dict(exclude_none=True)
        if preferences_dict:
            context_parts.append("\nUser preferences:")
            for key, value in preferences_dict.items():
                if isinstance(value, list):
                    context_parts.append(f"- {key.replace('_', ' ')}: {', '.join(value)}")
                else:
                    context_parts.append(f"- {key.replace('_', ' ')}: {value}")
        
        return "\n".join(context_parts)
    
    def _format_query_with_context(self, 
                                  query: str, 
                                  context: str, 
                                  preferences: UserPreference) -> str:
        """Format the query with context and personalization."""
        from core.prompt_templates import prompt_template_manager
        
        length = preferences.response_length_preference or "balanced"
        expertise = preferences.expertise_level or "intermediate"
        
        # Use your existing template manager
        formatted_prompt = prompt_template_manager.format_prompt(
            context=context,
            question=query,
            length=length,
            expertise=expertise
        )
        
        return formatted_prompt
    
    def _store_interaction(self, messages: List[Dict[str, str]], user_id: str, query: str):
        """Store the interaction in memory."""
        try:
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'query_intent': self._categorize_query(query)
            }
            
            self.user_memory.store_chat_interaction(messages, user_id, metadata)
            logger.info(f"Stored chat interaction for user {user_id}")
        except Exception as e:
            logger.error(f"Error storing chat interaction: {str(e)}")
    
    def _categorize_query(self, query: str) -> str:
        #TODO : Implement intent detection
        """Simple query categorization."""
        # This could be expanded to use more sophisticated categorization
        if any(word in query.lower() for word in ['how', 'explain', 'describe']):
            return 'explanation'
        elif any(word in query.lower() for word in ['what is', 'definition', 'mean']):
            return 'definition'
        elif any(word in query.lower() for word in ['example', 'show me', 'demonstrate']):
            return 'example'
        elif any(word in query.lower() for word in ['compare', 'difference', 'versus']):
            return 'comparison'
        else:
            return 'general'
    
    def _analyze_interaction_for_preferences(self, messages: List[Dict[str, str]], user_id: str):
        """Analyze the interaction to infer user preferences."""
        try:
            # In a real implementation, this would use more sophisticated analysis
            # For now, we'll use a simple rule-based approach
            
            # Extract the user's latest message
            user_message = next((msg['content'] for msg in messages if msg['role'] == 'user'), None)
            if not user_message:
                return
            
            # Simple inference
            preferences = UserPreference()
            
            # Check for expertise level indicators
            if any(word in user_message.lower() for word in ['beginner', 'novice', 'new', 'starting']):
                preferences.expertise_level = 'beginner'
            elif any(word in user_message.lower() for word in ['advanced', 'expert', 'professional']):
                preferences.expertise_level = 'advanced'
            
            # Check for response length preference
            if any(word in user_message.lower() for word in ['brief', 'short', 'concise', 'quick']):
                preferences.response_length_preference = 'concise'
            elif any(word in user_message.lower() for word in ['detailed', 'comprehensive', 'thorough']):
                preferences.response_length_preference = 'detailed'
            
            # Check for interests
            interests = []
            common_topics = ['machine learning', 'coding', 'python', 'data science', 'mathematics']
            for topic in common_topics:
                if topic in user_message.lower():
                    interests.append(topic)
            
            if interests:
                preferences.interests = interests
            
            # Only update if we inferred something
            if preferences.dict(exclude_none=True):
                self.user_memory.update_user_preferences(user_id, preferences, confidence=0.7)
                logger.info(f"Updated user preferences for {user_id} based on interaction analysis")
                
        except Exception as e:
            logger.error(f"Error analyzing interaction for preferences: {str(e)}")
    
    def track_learning_goal(self, 
                           user_id: str, 
                           goal_description: str, 
                           milestones: List[str] = None) -> str:
        """
        Create a new learning goal for the user.
        
        Args:
            user_id: Unique identifier for the user
            goal_description: Description of the learning goal
            milestones: Optional list of milestone descriptions
            
        Returns:
            ID of the created goal
        """
        import uuid
        
        goal_id = str(uuid.uuid4())
        
        # Create milestone objects
        milestone_objects = []
        if milestones:
            for i, desc in enumerate(milestones):
                milestone_objects.append({
                    "id": str(uuid.uuid4()),
                    "description": desc,
                    "order": i+1,
                    "completed": False,
                    "completion_date": None
                })
        
        # Create goal progress object
        goal_progress = UserProgress(
            goal_id=goal_id,
            goal_description=goal_description,
            milestones=milestone_objects,
            completion_percentage=0.0,
            status="in_progress"
        )
        
        # Store in memory
        self.user_memory.track_goal_progress(user_id, goal_progress)
        
        return goal_id
    
    def update_goal_progress(self, 
                            user_id: str, 
                            goal_id: str, 
                            milestone_id: str = None, 
                            completion_percentage: float = None) -> bool:
        """
        Update progress on a learning goal.
        
        Args:
            user_id: Unique identifier for the user
            goal_id: ID of the goal to update
            milestone_id: Optional ID of the milestone to mark as completed
            completion_percentage: Optional direct update to completion percentage
            
        Returns:
            Success status
        """
        # Get current goal progress
        goal_progress = self.user_memory.get_goal_progress(user_id, goal_id)
        if not goal_progress:
            logger.error(f"Goal {goal_id} not found for user {user_id}")
            return False
        
        # Update milestone if provided
        if milestone_id:
            for milestone in goal_progress.milestones:
                if milestone.get("id") == milestone_id:
                    milestone["completed"] = True
                    milestone["completion_date"] = datetime.now().isoformat()
                    
                    # Recalculate completion percentage based on milestones
                    completed_count = sum(1 for m in goal_progress.milestones if m.get("completed"))
                    total_count = len(goal_progress.milestones)
                    goal_progress.completion_percentage = (completed_count / total_count * 100) if total_count > 0 else 0
                    
                    # If all milestones complete, mark goal as completed
                    if completed_count == total_count:
                        goal_progress.status = "completed"
                    
                    break
        
        # Direct update to completion percentage if provided
        if completion_percentage is not None:
            goal_progress.completion_percentage = min(max(completion_percentage, 0.0), 100.0)
            
            # If 100%, mark as completed
            if goal_progress.completion_percentage >= 100.0:
                goal_progress.status = "completed"
        
        # Update last_update timestamp
        goal_progress.last_update = datetime.now()
        
        # Store updated progress
        self.user_memory.track_goal_progress(user_id, goal_progress)
        
        return True
    
    def get_learning_recommendations(self, user_id: str) -> List[Dict]:
        """
        Generate personalized learning recommendations based on user preferences,
        goals, and interaction history.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of recommendation dictionaries
        """
        # Get user preferences
        preferences = self.user_memory.get_user_preferences(user_id)
        
        # Get current goals
        goals = self.user_memory.get_all_goals(user_id)
        
        # This would typically use an LLM to generate recommendations
        # For now, we'll return a simple structure
        recommendations = []
        
        # Based on interests
        if preferences.interests:
            for interest in preferences.interests[:3]:  # Limit to top 3
                recommendations.append({
                    "type": "interest_based",
                    "title": f"Explore more about {interest}",
                    "description": f"Based on your interest in {interest}",
                    "confidence": 0.8
                })
        
        # Based on in-progress goals
        for goal in goals:
            if goal.status == "in_progress":
                incomplete_milestones = [m for m in goal.milestones if not m.get("completed")]
                if incomplete_milestones:
                    next_milestone = incomplete_milestones[0]
                    recommendations.append({
                        "type": "goal_based",
                        "title": f"Continue progress on: {goal.goal_description}",
                        "description": f"Next step: {next_milestone.get('description')}",
                        "confidence": 0.9,
                        "goal_id": goal.goal_id
                    })
        
        # If we have expertise level, suggest content at that level
        if preferences.expertise_level:
            recommendations.append({
                "type": "level_based",
                "title": f"{preferences.expertise_level.capitalize()} level content",
                "description": f"Content matching your {preferences.expertise_level} expertise level",
                "confidence": 0.7
            })
        
        return recommendations


# Function to initialize memory system in Streamlit
def initialize_memory_system():
    """Initialize the memory system and store in session state."""
    if "memory_system" not in st.session_state:
        st.session_state.memory_system = MemoryAugmentedChat()
        
        # Generate a session ID if not present
        if "session_id" not in st.session_state:
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
        
        # Set default user (in a real app, this would come from authentication)
        st.session_state.user_id = st.session_state.session_id
        
        logger.info(f"Memory system initialized with session ID: {st.session_state.session_id}")

