from fastapi import APIRouter, Depends, status
from typing import Dict, Any
from datetime import datetime
import os

# Create a router for health-related endpoints
router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify API is running.
    Returns server status and basic system metrics.
    """
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }