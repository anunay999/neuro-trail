from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.user import UserPreferences, UserGoals

router = APIRouter()

@router.get("/", response_model=UserPreferences)
async def get_preferences(
    db: Session = Depends(get_db)
):
    """Get user preferences (using default user for now)"""
    user_service = UserService(db)
    preferences = user_service.get_user_preferences(user_id="default")
    return preferences

@router.put("/", response_model=UserPreferences)
async def update_preferences(
    preferences: UserPreferences,
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    user_service = UserService(db)
    updated_preferences = user_service.update_user_preferences(
        user_id="default",
        preferences=preferences
    )
    return updated_preferences

@router.get("/goals", response_model=UserGoals)
async def get_goals(
    db: Session = Depends(get_db)
):
    """Get user learning goals"""
    user_service = UserService(db)
    goals = user_service.get_user_goals(user_id="default")
    return goals

@router.put("/goals", response_model=UserGoals)
async def update_goals(
    goals: UserGoals,
    db: Session = Depends(get_db)
):
    """Update user learning goals"""
    user_service = UserService(db)
    updated_goals = user_service.update_user_goals(
        user_id="default",
        goals=goals
    )
    return updated_goals