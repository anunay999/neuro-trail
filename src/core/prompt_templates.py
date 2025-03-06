import json
import logging
import os
from typing import Any, Dict, List, Optional

import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """
    Manages prompt templates with LangChain compatibility and persistence.
    """

    def __init__(self, storage_path: Optional[str] = "./.data/prompt_templates"):
        """
        Initialize the prompt template manager.

        Args:
            storage_path: Path to store prompt templates
        """
        self.storage_path = storage_path
        self._ensure_session_state_initialized()

    def _ensure_session_state_initialized(self):
        """
        Ensure session state is initialized with prompt templates.
        This method should be called on every page load.
        """
        # Initialize prompt templates if not exists
        if "prompt_templates" not in st.session_state:
            st.session_state["prompt_templates"] = {}

        # Initialize active template if not exists
        if "active_template" not in st.session_state:
            st.session_state["active_template"] = "default"

        # Ensure storage directory exists
        if self.storage_path:
            os.makedirs(self.storage_path, exist_ok=True)

        # Load templates only if they are empty
        if not st.session_state["prompt_templates"]:
            self._load_default_templates()
            self._load_saved_templates()

    def _load_default_templates(self):
        """Load default prompt templates."""
        default_templates = {
            "default": {
                "name": "Default",
                "description": "Standard balanced response",
                "template": """
                You are a helpful assistant for the Neuro Trail learning platform.
                Answer the following question based on the provided context.
                If the context doesn't contain relevant information, say so.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
                "system": True,  # System template, cannot be deleted
            },
            "friendly": {
                "name": "Friendly",
                "description": "Warm, conversational responses",
                "template": """
                You are a friendly and supportive learning assistant for Neuro Trail.
                Your tone is warm, encouraging, and conversational.
                Answer the following question in a friendly manner, using simple language and relatable examples.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
                "system": True,
            },
            "academic": {
                "name": "Academic",
                "description": "Formal, scholarly responses",
                "template": """
                You are an academic expert for the Neuro Trail learning platform.
                Your tone is formal, precise, and scholarly.
                Provide a well-structured response with references to academic concepts where relevant.
                Use proper terminology and maintain an educational tone throughout.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
                "system": True,
            },
            "concise": {
                "name": "Concise",
                "description": "Brief, to-the-point responses",
                "template": """
                You are a concise assistant for the Neuro Trail learning platform.
                Keep your response brief and to the point.
                Focus only on the most essential information and avoid unnecessary elaboration.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
                "system": True,
            },
            "socratic": {
                "name": "Socratic",
                "description": "Questions that prompt deeper thinking",
                "template": """
                You are a Socratic teaching assistant for the Neuro Trail learning platform.
                Instead of providing direct answers, guide the user to discover insights through thoughtful questions.
                Begin with a brief orientation to the topic, then pose 2-3 thought-provoking questions
                that will help the user reach their own understanding.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
                "system": True,
            },
            "beginner": {
                "name": "Beginner-Friendly",
                "description": "Simple explanations for newcomers",
                "template": """
                You are a beginner-friendly assistant for the Neuro Trail learning platform.
                Explain concepts as if to someone with no prior knowledge of the subject.
                Use simple language, avoid jargon, and include basic examples.
                Break down complex ideas into easy-to-understand parts.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
                "system": True,
            },
            "expert": {
                "name": "Expert",
                "description": "Advanced, technical responses",
                "template": """
                You are an expert-level assistant for the Neuro Trail learning platform.
                Provide detailed, technical responses assuming advanced knowledge of the subject.
                Include nuanced analysis, technical terminology, and sophisticated concepts.
                Do not oversimplify or explain basic concepts unless specifically asked.
                
                Context: {context}
                
                Question: {question}
                """,
                "input_variables": ["context", "question"],
                "system": True,
            },
        }

        # Add default templates to session state if they don't exist
        for template_id, template in default_templates.items():
            if template_id not in st.session_state["prompt_templates"]:
                st.session_state["prompt_templates"][template_id] = template

    def _load_saved_templates(self):
        """Load saved prompt templates from disk."""
        if not self.storage_path:
            return

        try:
            template_file = os.path.join(self.storage_path, "user_templates.json")
            if os.path.exists(template_file):
                with open(template_file, "r") as f:
                    user_templates = json.load(f)

                    # Add user templates to session state
                    for template_id, template in user_templates.items():
                        # Skip system templates (they're already loaded)
                        if not template.get("system", False):
                            st.session_state["prompt_templates"][template_id] = template

                logger.info(f"Loaded {len(user_templates)} user templates from disk")
            else:
                logger.info("No saved templates found")
        except Exception as e:
            logger.exception(f"Error loading saved templates: {e}")

    def save_templates(self):
        """Save prompt templates to disk."""
        if not self.storage_path:
            return

        try:
            # Only save user-created templates (not system ones)
            user_templates = {
                template_id: template
                for template_id, template in st.session_state[
                    "prompt_templates"
                ].items()
                if not template.get("system", False)
            }

            template_file = os.path.join(self.storage_path, "user_templates.json")
            with open(template_file, "w") as f:
                json.dump(user_templates, f, indent=2)

            logger.info(f"Saved {len(user_templates)} user templates to disk")
            return True
        except Exception as e:
            logger.exception(f"Error saving templates: {e}")
            return False

    def create_template(
        self, name: str, description: str, template: str, input_variables: List[str]
    ) -> Optional[str]:
        """
        Create a new prompt template.

        Args:
            name: Name of the template
            description: Description of the template
            template: Template string with variables in {variable} format
            input_variables: List of variable names used in the template

        Returns:
            Template ID if successful, None if failed
        """
        # Generate a template ID from the name
        template_id = name.lower().replace(" ", "_")

        # Check if template ID already exists
        if template_id in st.session_state["prompt_templates"]:
            # Append a number to make it unique
            i = 1
            while f"{template_id}_{i}" in st.session_state["prompt_templates"]:
                i += 1
            template_id = f"{template_id}_{i}"

        # Create the template
        st.session_state["prompt_templates"][template_id] = {
            "name": name,
            "description": description,
            "template": template,
            "input_variables": input_variables,
            "system": False,  # User template, can be deleted
        }

        # Save to disk
        self.save_templates()

        logger.info(f"Created new template: {template_id}")
        return template_id

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template: Optional[str] = None,
        input_variables: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an existing prompt template.

        Args:
            template_id: ID of the template to update
            name: New name for the template
            description: New description for the template
            template: New template string
            input_variables: New list of input variables

        Returns:
            True if successful, False if failed
        """
        # Check if template exists
        if template_id not in st.session_state["prompt_templates"]:
            logger.warning(f"Template {template_id} not found")
            return False

        # Check if it's a system template (cannot be updated)
        if st.session_state["prompt_templates"][template_id].get("system", False):
            logger.warning(f"Cannot update system template: {template_id}")
            return False

        # Update template fields
        if name is not None:
            st.session_state["prompt_templates"][template_id]["name"] = name

        if description is not None:
            st.session_state["prompt_templates"][template_id]["description"] = (
                description
            )

        if template is not None:
            st.session_state["prompt_templates"][template_id]["template"] = template

        if input_variables is not None:
            st.session_state["prompt_templates"][template_id]["input_variables"] = (
                input_variables
            )

        # Save to disk
        self.save_templates()

        logger.info(f"Updated template: {template_id}")
        return True

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a prompt template.

        Args:
            template_id: ID of the template to delete

        Returns:
            True if successful, False if failed
        """
        # Check if template exists
        if template_id not in st.session_state["prompt_templates"]:
            logger.warning(f"Template {template_id} not found")
            return False

        # Check if it's a system template (cannot be deleted)
        if st.session_state["prompt_templates"][template_id].get("system", False):
            logger.warning(f"Cannot delete system template: {template_id}")
            return False

        # If it's the active template, reset to default
        if st.session_state["active_template"] == template_id:
            st.session_state["active_template"] = "default"

        # Delete the template
        del st.session_state["prompt_templates"][template_id]

        # Save to disk
        self.save_templates()

        logger.info(f"Deleted template: {template_id}")
        return True

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a prompt template by ID.

        Args:
            template_id: ID of the template to get

        Returns:
            Template dictionary or None if not found
        """
        return st.session_state["prompt_templates"].get(template_id)

    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all prompt templates.

        Returns:
            Dictionary of template IDs to template dictionaries
        """
        return st.session_state["prompt_templates"]

    def set_active_template(self, template_id: str) -> bool:
        """
        Set the active template.

        Args:
            template_id: ID of the template to set as active

        Returns:
            True if successful, False if failed
        """
        if template_id not in st.session_state["prompt_templates"]:
            logger.warning(f"Template {template_id} not found")
            return False

        st.session_state["active_template"] = template_id
        logger.info(f"Set active template to: {template_id}")
        return True

    def get_active_template_id(self) -> str:
        """
        Get the active template ID.

        Returns:
            ID of the active template
        """
        return st.session_state.get("active_template", "default")

    def format_prompt(self, **kwargs) -> str:
        """
        Format the active prompt template with the provided variables.

        Args:
            **kwargs: Variables to use in formatting the template

        Returns:
            Formatted prompt string
        """
        template_id = self.get_active_template_id()
        template = self.get_template(template_id)

        if not template:
            logger.warning(f"Active template {template_id} not found, using default")
            template = self.get_template("default")

        try:
            # Check if all required variables are provided
            for var in template["input_variables"]:
                if var not in kwargs:
                    logger.warning(f"Missing required variable: {var}")
                    kwargs[var] = f"[{var} not provided]"

            # Format the template
            return template["template"].format(**kwargs)
        except Exception as e:
            logger.exception(f"Error formatting prompt: {e}")
            return f"Error formatting prompt: {str(e)}"


# Modify the singleton initialization
def initialize_prompt_template_manager():
    """
    Function to initialize the prompt template manager.
    This should be called at the start of your Streamlit app.
    """
    if "prompt_template_manager" not in st.session_state:
        st.session_state["prompt_template_manager"] = PromptTemplateManager()

    return st.session_state["prompt_template_manager"]


# Initialize the prompt template manager
prompt_template_manager = initialize_prompt_template_manager()
