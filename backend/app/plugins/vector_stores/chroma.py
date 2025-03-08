import logging
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.core.plugin_base import VectorStorePlugin
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStorePlugin):
    """Plugin for ChromaDB vector store"""
    
    plugin_type = "vector_store"
    plugin_name = "chroma"
    plugin_version = "0.1.0"
    plugin_description = "ChromaDB vector store"
    
    def __init__(self):
        """Initialize ChromaDB vector store plugin"""
        self.initialized = False
        self.client = None
        self.collection = None
        self.collection_name = settings.VECTOR_STORE_KNOWLEDGE_COLLECTION
        
    async def initialize(self, **kwargs) -> bool:
        """
        Initialize the plugin
        
        Args:
            **kwargs: Additional parameters
                - collection_name: Optional collection name override
                - persist_directory: Optional persistence directory
            
        Returns:
            bool: True if initialization successful
        """
        try:
            # Get settings from kwargs or use defaults
            if kwargs.get("collection_name"):
                self.collection_name = kwargs["collection_name"]
            
            persist_dir = kwargs.get("persist_directory") or os.path.join(".data", "chromadb")
            
            # Ensure persistence directory exists
            os.makedirs(persist_dir, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            
            self.initialized = True
            logger.info(f"ChromaDB vector store initialized with collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.exception(f"Error initializing ChromaDB vector store: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shutdown the plugin
        
        Returns:
            bool: True if shutdown successful
        """
        self.client = None
        self.collection = None
        self.initialized = False
        logger.info("ChromaDB vector store shutdown")
        return True
    
    async def add_texts(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """
        Add texts to the vector store
        
        Args:
            texts: List of text documents
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dictionaries
            ids: Optional list of IDs
            
        Returns:
            List[str]: List of added document IDs
        """
        if not self.initialized:
            logger.error("ChromaDB vector store not initialized")
            return []
        
        # Validate inputs
        if len(texts) != len(embeddings):
            raise ValueError("Number of texts and embeddings must match")
        
        if not texts:
            logger.warning("No texts provided to add to ChromaDB")
            return []
        
        # Generate IDs if not provided
        if ids is None:
            # Get current count and use as starting ID
            count = self.collection.count()
            ids = [str(count + i) for i in range(len(texts))]
        
        # Ensure metadatas is properly formatted
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        try:
            # Add to ChromaDB in batches of 100
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                end_idx = min(i + batch_size, len(texts))
                
                self.collection.add(
                    embeddings=embeddings[i:end_idx],
                    documents=texts[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )
            
            logger.info(f"Added {len(texts)} texts to ChromaDB collection '{self.collection_name}'")
            return ids
            
        except Exception as e:
            logger.exception(f"Error adding texts to ChromaDB: {e}")
            return []
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of results to return
            filter: Optional filter to apply to the search
            
        Returns:
            List[Dict[str, Any]]: List of documents and their metadata
        """
        if not self.initialized:
            logger.error("ChromaDB vector store not initialized")
            return []
        
        # Prepare query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k * 2, self.collection.count() or top_k * 2),  # Get more results for refinement
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
                    "score": float(results["distances"][0][i]) if results["distances"] else 0.0,
                    "document_id": results["metadatas"][0][i].get("document_id", "") if results["metadatas"] else ""
                })

            return formatted_results

        except Exception as e:
            logger.exception(f"Error searching ChromaDB: {e}")
            return []
    
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        Delete documents from vector store
        
        Args:
            ids: Optional list of IDs to delete
            filter: Optional filter to apply to deletion
            
        Returns:
            bool: True if deletion was successful
        """
        if not self.initialized:
            logger.error("ChromaDB vector store not initialized")
            return False
        
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
            return False
    
    async def get(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get documents from vector store
        
        Args:
            ids: Optional list of IDs to get
            filter: Optional filter to apply
            
        Returns:
            Dict[str, Any]: Dictionary containing the retrieved documents
        """
        if not self.initialized:
            logger.error("ChromaDB vector store not initialized")
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
        
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
                "embeddings": result["embeddings"] if "embeddings" in result else None,
            }
            
        except Exception as e:
            logger.exception(f"Error getting documents from ChromaDB: {e}")
            return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}
    
    async def clear_collection(self) -> bool:
        """
        Clear the entire collection
        
        Returns:
            bool: True if clearing was successful
        """
        if not self.initialized:
            logger.error("ChromaDB vector store not initialized")
            return False
        
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
            return False
    
    @property
    def count(self) -> int:
        """
        Get the count of documents in the collection
        
        Returns:
            int: Number of documents in the collection
        """
        if not self.initialized:
            logger.error("ChromaDB vector store not initialized")
            return 0
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.exception(f"Error getting count from ChromaDB: {e}")
            return 0