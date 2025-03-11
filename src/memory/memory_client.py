from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from mem0 import Memory
from pydantic import BaseModel, Field
from core.settings import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    USER = "user"
    KNOWLEDGE = "knowledge"


# Configuration models
class VectorStoreConfig(BaseModel):
    provider: str
    collection_name: str = Field(default="default")
    path: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class LLMConfig(BaseModel):
    model: str
    provider: str = "litellm"
    temperature: float = 0.0
    max_tokens: int = 2000
    api_key: Optional[str] = None


class EmbedderConfig(BaseModel):
    provider: str
    model: str
    api_key: Optional[str] = None


class GraphStoreConfig(BaseModel):
    provider: str
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class MemoryConfig(BaseModel):
    vector_store: Optional[VectorStoreConfig] = None
    llm: Optional[LLMConfig] = None
    embedder: Optional[EmbedderConfig] = None
    graph_store: Optional[GraphStoreConfig] = None


class AbstractMemoryClient(ABC):
    """
    Abstract base class for memory operations that can be extended for different memory types.
    """
    @abstractmethod
    def add(self, data: Union[str, List[Dict[str, str]]], user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """Add a memory for a user"""
        pass

    @abstractmethod
    def get(self, memory_id: str) -> Dict:
        """Get a specific memory by ID"""
        pass

    @abstractmethod
    def get_all(self, user_id: str) -> Dict:
        """Get all memories for a user"""
        pass

    @abstractmethod
    def search(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """Search for relevant memories"""
        pass

    @abstractmethod
    def update(self, memory_id: str, data: Union[str, List[Dict[str, str]]], metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """Update a memory"""
        pass

    @abstractmethod
    def delete(self, memory_id: str) -> Dict:
        """Delete a memory by ID"""
        pass

    @abstractmethod
    def delete_all(self, user_id: str) -> Dict:
        """Delete all memories for a user"""
        pass

    @abstractmethod
    def history(self, memory_id: str) -> Dict:
        """Get history of a memory"""
        pass


class CommonMemoryClient(AbstractMemoryClient):
    """
    Common implementation of memory operations using mem0 SDK.
    """

    def __init__(self, config: MemoryConfig):
        """Initialize the memory client with configuration."""
        self.config = config
        self._convert_config_to_mem0_format()
        logger.info(
            f"Initializing memory client with config: \n{self.mem0_config}")
        self.memory = Memory.from_config(config_dict=self.mem0_config)

    def _convert_config_to_mem0_format(self):
        """Convert our Pydantic models to the format expected by mem0."""
        self.mem0_config = {}

        if self.config.vector_store:
            self.mem0_config["vector_store"] = {
                "provider": self.config.vector_store.provider,
                "config": self.config.vector_store.dict(exclude={"provider"}, exclude_none=True)
            }

        if self.config.llm:
            self.mem0_config["llm"] = {
                "provider": self.config.llm.provider,
                "config": self.config.llm.dict(exclude={"provider"}, exclude_none=True)
            }

        if self.config.embedder:
            self.mem0_config["embedder"] = {
                "provider": self.config.embedder.provider,
                "config": self.config.embedder.dict(exclude={"provider"}, exclude_none=True)
            }

        if self.config.graph_store:
            self.mem0_config["graph_store"] = {
                "provider": self.config.graph_store.provider,
                "config": self.config.graph_store.dict(exclude={"provider"}, exclude_none=True)
            }

    def add(self, messages: Union[str, List[Dict[str, str]]], user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict:
        """Add a memory for a user."""
        return self.memory.add(messages, user_id=user_id, metadata=metadata or {})

    def get(self, memory_id: str) -> Dict:
        """Get a specific memory by ID."""
        return self.memory.get(memory_id)

    def get_all(self, user_id: str) -> Dict:
        """Get all memories for a user."""
        return self.memory.get_all(user_id=user_id)

    def search(self, query: str, user_id: str, limit: int = 5) -> Dict:
        """Search for relevant memories."""
        return self.memory.search(query, user_id=user_id, limit=limit)

    def update(self, memory_id: str, data: Union[str, List[Dict[str, str]]]) -> Dict:
        """Update a memory."""
        update_params = {"data": data}
        return self.memory.update(memory_id=memory_id, **update_params)

    def delete(self, memory_id: str) -> Dict:
        """Delete a memory by ID."""
        return self.memory.delete(memory_id=memory_id)

    def delete_all(self, user_id: str) -> Dict:
        """Delete all memories for a user."""
        return self.memory.delete_all(user_id=user_id)

    def history(self, memory_id: str) -> Dict:
        """Get history of a memory."""
        return self.memory.history(memory_id=memory_id)


def create_memory_client_from_settings() -> CommonMemoryClient:
    """Create a memory client from application settings."""
    vector_store_config = None
    if settings.vector_store_provider == "chroma":
        vector_store_config = VectorStoreConfig(
            provider=settings.vector_store_provider,
            collection_name=settings.vector_store_user_collection,
            port=settings.vector_store_port
        )
    elif settings.vector_store_provider == "pinecone":
        vector_store_config = VectorStoreConfig(
            provider=settings.vector_store_provider,
            collection_name=settings.vector_store_user_collection,
            api_key=settings.vector_store_api_key,
            environment=settings.vector_store_environment
        )
    elif settings.vector_store_provider == "weaviate":
        vector_store_config = VectorStoreConfig(
            provider=settings.vector_store_provider,
            collection_name=settings.vector_store_user_collection,
            url=settings.vector_store_url,
            auth=settings.vector_store_auth
        )

    elif settings.vector_store_provider == "qdrant":
        vector_store_config = VectorStoreConfig(
            provider=settings.vector_store_provider,
            collection_name=settings.vector_store_user_collection,
            url=settings.vector_store_url,
            auth=settings.vector_store_auth
        )

    embedder_config = EmbedderConfig(
        provider=settings.embedder_provider,
        model=settings.embedder_model,
        api_key=settings.embedder_provider_api_key if settings.embedder_provider_api_key else None
    )

    llm_config = LLMConfig(
        provider=settings.llm_provider,
        model=settings.llm_model,
        api_key=settings.llm_api_key if settings.llm_api_key else None
    )

    memory_config = MemoryConfig(
        vector_store=vector_store_config,
        llm=llm_config,
        embedder=embedder_config,
    )

    return CommonMemoryClient(memory_config)
