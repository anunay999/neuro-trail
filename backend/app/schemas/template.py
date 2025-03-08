from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Any, List

from app.schemas.base import TimestampMixin


class TemplateBase(BaseModel):
    """Base template attributes"""
    name: str
    description: Optional[str] = None
    template_content: str
    input_variables: List[str]
    is_system: bool = False  # Whether this is a system template (can't be deleted)


class TemplateCreate(TemplateBase):
    """Attributes for creating a template"""
    pass


class TemplateUpdate(BaseModel):
    """Attributes for updating a template"""
    name: Optional[str] = None
    description: Optional[str] = None
    template_content: Optional[str] = None
    input_variables: Optional[List[str]] = None

    @field_validator('input_variables')
    def validate_inputs(cls, v, values):
        # If updating template_content, ensure all variables are defined
        if 'template_content' in values and values['template_content'] and v:
            # Check if all variables in the template_content are in input_variables
            template = values['template_content']
            # Simple check for {variable} pattern
            import re
            variables = re.findall(r'\{([^{}]+)\}', template)
            missing = [var for var in variables if var not in v]
            if missing:
                raise ValueError(f"Template contains variables not in input_variables: {missing}")
        return v


class TemplateResponse(TemplateBase, TimestampMixin):
    """Template response model"""
    id: str
    usage_count: Optional[int] = 0

    class Config:
        from_attributes = True