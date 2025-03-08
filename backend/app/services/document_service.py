from fastapi import Depends
from sqlalchemy.orm import Session
import uuid
import logging
from typing import List, Dict, Any, Optional
from app.crud.document import document as crud_document

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentStatus
from app.services.plugin_manager import plugin_manager
from app.core.plugin_base import DocumentPlugin, VectorStorePlugin, KnowledgeGraphPlugin
from app.utils.file_utils import get_file_extension, create_temp_file, delete_file
from app.utils.text_utils import split_text, extract_metadata
from app.core.exceptions import ServiceUnavailableError

# Configure logging
logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document processing and management"""
    
    def __init__(self, db: Session):
        """
        Initialize document service
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_document(
        self, 
        document_id: str,
        filename: str, 
        file_type: str
    ) -> Document:
        """
        Create a document record in the database
        
        Args:
            document_id: Document ID
            filename: Original filename
            file_type: File type (extension)
            
        Returns:
            Document: Created document record
        """
        from app.schemas.document import DocumentCreate
        doc_in = DocumentCreate(filename=filename, file_type=file_type)
        document_obj = crud_document.create_with_id(
            db=self.db, 
            obj_in=doc_in, 
            document_id=document_id
        )
        
        logger.info(f"Created document record: {document_id}")

        
        return document_obj
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Optional[Document]: Document record or None if not found
        """
        return crud_document.get(db=self.db, id=document_id)
    
    def get_documents(self) -> List[Document]:
        """
        Get all documents
        
        Returns:
            List[Document]: List of document records
        """
        return crud_document.get_multi(
                        db=self.db, 
                        skip=0, 
                        limit=100  # You may want to add pagination parameters here
                    )
    
    def update_document_status(
        self, 
        document_id: str, 
        status: DocumentStatus,
        metadata: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None
    ) -> Optional[Document]:
        """
        Update document status
        
        Args:
            document_id: Document ID
            status: New status
            metadata: Optional metadata to update/merge
            message: Optional status message
            
        Returns:
            Optional[Document]: Updated document or None if not found
        """
        return crud_document.update_status(
            db=self.db,
            document_id=document_id,
            status=status,
            message=message,
            metadata=metadata
        )
    
    async def process_document(
        self,
        document_id: str,
        content: bytes,
        file_type: str
    ) -> Optional[Document]:
        """
        Process a document (in background)
        
        Args:
            document_id: Document ID
            content: Binary content of the file
            file_type: File type (extension)
            
        Returns:
            Optional[Document]: Processed document or None if error
        """
        try:
            # Update status to processing
            document = self.update_document_status(
                document_id=document_id,
                status=DocumentStatus.PROCESSING,
                message="Document processing started"
            )
            
            if not document:
                logger.error(f"Document not found: {document_id}")
                return None
            
            # Create temporary file
            temp_file_path = create_temp_file(content, suffix=f".{file_type}")
            
            try:
                # Get document handler plugin
                document_plugin = await self._get_document_plugin(file_type)
                
                # Process document
                result = await document_plugin.process_document(
                    file_content=content,
                    file_name=document.filename
                )
                
                # Extract texts and metadata
                texts = result.get("texts", [])
                metadata = result.get("metadata", {})
                chapters = result.get("chapters", [])
                
                # Update document with metadata
                document = self.update_document_status(
                    document_id=document_id,
                    status=DocumentStatus.PROCESSING,
                    metadata={
                        "title": metadata.get("title", document.filename),
                        "author": metadata.get("author", "Unknown"),
                        "chapters": chapters,
                        "chunk_count": len(texts),
                        "processed_date": str(document.updated_at)
                    },
                    message="Document parsed, adding to knowledge base"
                )
                
                # Add to knowledge graph
                await self._add_to_knowledge_graph(
                    document_id=document_id,
                    title=metadata.get("title", document.filename),
                    author=metadata.get("author", "Unknown"),
                    chapters=chapters
                )
                
                # Add to vector store
                await self._add_to_vector_store(
                    document_id=document_id,
                    texts=texts,
                    metadata=metadata
                )
                
                # Update status to completed
                document = self.update_document_status(
                    document_id=document_id,
                    status=DocumentStatus.COMPLETED,
                    message="Document processing completed"
                )
                
                logger.info(f"Document processing completed: {document_id}")
                
                return document
                
            finally:
                # Clean up temporary file
                delete_file(temp_file_path)
        
        except Exception as e:
            logger.exception(f"Error processing document {document_id}: {e}")
            
            # Update status to failed
            self.update_document_status(
                document_id=document_id,
                status=DocumentStatus.FAILED,
                message=f"Document processing failed: {str(e)}"
            )
            
            return None
    
    async def _get_document_plugin(self, file_type: str) -> DocumentPlugin:
        """Get document handler plugin for file type"""
        try:
            # Map file type to plugin name
            plugin_map = {
                "epub": "epub_handler",
                "pdf": "pdf_handler",
                "docx": "docx_handler"
            }
            
            plugin_name = plugin_map.get(file_type.lower())
            if not plugin_name:
                raise ServiceUnavailableError(f"Unsupported file type: {file_type}")
            
            # Get plugin from plugin manager
            from app.services.plugin_manager import plugin_manager
            plugin = await plugin_manager.get_plugin(
                plugin_type="document_handler",
                plugin_name=plugin_name
            )
            
            return plugin
        
        except Exception as e:
            logger.exception(f"Error getting document plugin for {file_type}: {e}")
            raise ServiceUnavailableError(f"Document processing service unavailable: {str(e)}")
    
    async def _add_to_knowledge_graph(
        self,
        document_id: str,
        title: str,
        author: str,
        chapters: List[Dict[str, Any]]
    ) -> bool:
        """Add document to knowledge graph"""
        try:
            # Get knowledge graph plugin from plugin manager
            from app.services.plugin_manager import plugin_manager
            kg_plugin = await plugin_manager.get_plugin(
                plugin_type="knowledge_graph",
                plugin_name="neo4j"
            )
            
            # Add book to knowledge graph
            await kg_plugin.add_book(title=title, author=author)
            
            # Add chapters if available
            if chapters:
                await kg_plugin.add_chapters(book_title=title, chapters=chapters)
            
            logger.info(f"Added document to knowledge graph: {document_id}")
            return True
        
        except Exception as e:
            logger.exception(f"Error adding document to knowledge graph: {e}")
            return False
        
    async def _add_to_vector_store(
    self,
    document_id: str,
    texts: List[str],
    metadata: Dict[str, Any]
    ) -> bool:
        """Add document texts to vector store"""
        try:
            # Get plugin manager
            from app.services.plugin_manager import plugin_manager
            
            # Get vector store plugin
            vector_store = await plugin_manager.get_plugin(
                plugin_type="vector_store",
                plugin_name="chroma"
            )
            
            # Get embedding plugin
            embedding_plugin = await plugin_manager.get_plugin(
                plugin_type="embedding",
                plugin_name="ollama"
            )
            
            # Generate embeddings
            embeddings = await embedding_plugin.embed_documents(texts=texts)
            
            # Prepare metadata for each chunk
            chunk_metadatas = []
            for i, _ in enumerate(texts):
                chunk_metadatas.append({
                    "document_id": document_id,
                    "chunk_index": i,
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "chapter": metadata.get("chapters", [{}])[min(i // 5, len(metadata.get("chapters", [])) - 1)].get("title", "") if metadata.get("chapters") else ""
                })
            
            # Add to vector store
            await vector_store.add_texts(
                texts=texts,
                embeddings=embeddings,
                metadatas=chunk_metadatas
            )
            
            logger.info(f"Added document to vector store: {document_id} ({len(texts)} chunks)")
            return True
        
        except Exception as e:
            logger.exception(f"Error adding document to vector store: {e}")
            return False