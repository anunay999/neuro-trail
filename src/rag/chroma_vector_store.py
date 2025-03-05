import os
from typing import Dict, List, Optional, Any
import logging

import streamlit as st
import numpy as np
from chromadb import PersistentClient

from core.settings import settings
from rag.base_vector_store import BaseVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB implementation of the BaseVectorStore."""

    def __init__(
        self,
        collection_name: str,
        dimension: Optional[int] = None,
        persist_directory: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the ChromaDB vector store.

        Args:
            collection_name: Name of the collection in ChromaDB.
            dimension: Dimension of the embedding vectors (if known).
            persist_directory: Directory to persist ChromaDB data.
            **kwargs: Additional kwargs passed to the base class.
        """
        super().__init__(collection_name, **kwargs)
        
        # Set persistence directory
        self.persist_dir = persist_directory or os.path.join(".data", "chromadb")
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self._initialize_chromadb()
        
        self.index = None

    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            logger.info(f"Initializing ChromaDB with persistence directory: {self.persist_dir}")
            self.client = PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.info(f"ChromaDB collection '{self.collection_name}' initialized")
        except Exception as e:
            logger.exception(f"Error initializing ChromaDB: {e}")
            st.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """Add texts and their embeddings to ChromaDB."""
        if not texts:
            logger.warning("No texts provided to add to ChromaDB")
            return []
            
        # Generate IDs if not provided
        if ids is None:
            ids = [str(self.count + i) for i in range(len(texts))]
            
        # Ensure metadatas is properly formatted
        if metadatas is None:
            metadatas = [{} for _ in texts]
            
        try:
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(texts)} texts to ChromaDB collection '{self.collection_name}'")
                
            return ids
        except Exception as e:
            logger.exception(f"Error adding texts to ChromaDB: {e}")
            st.error(f"Failed to add texts to vector store: {e}")
            return []

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search for similar documents in ChromaDB."""
        # Prepare query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k * 3, self.count)  # Get more results for refinement
        }
        
        # Add filter if provided
        if filter:
            query_params["where"] = filter
            
        try:
            # Query ChromaDB
            results = self.collection.query(**query_params)
            
            if not results["ids"][0]:  # Handle empty results
                logger.info("No results found in ChromaDB")
                return []
                
            formatted_results = []
            for i in range(min(top_k, len(results["ids"][0]))):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": float(results["distances"][0][i]) if results["distances"] else 0.0
                })
                
            return formatted_results
            
        except Exception as e:
            logger.exception(f"Error searching ChromaDB: {e}")
            st.error(f"Search failed: {e}")
            return []

    def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """Delete documents from ChromaDB."""
        try:
            if ids:
                self.collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents by ID from ChromaDB")
            elif filter:
                self.collection.delete(where=filter)
                logger.info(f"Deleted documents with filter {filter} from ChromaDB")
            else:
                logger.warning("No IDs or filter provided for deletion")
                return False
                
            return True
        except Exception as e:
            logger.exception(f"Error deleting from ChromaDB: {e}")
            st.error(f"Deletion failed: {e}")
            return False

    def get(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get documents from ChromaDB."""
        try:
            params = {"include": ["documents", "metadatas", "embeddings"]}
            
            if ids:
                params["ids"] = ids
            elif filter:
                params["where"] = filter
                
            result = self.collection.get(**params)
            
            # Return in a standardized format
            return {
                "ids": result["ids"],
                "documents": result["documents"],
                "metadatas": result["metadatas"],
                "embeddings": result["embeddings"] if "embeddings" in result else None
            }
        except Exception as e:
            logger.exception(f"Error getting documents from ChromaDB: {e}")
            st.error(f"Failed to retrieve documents: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    def clear_collection(self) -> bool:
        """Clear the entire ChromaDB collection."""
        try:
            # Delete the collection
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted ChromaDB collection '{self.collection_name}'")
            
            # Recreate the collection
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            logger.info(f"Recreated ChromaDB collection '{self.collection_name}'")
                
            return True
        except Exception as e:
            logger.exception(f"Error clearing ChromaDB collection: {e}")
            st.error(f"Failed to clear collection: {e}")
            return False

    @property
    def count(self) -> int:
        """Get the count of documents in the ChromaDB collection."""
        try:
            return self.collection.count()
        except Exception as e:
            logger.exception(f"Error getting count from ChromaDB: {e}")
            return 0