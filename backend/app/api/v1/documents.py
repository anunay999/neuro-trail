from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid

from app.db.session import get_db
from app.services.document_service import DocumentService
from app.schemas.document import DocumentResponse
import logging

logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document (EPUB, PDF, DOCX).
    This will create a knowledge graph and store embeddings in the vector DB.
    """
    # Validate file type
    filename = file.filename
    extension = filename.split(".")[-1].lower()
    if extension not in ["epub", "pdf", "docx"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}. Supported types: epub, pdf, docx"
        )
    
    # Read file content
    content = await file.read()
    
    # Create document record
    document_service = DocumentService(db)
    document_id = str(uuid.uuid4())
    document_service.create_document(
        document_id=document_id,
        filename=filename,
        file_type=extension
    )
    
    # Process document in background
    background_tasks.add_task(
        document_service.process_document,
        document_id=document_id,
        content=content,
        file_type=extension
    )
    
    return {
        "id": document_id,
        "filename": filename,
        "status": "processing",
        "message": "Document uploaded and processing started"
    }

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db)
):
    """List all processed documents"""
    document_service = DocumentService(db)
    documents = document_service.get_documents()

    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get document details by ID"""
    document_service = DocumentService(db)
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document