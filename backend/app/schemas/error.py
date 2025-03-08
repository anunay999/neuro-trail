from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None