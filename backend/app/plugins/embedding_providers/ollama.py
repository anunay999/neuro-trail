import logging
import aiohttp
import json
from typing import List, Dict, Any, Optional

from app.core.plugin_base import EmbeddingPlugin
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class OllamaEmbedding(EmbeddingPlugin):
    """Plugin for Ollama embedding integration"""
    
    plugin_type = "embedding"
    plugin_name = "ollama"
    plugin_version = "0.1.0"
    plugin_description = "Ollama embedding provider"
    
    def __init__(self):
        """Initialize Ollama embedding plugin"""
        self.initialized = False
        self.base_url = settings.EMBEDDER_BASE_URL
        self.model = settings.EMBEDDER_MODEL
        
    async def initialize(self, **kwargs) -> bool:
        """
        Initialize the plugin
        
        Args:
            **kwargs: Additional parameters
                - base_url: Optional base URL override
                - model: Optional model name override
            
        Returns:
            bool: True if initialization successful
        """
        try:
            # Get settings from kwargs or use defaults
            self.base_url = kwargs.get("base_url") or self.base_url
            self.model = kwargs.get("model") or self.model
            
            # Check if base URL is valid
            if not self.base_url:
                logger.error("Ollama base URL not provided")
                return False
            
            # Check if model is valid
            if not self.model:
                logger.error("Ollama embedding model name not provided")
                return False
            
            # Check if Ollama is running
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        logger.error(f"Ollama service not available at {self.base_url}")
                        return False
            
            self.initialized = True
            logger.info(f"Ollama embedding initialized with model: {self.model}")
            return True
            
        except Exception as e:
            logger.exception(f"Error initializing Ollama embedding: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shutdown the plugin
        
        Returns:
            bool: True if shutdown successful
        """
        self.initialized = False
        logger.info("Ollama embedding shutdown")
        return True
    
    async def embed_documents(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for documents
        
        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters
                - model: Optional model override
                
        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not self.initialized:
            logger.error("Ollama embedding not initialized")
            raise RuntimeError("Ollama embedding not initialized. Please check if Ollama is running.")
        
        model = kwargs.get("model") or self.model
        
        # Generate embeddings for each text
        embeddings = []
        for text in texts:
            try:
                embedding = await self._get_embedding(text, model)
                embeddings.append(embedding)
            except Exception as e:
                logger.exception(f"Error embedding text with Ollama: {e}")
                # Use zero vector as fallback
                embeddings.append([0.0] * 768)  # Default dimension
        
        return embeddings
    
    async def embed_query(
        self,
        text: str,
        **kwargs
    ) -> List[float]:
        """
        Generate embedding for a query
        
        Args:
            text: Query text to embed
            **kwargs: Additional parameters
                - model: Optional model override
                
        Returns:
            List[float]: Embedding vector
        """
        if not self.initialized:
            logger.error("Ollama embedding not initialized")
            raise RuntimeError("Ollama embedding not initialized. Please check if Ollama is running.")
        
        model = kwargs.get("model") or self.model
        
        try:
            embedding = await self._get_embedding(text, model)
            return embedding
        except Exception as e:
            logger.exception(f"Error embedding query with Ollama: {e}")
            raise
    
    async def _get_embedding(self, text: str, model: str) -> List[float]:
        """
        Get embedding for a single text using Ollama API
        
        Args:
            text: Text to embed
            model: Model name
            
        Returns:
            List[float]: Embedding vector
        """
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": text,
            "options": {
                "embedding": True  # Request embeddings instead of text generation
            }
        }
        
        # Make request to Ollama API
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama API error: {error_text}")
                    raise RuntimeError(f"Ollama API returned status {response.status}: {error_text}")
                
                result = await response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise ValueError("Ollama did not return an embedding")
                
                return embedding