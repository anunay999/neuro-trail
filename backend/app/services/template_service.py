from fastapi import Depends
from sqlalchemy.orm import Session
import uuid
import logging
from typing import List, Dict, Any, Optional
import re
import json

from app.db.session import get_db
from app.models.template import Template
from app.models.user import UserPreference
from app.schemas.template import TemplateCreate, TemplateUpdate
from app.core.exceptions import NotFoundError, BadRequestError
from app.crud.template import template as crud_template


# Configure logging
logger = logging.getLogger(__name__)


class TemplateService:
    """Service for prompt template management"""
    
    def __init__(self, db: Session):
        """
        Initialize template service
        
        Args:
            db: Database session
        """
        self.db = db
        self._ensure_default_templates()
    
    def _ensure_default_templates(self) -> None:
        """Ensure default templates exist in the database"""
        default_templates = self._get_default_templates()
        
        for template_id, template_data in default_templates.items():
            # Check if template exists
            existing = self.db.query(Template).filter(
                Template.id == template_id
            ).first()
            
            if not existing:
                # Create template
                template = Template(
                    id=template_id,
                    name=template_data["name"],
                    description=template_data["description"],
                    template_content=template_data["template_content"],
                    input_variables=template_data["input_variables"],
                    is_system=True
                )
                
                self.db.add(template)
        
        # Commit if any templates were added
        self.db.commit()
    
    def _get_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get default templates
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of template ID to template data
        """
        return {
            "default": {
                "name": "Default",
                "description": "Standard balanced response",
                "template_content": """
                You are a helpful assistant for the Neuro Trail learning platform.
                Answer the following question based on the provided context.
                If the context doesn't contain relevant information, say so.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
            },
            "friendly": {
                "name": "Friendly",
                "description": "Warm, conversational responses",
                "template_content": """
                You are a friendly and supportive learning assistant for Neuro Trail.
                Your tone is warm, encouraging, and conversational.
                Answer the following question in a friendly manner, using simple language and relatable examples.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
            },
            "academic": {
                "name": "Academic",
                "description": "Formal, scholarly responses",
                "template_content": """
                You are an academic expert for the Neuro Trail learning platform.
                Your tone is formal, precise, and scholarly.
                Provide a well-structured response with references to academic concepts where relevant.
                Use proper terminology and maintain an educational tone throughout.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
            },
            "concise": {
                "name": "Concise",
                "description": "Brief, to-the-point responses",
                "template_content": """
                You are a concise assistant for the Neuro Trail learning platform.
                Keep your response brief and to the point.
                Focus only on the most essential information and avoid unnecessary elaboration.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
            },
            "socratic": {
                "name": "Socratic",
                "description": "Questions that prompt deeper thinking",
                "template_content": """
                You are a Socratic teaching assistant for the Neuro Trail learning platform.
                Instead of providing direct answers, guide the user to discover insights through thoughtful questions.
                Begin with a brief orientation to the topic, then pose 2-3 thought-provoking questions
                that will help the user reach their own understanding.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
            },
            "personalized": {
                "name": "Personalized",
                "description": "Personalized learning experience",
                "template_content": """
                You are a personalized learning assistant for the Neuro Trail platform.
                
                **Instructions**:
                - **Style**: {style}
                - **Response Length**: {length}
                - **Expertise Level**: {expertise}
                
                Previous conversation:
                {history}
                
                Context from documents:
                {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question", "history", "style", "length", "expertise"],
            }
        }
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Get template by ID
        
        Args:
            template_id: Template ID
            
        Returns:
            Optional[Template]: Template or None if not found
        """
        return self.db.query(Template).filter(Template.id == template_id).first()
    
    def get_templates(self) -> List[Template]:
        """
        Get all templates
        
        Returns:
            List[Template]: List of templates
        """
        return self.db.query(Template).order_by(Template.name).all()
    
    def create_template(self, template: TemplateCreate) -> Template:
        """
        Create a new template
        
        Args:
            template: Template data
            
        Returns:
            Template: Created template
            
        Raises:
            BadRequestError: If validation fails
        """
        # Validate template variables
        variables = self._extract_variables(template.template_content)
        for var in variables:
            if var not in template.input_variables:
                raise BadRequestError(
                    f"Template contains variable '{var}' not in input_variables"
                )
        
        # Generate ID from name
        template_id = crud_template.generate_id(template.name, db=self.db)
        db_template = template.create_with_id(
                        db=self.db,
                        obj_in=template,
                        template_id=template_id
                    )
        
        logger.info(f"Created template: {template_id}")
        
        return db_template
    
    def update_template(
        self, 
        template_id: str, 
        template: TemplateUpdate
    ) -> Optional[Template]:
        """
        Update a template
        
        Args:
            template_id: Template ID
            template: Template update data
            
        Returns:
            Optional[Template]: Updated template or None if not found
            
        Raises:
            BadRequestError: If validation fails or trying to update system template
        """
        db_template = self.get_template(template_id)
        if not db_template:
            return None
        
        # Check if system template
        if db_template.is_system:
            raise BadRequestError("Cannot update system template")
        
        # Update fields if provided
        if template.name is not None:
            db_template.name = template.name
        
        if template.description is not None:
            db_template.description = template.description
        
        if template.template_content is not None:
            db_template.template_content = template.template_content
        
        if template.input_variables is not None:
            # Validate template variables
            variables = self._extract_variables(db_template.template_content)
            for var in variables:
                if var not in template.input_variables:
                    raise BadRequestError(
                        f"Template contains variable '{var}' not in input_variables"
                    )
            
            db_template.input_variables = template.input_variables
        
        self.db.commit()
        self.db.refresh(db_template)
        
        logger.info(f"Updated template: {template_id}")
        
        return db_template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template
        
        Args:
            template_id: Template ID
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            BadRequestError: If trying to delete system template
        """
        db_template = self.get_template(template_id)
        if not db_template:
            return False
        
        # Check if system template
        if db_template.is_system:
            raise BadRequestError("Cannot delete system template")
        
        # Delete template
        self.db.delete(db_template)
        self.db.commit()
        
        logger.info(f"Deleted template: {template_id}")
        
        return True
    
    def set_active_template(self, template_id: str, user_id: str) -> bool:
        """
        Set a template as active for a user
        
        Args:
            template_id: Template ID
            user_id: User ID
            
        Returns:
            bool: True if successful, False if template not found
        """
        # Check if template exists
        template = self.get_template(template_id)
        if not template:
            return False
        
        # Get user preference or create new
        user_pref = self.db.query(UserPreference).filter(
            UserPreference.user_id == user_id
        ).first()
        
        if not user_pref:
            user_pref = UserPreference(
                user_id=user_id,
                preferences={"active_template_id": template_id}
            )
            self.db.add(user_pref)
        else:
            # Update preferences
            preferences = user_pref.preferences or {}
            preferences["active_template_id"] = template_id
            user_pref.preferences = preferences
        
        self.db.commit()
        
        logger.info(f"Set active template for user {user_id}: {template_id}")
        
        return True
    
    def format_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a template with variables
        
        Args:
            template_id: Template ID
            variables: Dictionary of variables
            
        Returns:
            str: Formatted template
            
        Raises:
            NotFoundError: If template not found
        """
        # Get template
        template = self.get_template(template_id)
        if not template:
            # Try default template
            template = self.get_template("default")
            if not template:
                raise NotFoundError(f"Template not found: {template_id}")
        
        # Increment usage count
        template.update_usage_count(db=self.db, template_id=template_id)
        
        # Format template
        try:
            # Prepare variables
            for var in template.input_variables:
                if var not in variables:
                    variables[var] = f"[{var} not provided]"
            
            # Use string formatting
            return template.template_content.format(**variables)
        
        except KeyError as e:
            logger.warning(f"Missing variable in template: {e}")
            return template.template_content
        
        except Exception as e:
            logger.exception(f"Error formatting template: {e}")
            return template.template_content
    
    def _extract_variables(self, template_content: str) -> List[str]:
        """
        Extract variables from template content
        
        Args:
            template_content: Template content
            
        Returns:
            List[str]: List of variable names
        """
        variables = []
        
        # Simple regex for {variable} pattern
        pattern = r'\{([^{}]+)\}'
        matches = re.findall(pattern, template_content)
        
        for match in matches:
            if match not in variables:
                variables.append(match)
        
        return variables
    
    def _generate_template_id(self, name: str) -> str:
        """
        Generate a template ID from name
        
        Args:
            name: Template name
            
        Returns:
            str: Template ID
        """
        # Convert to lowercase and replace spaces with underscores
        base_id = name.lower().replace(' ', '_')
        
        # Remove special characters
        base_id = re.sub(r'[^a-z0-9_]', '', base_id)
        
        # Check if ID already exists
        existing = self.get_template(base_id)
        if not existing:
            return base_id
        
        # Append number to make unique
        i = 1
        while True:
            new_id = f"{base_id}_{i}"
            existing = self.get_template(new_id)
            if not existing:
                return new_id
            i += 1