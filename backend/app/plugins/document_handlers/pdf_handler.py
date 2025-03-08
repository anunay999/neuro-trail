import logging
import io
from typing import Dict, Any, List, Optional
import pymupdf

from app.core.plugin_base import DocumentPlugin
from app.utils.text_utils import split_text, extract_metadata

# Configure logging
logger = logging.getLogger(__name__)


class PDFHandler(DocumentPlugin):
    """Plugin for handling PDF documents"""
    
    plugin_type = "document_handler"
    plugin_name = "pdf_handler"
    plugin_version = "0.1.0"
    plugin_description = "Handler for PDF documents"
    
    def __init__(self):
        """Initialize PDF handler"""
        self.initialized = False
    
    async def initialize(self, **kwargs) -> bool:
        """
        Initialize the plugin
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            bool: True if initialization successful
        """
        self.initialized = True
        logger.info("PDF handler initialized")
        return True
    
    async def shutdown(self) -> bool:
        """
        Shutdown the plugin
        
        Returns:
            bool: True if shutdown successful
        """
        self.initialized = False
        logger.info("PDF handler shutdown")
        return True
    
    async def process_document(
        self, 
        file_content: bytes, 
        file_name: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a PDF document
        
        Args:
            file_content: Binary content of the PDF file
            file_name: Name of the file
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Dictionary with processed document data
        """
        logger.info(f"Processing PDF document: {file_name}")
        
        try:
            # Create a BytesIO object from file_content
            file_stream = io.BytesIO(file_content)
            
            # Open the PDF
            pdf_document = pymupdf.open(stream=file_stream, filetype="pdf")
            
            # Extract metadata
            metadata = {
                "title": pdf_document.metadata.get("title", file_name),
                "author": pdf_document.metadata.get("author", "Unknown Author"),
                "format": "pdf",
                "pages": len(pdf_document)
            }
            
            # Extract chapters (bookmarks/outline)
            chapters = self._extract_chapters(pdf_document)
            
            # Extract text from each page
            text_parts = []
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
            
            # Combine all text parts
            full_text = "\n\n".join(text_parts)
            
            # Split text into chunks
            text_chunks = split_text(full_text, chunk_size=1000, overlap=200)
            
            logger.info(f"Processed PDF document: {metadata['title']} by {metadata['author']}, {len(text_chunks)} chunks")
            
            # Return processed document data
            return {
                "metadata": metadata,
                "chapters": chapters,
                "texts": text_chunks,
                "full_text": full_text
            }
            
        except Exception as e:
            logger.exception(f"Error processing PDF document: {e}")
            raise Exception(f"Error processing PDF document: {str(e)}")
    
    def _extract_chapters(self, pdf_document) -> List[Dict[str, Any]]:
        """
        Extract chapters from PDF outline
        
        Args:
            pdf_document: PyMuPDF document
            
        Returns:
            List[Dict[str, Any]]: List of chapters
        """
        chapters = []
        toc = pdf_document.get_toc()
        
        if not toc:
            # If no table of contents, create chapters for each page
            for i in range(len(pdf_document)):
                chapters.append({
                    "title": f"Page {i+1}",
                    "seq": i+1
                })
        else:
            # Extract chapters from table of contents
            for i, (level, title, page) in enumerate(toc):
                if level == 1:  # Only top-level items
                    chapters.append({
                        "title": title,
                        "seq": i+1
                    })
        
        return chapters