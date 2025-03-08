from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, ClassVar, Type
import logging

# Configure logging
logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """Base class for all plugins"""
    
    # Class variables
    plugin_type: ClassVar[str] = "base"
    plugin_name: ClassVar[str] = "base"
    plugin_version: ClassVar[str] = "0.1.0"
    plugin_description: ClassVar[str] = "Base plugin class"
    
    @classmethod
    def get_info(cls) -> Dict[str, str]:
        """Get plugin information"""
        return {
            "type": cls.plugin_type,
            "name": cls.plugin_name,
            "version": cls.plugin_version,
            "description": cls.plugin_description,
        }
    
    @abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """
        Initialize the plugin
        
        Args:
            **kwargs: Additional initialization parameters
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """
        Shutdown the plugin
        
        Returns:
            bool: True if shutdown successful, False otherwise
        """
        pass


class VectorStorePlugin(PluginBase):
    """Base class for vector store plugins"""
    
    plugin_type: ClassVar[str] = "vector_store"
    
    @abstractmethod
    async def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> List[str]:
        """
        Add texts to the vector store
        
        Args:
            texts: List of text documents to add
            metadatas: Optional metadata for each text
            **kwargs: Additional parameters
            
        Returns:
            List[str]: List of IDs for the added texts
        """
        pass
    
    @abstractmethod
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
            **kwargs: Additional parameters
            
        Returns:
            List[Dict[str, Any]]: List of documents and their metadata
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        Delete documents from the vector store
        
        Args:
            ids: Optional list of IDs to delete
            filter: Optional filter to apply to deletion
            **kwargs: Additional parameters
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass


class LLMPlugin(PluginBase):
    """Base class for LLM plugins"""
    
    plugin_type: ClassVar[str] = "llm"
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Generate text using the LLM
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            str: Generated text
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ):
        """
        Stream generated text from the LLM
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Yields:
            str: Chunks of generated text
        """
        pass


class EmbeddingPlugin(PluginBase):
    """Base class for embedding plugins"""
    
    plugin_type: ClassVar[str] = "embedding"
    
    @abstractmethod
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
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        pass
    
    @abstractmethod
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
            
        Returns:
            List[float]: Embedding vector
        """
        pass


class DocumentPlugin(PluginBase):
    """Base class for document handler plugins"""
    
    plugin_type: ClassVar[str] = "document_handler"
    
    @abstractmethod
    async def process_document(
        self,
        file_content: bytes,
        file_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a document
        
        Args:
            file_content: Binary content of the file
            file_name: Name of the file
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Processed document data
        """
        pass


class KnowledgeGraphPlugin(PluginBase):
    """Base class for knowledge graph plugins"""
    
    plugin_type: ClassVar[str] = "knowledge_graph"
    
    @abstractmethod
    async def add_book(
        self,
        title: str,
        author: str,
        **kwargs
    ) -> bool:
        """
        Add a book to the knowledge graph
        
        Args:
            title: Book title
            author: Book author
            **kwargs: Additional parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def add_chapters(
        self,
        book_title: str,
        chapters: List[Dict[str, Any]],
        **kwargs
    ) -> bool:
        """
        Add chapters to a book in the knowledge graph
        
        Args:
            book_title: Book title
            chapters: List of chapter dictionaries
            **kwargs: Additional parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass