# Import all plugin modules to ensure they're registered
from app.plugins.document_handlers import EPUBHandler, PDFHandler, DOCXHandler
from app.plugins.vector_stores import ChromaVectorStore
from app.plugins.llm_providers import OllamaLLM
from app.plugins.embedding_providers import OllamaEmbedding
from app.plugins.knowledge_graphs import Neo4jDocumentGraph

# List of all available plugins
available_plugins = {
    "document_handler": {
        "epub_handler": EPUBHandler,
        "pdf_handler": PDFHandler,
        "docx_handler": DOCXHandler
    },
    "vector_store": {
        "chroma": ChromaVectorStore
    },
    "llm": {
        "ollama": OllamaLLM
    },
    "embedding": {
        "ollama": OllamaEmbedding
    },
    "knowledge_graph": {
        "neo4j": Neo4jDocumentGraph
    }
}

__all__ = [
    "EPUBHandler", 
    "PDFHandler", 
    "DOCXHandler",
    "ChromaVectorStore",
    "OllamaLLM",
    "OllamaEmbedding",
    "Neo4jDocumentGraph",
    "available_plugins"
]