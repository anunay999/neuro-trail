from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import re

from app.crud.base import CRUDBase
from app.models.template import Template
from app.schemas.template import TemplateCreate, TemplateUpdate


class CRUDTemplate(CRUDBase[Template, TemplateCreate, TemplateUpdate]):
    """CRUD for template operations"""
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Template]:
        """
        Get template by name
        
        Args:
            db: Database session
            name: Template name
            
        Returns:
            Optional[Template]: Template or None if not found
        """
        return db.query(Template).filter(Template.name == name).first()
    
    def create_with_id(self, db: Session, *, obj_in: TemplateCreate, template_id: str) -> Template:
        """
        Create template with specific ID
        
        Args:
            db: Database session
            obj_in: Template create data
            template_id: Template ID
            
        Returns:
            Template: Created template
        """
        obj_in_data = obj_in.model_dump()
        db_obj = Template(
            id=template_id,
            name=obj_in_data["name"],
            description=obj_in_data["description"],
            template_content=obj_in_data["template_content"],
            input_variables=obj_in_data["input_variables"],
            is_system=obj_in_data.get("is_system", False)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_usage_count(self, db: Session, *, template_id: str) -> Optional[Template]:
        """
        Increment template usage count
        
        Args:
            db: Database session
            template_id: Template ID
            
        Returns:
            Optional[Template]: Updated template or None if not found
        """
        template = self.get(db, id=template_id)
        if not template:
            return None
        
        template.usage_count = (template.usage_count or 0) + 1
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return template
    
    def get_system_templates(self, db: Session) -> List[Template]:
        """
        Get all system templates
        
        Args:
            db: Database session
            
        Returns:
            List[Template]: List of system templates
        """
        return db.query(Template).filter(Template.is_system == True).all()
    
    def get_user_templates(self, db: Session) -> List[Template]:
        """
        Get all user templates
        
        Args:
            db: Database session
            
        Returns:
            List[Template]: List of user templates
        """
        return db.query(Template).filter(Template.is_system == False).all()
    
    def generate_id(self, name: str, db: Session) -> str:
        """
        Generate a unique ID from template name
        
        Args:
            name: Template name
            db: Database session
            
        Returns:
            str: Unique template ID
        """
        # Convert to lowercase and replace spaces with underscores
        base_id = name.lower().replace(' ', '_')
        
        # Remove special characters
        base_id = re.sub(r'[^a-z0-9_]', '', base_id)
        
        # Check if ID already exists
        existing = self.get(db, id=base_id)
        if not existing:
            return base_id
        
        # Append number to make unique
        i = 1
        while True:
            new_id = f"{base_id}_{i}"
            existing = self.get(db, id=new_id)
            if not existing:
                return new_id
            i += 1


template = CRUDTemplate(Template)