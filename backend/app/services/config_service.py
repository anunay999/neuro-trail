from fastapi import Depends
from sqlalchemy.orm import Session
import logging
from typing import Dict, List, Any, Optional
import os

from app.db.session import get_db
from app.models.config import Config
from app.schemas.config import (
    LLMConfig, EmbeddingConfig, VectorStoreConfig, 
    KnowledgeGraphConfig, ConfigResponse
)
from app.services.plugin_manager import plugin_manager
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class ConfigService:
    """Service for application configuration management"""
    
    def __init__(self, db: Session = None):
        """
        Initialize config service
        
        Args:
            db: Optional database session
        """
        self.db = db
    
    def get_config(self) -> ConfigResponse:
        """
        Get all configuration settings
        
        Returns:
            ConfigResponse: Configuration settings
        """
        # Create config response from settings
        llm_config = LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY
        )
        
        embedding_config = EmbeddingConfig(
            provider=settings.EMBEDDER_PROVIDER,
            model=settings.EMBEDDER_MODEL,
            base_url=settings.EMBEDDER_BASE_URL,
            api_key=settings.EMBEDDER_PROVIDER_API_KEY
        )
        
        vector_store_config = VectorStoreConfig(
            provider=settings.VECTOR_STORE_PROVIDER,
            host=settings.VECTOR_STORE_HOST,
            port=settings.VECTOR_STORE_PORT,
            collection_name=settings.VECTOR_STORE_KNOWLEDGE_COLLECTION,
            user_collection_name=settings.VECTOR_STORE_USER_COLLECTION
        )
        
        knowledge_graph_config = KnowledgeGraphConfig(
            provider="neo4j",  # Currently only neo4j is supported
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD
        )
        
        # Check if configuration is valid
        is_configured = (
            settings.LLM_PROVIDER 
            and settings.LLM_MODEL
            and settings.EMBEDDER_PROVIDER
            and settings.EMBEDDER_MODEL
        )
        
        return ConfigResponse(
            llm=llm_config,
            embedding=embedding_config,
            vector_store=vector_store_config,
            knowledge_graph=knowledge_graph_config,
            is_configured=is_configured
        )
    
    def update_llm_config(self, config: LLMConfig) -> LLMConfig:
        """
        Update LLM configuration
        
        Args:
            config: New LLM configuration
            
        Returns:
            LLMConfig: Updated configuration
        """
        # Update settings
        settings.LLM_PROVIDER = config.provider
        settings.LLM_MODEL = config.model
        settings.LLM_TEMPERATURE = config.temperature
        settings.LLM_MAX_TOKENS = config.max_tokens
        settings.LLM_BASE_URL = config.base_url
        
        # Only update API key if provided
        if config.api_key:
            settings.LLM_API_KEY = config.api_key
        
        # Save to .env file
        settings.save_to_env()
        
        # Update environment variables
        self._update_env_vars()
        
        logger.info("Updated LLM configuration")
        
        return config
    
    def update_embedding_config(self, config: EmbeddingConfig) -> EmbeddingConfig:
        """
        Update embedding configuration
        
        Args:
            config: New embedding configuration
            
        Returns:
            EmbeddingConfig: Updated configuration
        """
        # Update settings
        settings.EMBEDDER_PROVIDER = config.provider
        settings.EMBEDDER_MODEL = config.model
        settings.EMBEDDER_BASE_URL = config.base_url
        
        # Only update API key if provided
        if config.api_key:
            settings.EMBEDDER_PROVIDER_API_KEY = config.api_key
        
        # Save to .env file
        settings.save_to_env()
        
        # Update environment variables
        self._update_env_vars()
        
        logger.info("Updated embedding configuration")
        
        return config
    
    def update_vector_store_config(self, config: VectorStoreConfig) -> VectorStoreConfig:
        """
        Update vector store configuration
        
        Args:
            config: New vector store configuration
            
        Returns:
            VectorStoreConfig: Updated configuration
        """
        # Update settings
        settings.VECTOR_STORE_PROVIDER = config.provider
        settings.VECTOR_STORE_HOST = config.host
        settings.VECTOR_STORE_PORT = config.port
        settings.VECTOR_STORE_KNOWLEDGE_COLLECTION = config.collection_name
        settings.VECTOR_STORE_USER_COLLECTION = config.user_collection_name
        
        # Save to .env file
        settings.save_to_env()
        
        # Update environment variables
        self._update_env_vars()
        
        logger.info("Updated vector store configuration")
        
        return config
    
    def update_knowledge_graph_config(self, config: KnowledgeGraphConfig) -> KnowledgeGraphConfig:
        """
        Update knowledge graph configuration
        
        Args:
            config: New knowledge graph configuration
            
        Returns:
            KnowledgeGraphConfig: Updated configuration
        """
        # Update settings
        settings.NEO4J_URI = config.uri
        settings.NEO4J_USER = config.user
        
        # Only update password if provided
        if config.password:
            settings.NEO4J_PASSWORD = config.password
        
        # Save to .env file
        settings.save_to_env()
        
        # Update environment variables
        self._update_env_vars()
        
        logger.info("Updated knowledge graph configuration")
        
        return config
    
    def get_available_providers(self) -> Dict[str, List[str]]:
        """
        Get available providers for LLM, embeddings, vector stores, etc.
        
        Returns:
            Dict[str, List[str]]: Dictionary of provider types to lists of provider names
        """
        
        # Map plugin types to provider types
        provider_map = {
            "llm": ["ollama", "openai", "google", "mistral", "huggingface"],
            "embedding": ["ollama", "openai", "google", "mistral", "huggingface", "jina_ai"],
            "vector_store": ["qdrant", "chroma", "pinecone", "weaviate"],
            "knowledge_graph": ["neo4j"]
        }
        
        return provider_map
    
    def _update_env_vars(self) -> None:
        """Update environment variables for immediate use in current session"""
        # Set environment variables directly
        os.environ["NEO4J_URI"] = settings.NEO4J_URI
        os.environ["NEO4J_USER"] = settings.NEO4J_USER
        os.environ["NEO4J_PASSWORD"] = settings.NEO4J_PASSWORD
        
        os.environ["VECTOR_STORE_PROVIDER"] = settings.VECTOR_STORE_PROVIDER
        os.environ["VECTOR_STORE_HOST"] = settings.VECTOR_STORE_HOST
        os.environ["VECTOR_STORE_PORT"] = str(settings.VECTOR_STORE_PORT)
        
        os.environ["LLM_PROVIDER"] = settings.LLM_PROVIDER
        os.environ["LLM_MODEL"] = settings.LLM_MODEL
        os.environ["LLM_TEMPERATURE"] = str(settings.LLM_TEMPERATURE)
        os.environ["LLM_MAX_TOKENS"] = str(settings.LLM_MAX_TOKENS)
        os.environ["LLM_BASE_URL"] = settings.LLM_BASE_URL
        
        if settings.LLM_API_KEY:
            os.environ["LLM_API_KEY"] = settings.LLM_API_KEY
        
        os.environ["EMBEDDER_PROVIDER"] = settings.EMBEDDER_PROVIDER
        os.environ["EMBEDDER_MODEL"] = settings.EMBEDDER_MODEL
        os.environ["EMBEDDER_BASE_URL"] = settings.EMBEDDER_BASE_URL
        
        if settings.EMBEDDER_PROVIDER_API_KEY:
            os.environ["EMBEDDER_PROVIDER_API_KEY"] = settings.EMBEDDER_PROVIDER_API_KEY
        
        logger.info("Updated environment variables for current session")