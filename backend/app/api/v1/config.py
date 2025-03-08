from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from app.db.session import get_db
from app.services.config_service import ConfigService
from app.schemas.config import (
    LLMConfig, EmbeddingConfig, VectorStoreConfig, 
    KnowledgeGraphConfig, ConfigResponse
)

router = APIRouter()

@router.get("/", response_model=ConfigResponse)
async def get_config(
    db: Session = Depends(get_db)
):
    """Get all configuration settings"""
    config_service = ConfigService(db)
    config = config_service.get_config()
    return config

@router.put("/llm", response_model=LLMConfig)
async def update_llm_config(
    config: LLMConfig,
    db: Session = Depends(get_db)
):
    """Update LLM configuration"""
    config_service = ConfigService(db)
    updated_config = config_service.update_llm_config(config)
    return updated_config

@router.put("/embedding", response_model=EmbeddingConfig)
async def update_embedding_config(
    config: EmbeddingConfig,
    db: Session = Depends(get_db)
):
    """Update embedding configuration"""
    config_service = ConfigService(db)
    updated_config = config_service.update_embedding_config(config)
    return updated_config

@router.put("/vector-store", response_model=VectorStoreConfig)
async def update_vector_store_config(
    config: VectorStoreConfig,
    db: Session = Depends(get_db)
):
    """Update vector store configuration"""
    config_service = ConfigService(db)
    updated_config = config_service.update_vector_store_config(config)
    return updated_config

@router.put("/knowledge-graph", response_model=KnowledgeGraphConfig)
async def update_knowledge_graph_config(
    config: KnowledgeGraphConfig,
    db: Session = Depends(get_db)
):
    """Update knowledge graph configuration"""
    config_service = ConfigService(db)
    updated_config = config_service.update_knowledge_graph_config(config)
    return updated_config

@router.get("/providers", response_model=Dict[str, List[str]])
async def get_available_providers():
    """Get available providers for LLM, embeddings, vector stores, etc."""
    config_service = ConfigService()
    providers = config_service.get_available_providers()
    return providers