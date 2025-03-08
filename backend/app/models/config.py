from sqlalchemy import Column, String, JSON, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base_class import Base


class Config(Base):
    """Model for storing application configuration"""
    
    id = Column(String, primary_key=True)
    config_data = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)