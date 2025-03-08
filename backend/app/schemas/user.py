from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from app.schemas.base import TimestampMixin


class ResponseStyle(str, Enum):
    """Response style enum"""
    DEFAULT = "default"
    FRIENDLY = "friendly"
    ACADEMIC = "academic"
    CONCISE = "concise"
    SOCRATIC = "socratic"
    BEGINNER = "beginner"
    EXPERT = "expert"


class ResponseLength(str, Enum):
    """Response length enum"""
    VERY_BRIEF = "very_brief"
    BRIEF = "brief"
    BALANCED = "balanced"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class ExpertiseLevel(str, Enum):
    """Expertise level enum"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UserPreferences(BaseModel):
    """User preferences model"""
    response_style: ResponseStyle = ResponseStyle.DEFAULT
    response_length: ResponseLength = ResponseLength.BALANCED
    expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    active_template_id: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None


class LearningGoal(BaseModel):
    """Learning goal model"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    priority: Optional[int] = 1
    progress: Optional[int] = 0  # 0-100%
    completed: bool = False
    related_topics: Optional[List[str]] = None


class UserGoals(BaseModel):
    """User learning goals model"""
    primary_goal: Optional[str] = None
    learning_goals: List[LearningGoal] = []
    learning_interests: Optional[List[str]] = None
    knowledge_gaps: Optional[List[str]] = None