from typing import Dict, List, Optional, Any, Union
import logging

import streamlit as st
from core.settings import settings
from rag.base_vector_store import BaseVectorStore
from rag.vector_store_factory import VectorStoreFactory
from rag.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Service for interacting with vector stores.
    This provides a high-level API for working with vector stores.
    """

    def __init__(
        self,
        chapter_mode: bool = False,
        **kwargs
    ):
        """
        Initialize the vector store service.

        Args:
            embedding_model: The embedding model to use.
            collection_name: Name of the collection (defaults to settings).
            chapter_mode: Whether to store chapter information.
            **kwargs: Additional provider-specific parameters.
        """
        self.chapter_mode = chapter_mode
        
        # Create embedding service
        self.embedding_service = EmbeddingService()
        
        # Create vector store
        self.vector_store = VectorStoreFactory.create_vector_store(
            **kwargs
        )
        
        logger.info(f"Initialized VectorStoreService with {self.vector_store.__class__.__name__}")

    def add_texts(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        chapter: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Add texts to the vector store.

        Args:
            texts: List of text documents to add.
            metadata: Optional metadata for each text.
            chapter: Optional chapter name (if chapter_mode is True).
            **kwargs: Additional parameters.

        Returns:
            List of IDs for the added texts.
        """
        if not texts:
            logger.warning("No texts provided to add to vector store.")
            return []
            
        # Handle chapter mode
        if self.chapter_mode and chapter is not None:
            if metadata is None:
                metadata = [{"chapter": chapter} for _ in texts]
            else:
                for data in metadata:
                    data["chapter"] = chapter
                    
        elif metadata is None:
            metadata = [{} for _ in texts]
            
        try:
            # Generate embeddings
            embeddings = self.embedding_service.generate(texts)
            
            # Add to vector store
            ids = self.vector_store.add_texts(
                texts=texts,
                embeddings=embeddings.tolist(),
                metadatas=metadata,
                **kwargs
            )
            
            logger.info(f"Added {len(texts)} texts to vector store")
            return ids
            
        except Exception as e:
            logger.exception(f"Error adding texts to vector store: {e}")
            st.toast(f"Failed to add texts to vector store: {e}")
            return []

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents in the vector store.

        Args:
            query: The query text.
            top_k: Number of results to return.
            filter: Optional filter to apply to the search.
            **kwargs: Additional parameters.

        Returns:
            List of dictionaries containing found documents and their metadata.
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate(query)
            
            # Search vector store
            results = self.vector_store.search(
                query_embedding=query_embedding[0].tolist(),
                top_k=top_k,
                filter=filter,
                **kwargs
            )
            
            # Format results for consistency with the original implementation
            formatted_results = []
            for item in results:
                formatted_item = {
                    "text": item["text"],
                }
                
                # Add metadata
                if "metadata" in item and item["metadata"]:
                    for key, value in item["metadata"].items():
                        formatted_item[key] = value
                
                formatted_results.append(formatted_item)
                
            logger.info(f"Found {len(formatted_results)} results for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.exception(f"Error searching vector store: {e}")
            st.toast(f"Search failed: {e}")
            return []

    def get_all_documents(
        self,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get all documents from the vector store, optionally filtered.

        Args:
            filter: Optional filter to apply.
            **kwargs: Additional parameters.

        Returns:
            Dictionary containing retrieved documents.
        """
        try:
            # Get documents from vector store
            results = self.vector_store.get(filter=filter, **kwargs)
            logger.info(f"Retrieved {len(results['documents'])} documents from vector store")
            return results
            
        except Exception as e:
            logger.exception(f"Error retrieving documents from vector store: {e}")
            st.toast(f"Failed to retrieve documents: {e}")
            return {"ids": [], "documents": [], "metadatas": []}

    def clear_all(self) -> bool:
        """
        Clear all data from the vector store.

        Returns:
            True if successful, False otherwise.
        """
        try:
            result = self.vector_store.clear_collection()
            if result:
                logger.info("Successfully cleared vector store")
            else:
                logger.warning("Failed to clear vector store")
            return result
            
        except Exception as e:
            logger.exception(f"Error clearing vector store: {e}")
            st.toast(f"Failed to clear vector store: {e}")
            return False