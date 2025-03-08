import logging
import io
from typing import Dict, Any, List, Optional
import ebooklib
from ebooklib import epub
import os

from app.core.plugin_base import DocumentPlugin
from app.utils.text_utils import split_text, extract_metadata

# Configure logging
logger = logging.getLogger(__name__)


class EPUBHandler(DocumentPlugin):
    """Plugin for handling EPUB documents"""
    
    plugin_type = "document_handler"
    plugin_name = "epub_handler"
    plugin_version = "0.1.0"
    plugin_description = "Handler for EPUB documents"
    
    def __init__(self):
        """Initialize EPUB handler"""
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
        logger.info("EPUB handler initialized")
        return True
    
    async def shutdown(self) -> bool:
        """
        Shutdown the plugin
        
        Returns:
            bool: True if shutdown successful
        """
        self.initialized = False
        logger.info("EPUB handler shutdown")
        return True
    
    async def process_document(
        self, 
        file_content: bytes, 
        file_name: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process an EPUB document
        
        Args:
            file_content: Binary content of the EPUB file
            file_name: Name of the file
            **kwargs: Additional parameters
            
        Returns:
            Dict[str, Any]: Dictionary with processed document data
        """
        logger.info(f"Processing EPUB document: {file_name}")
        
        try:
            # Create a BytesIO object from file_content
            file_stream = io.BytesIO(file_content)
            
            # Read EPUB file
            book = epub.read_epub(file_stream)
            
            # Extract metadata
            title_list = book.get_metadata("DC", "title")
            author_list = book.get_metadata("DC", "creator")
            title = title_list[0][0] if title_list else os.path.basename(file_name)
            author = author_list[0][0] if author_list else "Unknown Author"
            
            metadata = {
                "title": title,
                "author": author,
                "format": "epub"
            }
            
            # Extract chapters and content
            chapters = []
            text_parts = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    try:
                        # Get content as string
                        content = item.get_body_content().decode("utf-8")
                        
                        # Try to get chapter title from the content
                        chapter_title = self._extract_title(content)
                        
                        # Add to chapters list
                        if chapter_title:
                            chapters.append({
                                "title": chapter_title,
                                "seq": len(chapters) + 1
                            })
                        
                        # Add content to text parts
                        text_parts.append(content)
                    except Exception as e:
                        logger.warning(f"Error processing EPUB item: {e}")
            
            # Combine all text parts
            full_text = "\n\n".join(text_parts)
            
            # Split text into chunks
            text_chunks = split_text(full_text, chunk_size=1000, overlap=200)
            
            logger.info(f"Processed EPUB document: {title} by {author}, {len(text_chunks)} chunks")
            
            # Return processed document data
            return {
                "metadata": metadata,
                "chapters": chapters,
                "texts": text_chunks,
                "full_text": full_text
            }
            
        except Exception as e:
            logger.exception(f"Error processing EPUB document: {e}")
            raise Exception(f"Error processing EPUB document: {str(e)}")
    
    def _extract_title(self, content: str) -> Optional[str]:
        """
        Extract title from HTML content
        
        Args:
            content: HTML content
            
        Returns:
            Optional[str]: Title if found, None otherwise
        """
        # Try to extract title from h1 tags
        import re
        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.IGNORECASE)
        if title_match:
            return title_match.group(1)
        
        # Try to extract title from title tags
        title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE)
        if title_match:
            return title_match.group(1)
        
        return None
    
    def _flatten_toc(self, toc_list):
        """
        Recursively flatten the EPUB table of contents
        
        Args:
            toc_list: TOC list from epub.toc
            
        Returns:
            List[str]: Flattened TOC
        """
        flat = []

        def _flatten(items):
            for item in items:
                if isinstance(item, tuple):
                    # Format: (link, title, subitems)
                    link, title, *rest = item
                    flat.append(title)
                    if rest and isinstance(rest[0], list):
                        _flatten(rest[0])
                else:
                    flat.append(item)

        _flatten(toc_list)
        return flat