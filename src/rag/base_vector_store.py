from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import logging

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """
    Abstract Base Class for Vector Stores.
    Implement this class to create a new vector store provider.
    """

    def __init__(
        self,
        collection_name: str,
        dimension: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize the base vector store.

        Args:
            collection_name: Collection name for the vector store.
            dimension: Dimension of the embedding vectors (if known).
            **kwargs: Additional provider-specific parameters.
        """
        self.collection_name = collection_name
        self.dimension = dimension
        logger.info(f"Initializing {self.__class__.__name__} with collection '{collection_name}'")

    @abstractmethod
    def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """
        Add texts and their embeddings to the vector store.

        Args:
            texts: List of text documents to add.
            embeddings: List of embedding vectors for each text.
            metadatas: Optional metadata for each text.
            ids: Optional IDs for each text.
            **kwargs: Additional provider-specific parameters.

        Returns:
            List of IDs for the added texts.
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents based on a query embedding.

        Args:
            query_embedding: Embedding vector of the query.
            top_k: Number of results to return.
            filter: Optional filter to apply to the search.
            **kwargs: Additional provider-specific parameters.

        Returns:
            List of dictionaries containing found documents and their metadata.
        """
        pass

    @abstractmethod
    def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        Delete documents from the vector store.

        Args:
            ids: Optional list of IDs to delete.
            filter: Optional filter to apply to deletion.
            **kwargs: Additional provider-specific parameters.

        Returns:
            True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get documents from the vector store.

        Args:
            ids: Optional list of IDs to get.
            filter: Optional filter to apply to get operation.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Dictionary containing the retrieved documents and their metadata.
        """
        pass

    @abstractmethod
    def clear_collection(self) -> bool:
        """
        Clear the entire collection.

        Returns:
            True if clearing was successful, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def count(self) -> int:
        """
        Get the count of documents in the collection.

        Returns:
            Number of documents in the collection.
        """
        pass