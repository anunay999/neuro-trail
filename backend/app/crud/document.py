from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid

from app.crud.base import CRUDBase
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentStatus


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    """CRUD for document operations"""
    
    def create_with_id(
        self, db: Session, *, obj_in: DocumentCreate, document_id: Optional[str] = None
    ) -> Document:
        """
        Create document with optional ID
        
        Args:
            db: Database session
            obj_in: Document create data
            document_id: Optional document ID
            
        Returns:
            Document: Created document
        """
        obj_in_data = obj_in.model_dump()
        db_obj = Document(
            id=document_id or str(uuid.uuid4()),
            filename=obj_in_data["filename"],
            file_type=obj_in_data["file_type"],
            status=DocumentStatus.PENDING,
            metadata={}
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_status(
        self, 
        db: Session, 
        *, 
        document_id: str, 
        status: DocumentStatus,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Document]:
        """
        Update document status
        
        Args:
            db: Database session
            document_id: Document ID
            status: New status
            message: Optional status message
            metadata: Optional metadata to update
            
        Returns:
            Optional[Document]: Updated document or None if not found
        """
        document = self.get(db, id=document_id)
        if not document:
            return None
        
        document.status = status
        
        if message:
            document.message = message
        
        if metadata:
            # Merge with existing metadata
            updated_metadata = document.doc_metadata or {}
            updated_metadata.update(metadata)
            document.doc_metadata = updated_metadata
        
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    
    def get_by_status(
        self, db: Session, status: DocumentStatus, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get documents by status
        
        Args:
            db: Database session
            status: Document status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Document]: List of documents
        """
        return db.query(Document).filter(
            Document.status == status
        ).offset(skip).limit(limit).all()
    
    def search_documents(
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Search documents by filename
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Document]: List of matching documents
        """
        return db.query(Document).filter(
            Document.filename.ilike(f"%{query}%")
        ).offset(skip).limit(limit).all()


document = CRUDDocument(Document)