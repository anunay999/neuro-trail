from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResponseBase(BaseModel):
    """Base for API responses"""
    success: bool = True
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """Parameters for pagination"""
    skip: int = 0
    limit: int = 100