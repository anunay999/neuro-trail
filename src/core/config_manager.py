import logging
import os

import streamlit as st

from core.settings_config import Settings, settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration in a user-friendly way with persistence."""

    def __init__(self):
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables if not already set."""
        logger.info("Initializing configuration session state.")

        if "config_initialized" not in st.session_state:
            # First-time setup flags
            st.session_state.config_initialized = False

            # Neo4j Configuration
            st.session_state.neo4j_uri = settings.neo4j_uri
            st.session_state.neo4j_user = settings.neo4j_user
            st.session_state.neo4j_password = settings.neo4j_password

            # Vector Store Configuration
            st.session_state.vector_store_provider = settings.vector_store_provider
            st.session_state.vector_store_host = settings.vector_store_host
            st.session_state.vector_store_port = settings.vector_store_port

            # LLM Configuration
            st.session_state.llm_provider = settings.llm_provider
            st.session_state.llm_model = settings.llm_model
            st.session_state.llm_temperature = settings.llm_temperature
            st.session_state.llm_max_tokens = settings.llm_max_tokens
            st.session_state.llm_base_url = settings.llm_base_url
            st.session_state.llm_api_key = settings.llm_api_key
            st.session_state.vector_store_embedding_provider_api_key = (
                settings.embedder_provider_api_key
            )

            # Embedder Configuration
            st.session_state.embedder_provider = settings.embedder_provider
            st.session_state.embedder_model = settings.embedder_model
            st.session_state.embedder_base_url = settings.embedder_base_url

            # For file upload & processing
            st.session_state.uploaded_files = []
            st.session_state.processing_status = None

            # For chat functionality
            st.session_state.chat_history = []

            # Check if required configs are present
            self._check_configuration_status()

    def _check_configuration_status(self):
        """Check if the necessary configurations are populated."""
        # Define essential config variables
        if st.session_state.llm_provider and st.session_state.llm_model:
            # Check API key for providers that need it
            if st.session_state.llm_provider.lower() in [
                "openai",
                "google",
                "gemini",
                "mistral",
                "huggingface",
            ]:
                if st.session_state.llm_api_key:
                    st.session_state.config_initialized = True
                else:
                    st.session_state.config_initialized = False
            else:
                # For Ollama, just check if base URL is set
                if st.session_state.llm_base_url:
                    st.session_state.config_initialized = True
                else:
                    st.session_state.config_initialized = False
        else:
            st.session_state.config_initialized = False

        logger.info(
            f"Configuration status: initialized={st.session_state.config_initialized}"
        )
        return st.session_state.config_initialized

    def is_configured(self):
        """Returns whether the app is properly configured."""
        return st.session_state.config_initialized

    def save_configuration(self):
        """Save the current configuration to the .env file."""
        try:
            # Update settings from session state
            updated_settings = Settings(
                # Neo4j Configuration
                neo4j_uri=st.session_state.neo4j_uri,
                neo4j_user=st.session_state.neo4j_user,
                neo4j_password=st.session_state.neo4j_password,
                # Vector Store Configuration
                vector_store_provider=st.session_state.vector_store_provider,
                vector_store_host=st.session_state.vector_store_host,
                vector_store_port=st.session_state.vector_store_port,
                # LLM Configuration
                llm_provider=st.session_state.llm_provider,
                llm_model=st.session_state.llm_model,
                llm_temperature=st.session_state.llm_temperature,
                llm_max_tokens=st.session_state.llm_max_tokens,
                llm_base_url=st.session_state.llm_base_url,
                llm_api_key=st.session_state.llm_api_key,
                # Embedder Configuration
                embedder_provider=st.session_state.embedder_provider,
                embedder_model=st.session_state.embedder_model,
                embedder_base_url=st.session_state.embedder_base_url,
            )

            # Save to .env file
            updated_settings.save_to_env()

            # Update global settings
            global settings
            settings = updated_settings

            # Update environment variables for immediate use
            self._update_env_vars()

            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.exception(f"Error saving configuration: {e}")
            return False

    def _update_env_vars(self):
        """Update environment variables for immediate use in current session."""
        # Set environment variables directly
        os.environ["NEO4J_URI"] = st.session_state.neo4j_uri
        os.environ["NEO4J_USER"] = st.session_state.neo4j_user
        os.environ["NEO4J_PASSWORD"] = st.session_state.neo4j_password

        # LLM Environment Variables
        os.environ["LLM_PROVIDER"] = st.session_state.llm_provider
        os.environ["LLM_MODEL"] = st.session_state.llm_model
        os.environ["LLM_BASE_URL"] = st.session_state.llm_base_url

        # Only set API key if it's not empty
        if st.session_state.llm_api_key:
            if st.session_state.llm_provider.lower() == "openai":
                os.environ["OPENAI_API_KEY"] = st.session_state.llm_api_key
            elif st.session_state.llm_provider.lower() in ["google", "gemini"]:
                os.environ["GEMINI_API_KEY"] = st.session_state.llm_api_key
            elif st.session_state.llm_provider.lower() == "mistral":
                os.environ["MISTRAL_API_KEY"] = st.session_state.llm_api_key
            elif st.session_state.llm_provider.lower() == "huggingface":
                os.environ["HUGGINGFACE_API_KEY"] = st.session_state.llm_api_key

        # Embedder Environment Variables
        os.environ["EMBEDDER_PROVIDER"] = st.session_state.embedder_provider
        os.environ["EMBEDDER_MODEL"] = st.session_state.embedder_model
        os.environ["EMBEDDER_BASE_URL"] = st.session_state.embedder_base_url

        # Only set API key if it's not empty
        if st.session_state.vector_store_embedding_provider_api_key:
            if st.session_state.llm_provider.lower() == "openai":
                os.environ["OPENAI_API_KEY"] = (
                    st.session_state.vector_store_embedding_provider_api_key
                )
            elif st.session_state.llm_provider.lower() in ["google", "gemini"]:
                os.environ["GEMINI_API_KEY"] = (
                    st.session_state.vector_store_embedding_provider_api_key
                )
            elif st.session_state.llm_provider.lower() == "mistral":
                os.environ["MISTRAL_API_KEY"] = (
                    st.session_state.vector_store_embedding_provider_api_key
                )
            elif st.session_state.llm_provider.lower() == "huggingface":
                os.environ["HUGGINGFACE_API_KEY"] = (
                    st.session_state.vector_store_embedding_provider_api_key
                )

        logger.info("Environment variables updated for current session")
