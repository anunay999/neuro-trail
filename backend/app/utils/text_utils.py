from typing import List, Dict, Any, Optional
import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalize text (remove extra whitespace, convert to lowercase)
    
    Args:
        text: Input text
        
    Returns:
        str: Normalized text
    """
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks with overlap
    
    Args:
        text: Input text
        chunk_size: Maximum size of each chunk
        overlap: Overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # Normalize text first
    text = normalize_text(text)
    
    # If text is shorter than chunk_size, return as is
    if len(text) <= chunk_size:
        return [text]
    
    # Split text into chunks
    chunks = []
    start = 0
    
    while start < len(text):
        # Get chunk
        end = start + chunk_size
        chunk = text[start:end]
        
        # If not at the end, try to find a good breaking point
        if end < len(text):
            # Try to break at paragraph or sentence
            break_points = [
                chunk.rfind('\n\n'), 
                chunk.rfind('. '), 
                chunk.rfind('? '), 
                chunk.rfind('! '),
                chunk.rfind(';'), 
                chunk.rfind(',')
            ]
            
            # Use the first valid break point
            for bp in break_points:
                if bp != -1 and bp > chunk_size // 2:
                    end = start + bp + 2  # Include the period and space
                    chunk = text[start:end]
                    break
        
        chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap if end - overlap > start else end
    
    return chunks


def extract_metadata(text: str, metadata_pattern: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Extract metadata from text based on patterns
    
    Args:
        text: Input text
        metadata_pattern: Optional dictionary of metadata field names to regex patterns
        
    Returns:
        Dict[str, Any]: Dictionary of extracted metadata
    """
    metadata = {}
    
    # Default patterns if none provided
    if metadata_pattern is None:
        metadata_pattern = {
            "title": r"(?:Title|TITLE):\s*(.+?)(?:\n|$)",
            "author": r"(?:Author|AUTHOR|By):\s*(.+?)(?:\n|$)",
            "date": r"(?:Date|DATE):\s*(.+?)(?:\n|$)"
        }
    
    # Extract metadata using patterns
    for key, pattern in metadata_pattern.items():
        match = re.search(pattern, text)
        if match:
            metadata[key] = match.group(1).strip()
    
    return metadata