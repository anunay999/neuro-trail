from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.user import User, UserPreference, UserGoal
from app.schemas.user import UserPreferences, UserGoals


class CRUDUser(CRUDBase[User, Dict[str, Any], Dict[str, Any]]):
    """CRUD for user operations"""
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            Optional[User]: User or None if not found
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: Email
            
        Returns:
            Optional[User]: User or None if not found
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_or_create_default(self, db: Session) -> User:
        """
        Get or create default user
        
        Args:
            db: Database session
            
        Returns:
            User: Default user
        """
        default_user = self.get(db, id="default")
        
        if not default_user:
            # Create default user
            default_user = User(
                id="default",
                username="default",
                email="default@example.com"
            )
            
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
        
        return default_user
    
    def is_superuser(self, user: User) -> bool:
        """
        Check if user is superuser
        
        Args:
            user: User
            
        Returns:
            bool: True if superuser, False otherwise
        """
        return user.is_superuser


class CRUDUserPreference(CRUDBase[UserPreference, Dict[str, Any], Dict[str, Any]]):
    """CRUD for user preference operations"""
    
    def get_by_user(self, db: Session, *, user_id: str) -> Optional[UserPreference]:
        """
        Get user preferences by user ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Optional[UserPreference]: User preferences or None if not found
        """
        return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    def get_or_create(self, db: Session, *, user_id: str) -> UserPreference:
        """
        Get or create user preferences
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            UserPreference: User preferences
        """
        user_pref = self.get_by_user(db, user_id=user_id)
        
        if not user_pref:
            # Create default preferences
            default_prefs = {
                "response_style": "default",
                "response_length": "balanced",
                "expertise_level": "intermediate",
                "active_template_id": "default"
            }
            
            user_pref = UserPreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                preferences=default_prefs
            )
            
            db.add(user_pref)
            db.commit()
            db.refresh(user_pref)
        
        return user_pref
    
    def update_preferences(
        self, db: Session, *, user_id: str, preferences: Dict[str, Any]
    ) -> Optional[UserPreference]:
        """
        Update user preferences
        
        Args:
            db: Database session
            user_id: User ID
            preferences: New preferences
            
        Returns:
            Optional[UserPreference]: Updated preferences or None if not found
        """
        user_pref = self.get_or_create(db, user_id=user_id)
        
        # Update preferences
        user_pref.preferences = preferences
        user_pref.updated_at = datetime.now()
        
        db.add(user_pref)
        db.commit()
        db.refresh(user_pref)
        
        return user_pref
    
    def set_active_template(
        self, db: Session, *, user_id: str, template_id: str
    ) -> Optional[UserPreference]:
        """
        Set active template
        
        Args:
            db: Database session
            user_id: User ID
            template_id: Template ID
            
        Returns:
            Optional[UserPreference]: Updated preferences or None if not found
        """
        user_pref = self.get_or_create(db, user_id=user_id)
        
        # Update active template
        preferences = user_pref.preferences or {}
        preferences["active_template_id"] = template_id
        user_pref.preferences = preferences
        
        db.add(user_pref)
        db.commit()
        db.refresh(user_pref)
        
        return user_pref


class CRUDUserGoal(CRUDBase[UserGoal, Dict[str, Any], Dict[str, Any]]):
    """CRUD for user goal operations"""
    
    def get_by_user(self, db: Session, *, user_id: str) -> List[UserGoal]:
        """
        Get user goals by user ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List[UserGoal]: List of user goals
        """
        return db.query(UserGoal).filter(
            UserGoal.user_id == user_id
        ).order_by(UserGoal.priority).all()
    
    def create_goal(
        self, 
        db: Session, 
        *, 
        user_id: str, 
        title: str,
        description: Optional[str] = None,
        target_date: Optional[datetime] = None,
        priority: Optional[int] = None,
        related_topics: Optional[List[str]] = None
    ) -> UserGoal:
        """
        Create a user goal
        
        Args:
            db: Database session
            user_id: User ID
            title: Goal title
            description: Optional goal description
            target_date: Optional target date
            priority: Optional priority
            related_topics: Optional related topics
            
        Returns:
            UserGoal: Created user goal
        """
        # Get max priority
        max_priority = db.query(UserGoal).filter(
            UserGoal.user_id == user_id
        ).count()
        
        goal = UserGoal(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            description=description,
            target_date=target_date,
            priority=priority or max_priority + 1,
            progress=0,
            completed=False,
            related_topics=related_topics or []
        )
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        return goal
    
    def update_progress(
        self, db: Session, *, goal_id: str, progress: int
    ) -> Optional[UserGoal]:
        """
        Update goal progress
        
        Args:
            db: Database session
            goal_id: Goal ID
            progress: New progress (0-100)
            
        Returns:
            Optional[UserGoal]: Updated goal or None if not found
        """
        goal = self.get(db, id=goal_id)
        if not goal:
            return None
        
        # Ensure progress is between 0 and 100
        progress = max(0, min(100, progress))
        
        goal.progress = progress
        goal.updated_at = datetime.now()
        
        # If progress is 100, mark as completed
        if progress == 100:
            goal.completed = True
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        return goal
    
    def toggle_completed(self, db: Session, *, goal_id: str) -> Optional[UserGoal]:
        """
        Toggle goal completed status
        
        Args:
            db: Database session
            goal_id: Goal ID
            
        Returns:
            Optional[UserGoal]: Updated goal or None if not found
        """
        goal = self.get(db, id=goal_id)
        if not goal:
            return None
        
        goal.completed = not goal.completed
        goal.updated_at = datetime.now()
        
        # If marked as completed, set progress to 100
        if goal.completed:
            goal.progress = 100
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        return goal


user = CRUDUser(User)
user_preference = CRUDUserPreference(UserPreference)
user_goal = CRUDUserGoal(UserGoal)