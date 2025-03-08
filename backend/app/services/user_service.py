from fastapi import Depends
from sqlalchemy.orm import Session
import uuid
import logging

from app.db.session import get_db
from app.models.user import User, UserPreference, UserGoal
from app.schemas.user import UserPreferences, UserGoals, LearningGoal
from app.core.exceptions import NotFoundError

from app.crud.user import user, user_preference, user_goal


# Configure logging
logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and preferences"""
    
    def __init__(self, db: Session):
        """
        Initialize user service
        
        Args:
            db: Database session
        """
        self.db = db
        self._ensure_default_user()
    
    def _ensure_default_user(self) -> None:
        """Ensure default user exists for development"""
        # Check if default user exists
        default_user = user.get_or_create_default(db=self.db)

        if not default_user:
            # Create default preferences
            self._create_default_preferences("default")
    
    def _create_default_preferences(self, user_id: str) -> UserPreference:
        """
        Create default preferences for a user
        
        Args:
            user_id: User ID
            
        Returns:
            UserPreference: Created preferences
        """
        # Default preferences
        default_prefs = {
            "response_style": "default",
            "response_length": "balanced",
            "expertise_level": "intermediate",
            "active_template_id": "default"
        }
        
        # Create preferences record
        user_pref = UserPreference(
            id=str(uuid.uuid4()),
            user_id=user_id,
            preferences=default_prefs
        )
        
        self.db.add(user_pref)
        self.db.commit()
        self.db.refresh(user_pref)
        
        return user_pref
    
    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """
        Get user preferences
        
        Args:
            user_id: User ID
            
        Returns:
            UserPreferences: User preferences
        """
        # Get preferences from database
        user_pref = user_preference.get_or_create(db=self.db, user_id=user_id)
        
        # Extract preferences
        prefs = user_pref.preferences or {}
        
        # Convert to schema
        return UserPreferences(
            response_style=prefs.get("response_style", "default"),
            response_length=prefs.get("response_length", "balanced"),
            expertise_level=prefs.get("expertise_level", "intermediate"),
            active_template_id=prefs.get("active_template_id", "default"),
            custom_settings=prefs.get("custom_settings", {})
        )
    
    def update_user_preferences(
        self, 
        user_id: str, 
        preferences: UserPreferences
    ) -> UserPreferences:
        """
        Update user preferences
        
        Args:
            user_id: User ID
            preferences: New preferences
            
        Returns:
            UserPreferences: Updated preferences
        """
        # Get preferences from database
        prefs_dict = {
                "response_style": preferences.response_style,
                "response_length": preferences.response_length,
                "expertise_level": preferences.expertise_level,
                "active_template_id": preferences.active_template_id,
                "custom_settings": preferences.custom_settings or {}
            }
        user_preference.update_preferences(db=self.db, user_id=user_id, preferences=prefs_dict)
        
        logger.info(f"Updated preferences for user: {user_id}")
        
        return preferences
    
    def get_user_goals(self, user_id: str) -> UserGoals:
        """
        Get user learning goals
        
        Args:
            user_id: User ID
            
        Returns:
            UserGoals: User goals
        """
        # Get goals from database
        goals = user_goal.get_by_user(db=self.db, user_id=user_id)
        
        # Convert to schema
        learning_goals = []
        for goal in goals:
            learning_goals.append(
                LearningGoal(
                    id=goal.id,
                    title=goal.title,
                    description=goal.description,
                    target_date=goal.target_date,
                    priority=goal.priority,
                    progress=goal.progress,
                    completed=goal.completed,
                    related_topics=goal.related_topics
                )
            )
        
        # Get preferences for primary goal
        user_pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        primary_goal = None
        if user_pref and user_pref.preferences:
            primary_goal = user_pref.preferences.get("primary_goal")
        
        return UserGoals(
            primary_goal=primary_goal,
            learning_goals=learning_goals,
            learning_interests=user_pref.preferences.get("learning_interests", []) if user_pref else [],
            knowledge_gaps=user_pref.preferences.get("knowledge_gaps", []) if user_pref else []
        )
    
    def update_user_goals(self, user_id: str, goals: UserGoals) -> UserGoals:
        """
        Update user learning goals
        
        Args:
            user_id: User ID
            goals: New goals
            
        Returns:
            UserGoals: Updated goals
        """
        # Get user preference
        user_pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        # Create if not exists
        if not user_pref:
            user_pref = UserPreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                preferences={}
            )
            self.db.add(user_pref)
        
        # Update preferences
        prefs = user_pref.preferences or {}
        prefs["primary_goal"] = goals.primary_goal
        prefs["learning_interests"] = goals.learning_interests
        prefs["knowledge_gaps"] = goals.knowledge_gaps
        user_pref.preferences = prefs
        
        # Update goals
        # First, get existing goals
        existing_goals = self.db.query(UserGoal).filter(
            UserGoal.user_id == user_id
        ).all()
        
        # Create mapping of existing goals by ID
        existing_goals_map = {goal.id: goal for goal in existing_goals}
        
        # Process each goal
        for i, goal_data in enumerate(goals.learning_goals):
            if goal_data.id and goal_data.id in existing_goals_map:
                # Update existing goal
                goal = existing_goals_map[goal_data.id]
                goal.title = goal_data.title
                goal.description = goal_data.description
                goal.target_date = goal_data.target_date
                goal.priority = i + 1  # Set priority based on order
                goal.progress = goal_data.progress
                goal.completed = goal_data.completed
                goal.related_topics = goal_data.related_topics
            else:
                # Create new goal
                goal = UserGoal(
                    id=goal_data.id or str(uuid.uuid4()),
                    user_id=user_id,
                    title=goal_data.title,
                    description=goal_data.description,
                    target_date=goal_data.target_date,
                    priority=i + 1,  # Set priority based on order
                    progress=goal_data.progress,
                    completed=goal_data.completed,
                    related_topics=goal_data.related_topics
                )
                self.db.add(goal)
        
        # Delete goals not in the update
        goal_ids = [goal.id for goal in goals.learning_goals if goal.id]
        for goal in existing_goals:
            if goal.id not in goal_ids:
                self.db.delete(goal)
        
        self.db.commit()
        
        logger.info(f"Updated goals for user: {user_id}")
        
        return self.get_user_goals(user_id)
    
    def add_learning_goal(self, user_id: str, goal: LearningGoal) -> LearningGoal:
        """
        Add a learning goal
        
        Args:
            user_id: User ID
            goal: Goal to add
            
        Returns:
            LearningGoal: Added goal
        """
    

        goal_obj = user_goal.create_goal(
                db=self.db,
                user_id=user_id,
                title=goal.title,
                description=goal.description,
                target_date=goal.target_date,
                priority=goal.priority,
                related_topics=goal.related_topics
            )
        
        
        logger.info(f"Added learning goal for user {user_id}: {goal_obj.title}")
        
        # Return updated goal
        return LearningGoal(
            id=goal_obj.id,
            title=goal_obj.title,
            description=goal_obj.description,
            target_date=goal_obj.target_date,
            priority=goal_obj.priority,
            progress=goal_obj.progress,
            completed=goal_obj.completed,
            related_topics=goal_obj.related_topics
        )