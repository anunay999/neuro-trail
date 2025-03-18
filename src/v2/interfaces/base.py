import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from smolagents import Tool


class MessageRole(str, Enum):
    user = "user"
    system = "system"
    assistant = "assistant"
    agent = "agent"


class ExpertiseLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


# Conversation info


class Message(BaseModel):
    role: MessageRole
    content: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_info: Dict[str, Any] = Field(default_factory=dict)


class HistoryMessage(Message):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    messages: List[HistoryMessage] = Field(default_factory=list)


class UserQuery(BaseModel):
    query: str
    history: Optional[ConversationHistory] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# User Learning state/preferences


class Skill(BaseModel):
    topic: str
    expertise_level: ExpertiseLevel
    last_updated: datetime = Field(default_factory=datetime.now)
    progress: float = 0.0  # 0.0 to 1.0 representing progress within the level


class LearningGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    target_skills: List[Skill]
    deadline: Optional[datetime] = None
    progress: float = 0.0


class UserPreference(BaseModel):
    learning_style: Optional[str] = None
    content_format: List[str] = ["text"]
    session_duration: Optional[int] = None  # preferred session length in minutes
    difficulty_preference: Optional[float] = None  # 0.0-1.0 scale (easy to challenging)
    tool_preferences: Dict[str, float] = Field(
        default_factory=dict
    )  # tool_id to preference score


class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    preferences: UserPreference = Field(default_factory=UserPreference)
    skills: List[Skill] = Field(default_factory=list)
    learning_goals: List[LearningGoal] = Field(default_factory=list)
    learning_history: Dict[str, Any] = Field(default_factory=dict)


# Retrievers


class RetrievalRequest(BaseModel):
    query: str
    history: Optional[ConversationHistory] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    content: str
    source: str
    chunk_id: str
    similarity_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalResponse(BaseModel):
    results: List[RetrievalResult]
    query: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Tools: we follow smolagents tool interface


class ToolCallInput(BaseModel):
    tool_id: str
    parameters: Dict[str, Any]
    user_profile: Optional[UserProfile] = None


class ToolCallOutput(BaseModel):
    result: Any
    details: Dict[str, Any] = Field(default_factory=dict)


# Supervisor models


class SupervisorInput(BaseModel):
    user_query: UserQuery
    user_profile: UserProfile
    tools: List[Tool] = Field(default_factory=list)


class SupervisorOutput(BaseModel):
    tool_calls: List[ToolCallInput] = Field(default_factory=list)
    generation_params: Dict[str, Any] = Field(default_factory=dict)
    response_strategy: Dict[str, Any] = Field(default_factory=dict)


# Generative models


class GenerationInput(BaseModel):
    user_query: UserQuery
    retrieval_responses: List[RetrievalResponse] = Field(default_factory=list)
    user_profile: UserProfile
    generation_params: Dict[str, Any] = Field(default_factory=dict)


class GenerationOutput(BaseModel):
    content: str
    sources: List[str] = Field(default_factory=list)
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Evaluation/Shield models


class EvaluationInput(BaseModel):
    user_query: UserQuery
    generated_content: GenerationOutput
    user_profile: UserProfile
    evaluation_criteria: Dict[str, Any] = Field(default_factory=dict)


class EvaluationOutput(BaseModel):
    score: float  # 0.0 to 1.0
    feedback: Dict[str, Any]
    pass_threshold: float
    passed: bool
    improvement_suggestions: Optional[str] = None


# User Learning/profile modification models


class ProfileUpdateInput(BaseModel):
    user_profile: UserProfile
    user_query: UserQuery
    interaction_data: Dict[str, Any] = Field(default_factory=dict)


class ProfileUpdateOutput(BaseModel):
    updated_profile: UserProfile
    reasoning: str
    suggested_goals: List[LearningGoal] = Field(default_factory=list)
