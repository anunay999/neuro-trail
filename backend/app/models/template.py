from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime

from app.db.base_class import Base


class Template(Base):
    """Model for storing prompt templates"""
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    template_content = Column(Text, nullable=False)
    input_variables = Column(ARRAY(String), default=[])
    is_system = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)