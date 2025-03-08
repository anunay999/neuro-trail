from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from app.schemas.base import TimestampMixin


class LLMProvider(str, Enum):
    """LLM provider enum"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GOOGLE = "google"
    MISTRAL = "mistral"
    HUGGINGFACE = "huggingface"


class EmbeddingProvider(str, Enum):
    """Embedding provider enum"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    GOOGLE = "google"
    MISTRAL = "mistral"
    HUGGINGFACE = "huggingface"
    JINA_AI = "jina_ai"


class VectorStoreProvider(str, Enum):
    """Vector store provider enum"""
    QDRANT = "qdrant"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"


class GraphProvider(str, Enum):
    """Knowledge graph provider enum"""
    NEO4J = "neo4j"


class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: LLMProvider
    model: str
    temperature: float = 0.0
    max_tokens: int = 2000
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    other_params: Optional[Dict[str, Any]] = None


class EmbeddingConfig(BaseModel):
    """Embedding configuration"""
    provider: EmbeddingProvider
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    other_params: Optional[Dict[str, Any]] = None


class VectorStoreConfig(BaseModel):
    """Vector store configuration"""
    provider: VectorStoreProvider
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "knowledge"
    user_collection_name: str = "user"
    api_key: Optional[str] = None
    other_params: Optional[Dict[str, Any]] = None


class KnowledgeGraphConfig(BaseModel):
    """Knowledge graph configuration"""
    provider: GraphProvider = GraphProvider.NEO4J
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    other_params: Optional[Dict[str, Any]] = None


class ConfigResponse(BaseModel):
    """Configuration response"""
    llm: LLMConfig
    embedding: EmbeddingConfig
    vector_store: VectorStoreConfig
    knowledge_graph: KnowledgeGraphConfig
    is_configured: bool = False