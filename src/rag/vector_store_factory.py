import logging
from typing import Optional

import streamlit as st

from core.settings import settings
from rag.base_vector_store import BaseVectorStore
from rag.chroma_vector_store import ChromaVectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Factory for creating vector store instances."""

    @staticmethod
    def create_vector_store(
        provider: Optional[str] = None, **kwargs
    ) -> BaseVectorStore:
        """
        Create a vector store instance based on the provider.

        Args:
            embedding_model: The embedding model to use.
            collection_name: Name of the collection (defaults to settings).
            provider: Vector store provider (defaults to settings).
            **kwargs: Additional provider-specific parameters.

        Returns:
            An instance of a BaseVectorStore implementation.
        """
        # Use provided values or defaults from settings
        vector_store_provider = settings.vector_store_provider
        vector_store_collection = settings.vector_store_knowledge_collection

        # Create vector store based on provider
        if vector_store_provider.lower() == "qdrant":
            try:
                # Future implementation for Qdrant
                logger.info("Qdrant support is not yet implemented. ")
                st.warning(f"{vector_store_provider.lower()} not implemented")
            except ImportError:
                logger.warning("Qdrant package not found. ")

        elif vector_store_provider.lower() == "pinecone":
            try:
                # Future implementation for Pinecone
                logger.info("Pinecone support is not yet implemented. ")
                st.warning(f"{vector_store_provider.lower()} not implemented")
            except ImportError:
                logger.warning("Pinecone package not found. ")

        elif vector_store_provider.lower() == "weaviate":
            try:
                # Future implementation for Weaviate
                logger.info("Weaviate support is not yet implemented. ")
                st.warning(f"{vector_store_provider.lower()} not implemented")

            except ImportError:
                logger.warning("Weaviate package not found. ")

        elif vector_store_provider.lower() == "astradb":
            try:
                # Future implementation for Weaviate
                logger.info("astradb support is not yet implemented. ")
                st.warning(f"{vector_store_provider.lower()} not implemented")

            except ImportError:
                logger.warning("astradb package not found. ")

        elif vector_store_provider.lower() == "chroma":
            # Default to ChromaDB
            return ChromaVectorStore(collection_name=vector_store_collection, **kwargs)
