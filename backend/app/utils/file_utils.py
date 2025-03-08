import os
import uuid
import shutil
from typing import Optional, List, Tuple
import logging

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


def ensure_dir(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        directory: Directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def save_upload_file(file_content: bytes, filename: str) -> Tuple[str, str]:
    """
    Save an uploaded file to the upload directory
    
    Args:
        file_content: Binary content of the file
        filename: Original filename
        
    Returns:
        Tuple[str, str]: Tuple of (file_id, file_path)
    """
    # Ensure upload directory exists
    ensure_dir(settings.UPLOAD_DIR)
    
    # Generate unique ID
    file_id = str(uuid.uuid4())
    
    # Get file extension
    _, ext = os.path.splitext(filename)
    
    # Create new filename with UUID
    new_filename = f"{file_id}{ext}"
    
    # Save file
    file_path = os.path.join(settings.UPLOAD_DIR, new_filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    logger.info(f"Saved uploaded file: {filename} -> {file_path}")
    
    return file_id, file_path


def create_temp_file(content: bytes, suffix: Optional[str] = None) -> str:
    """
    Create a temporary file
    
    Args:
        content: Binary content of the file
        suffix: Optional file suffix (extension)
        
    Returns:
        str: Path to the temporary file
    """
    # Ensure temp directory exists
    ensure_dir(settings.TEMP_DIR)
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}"
    if suffix:
        filename = f"{filename}{suffix}"
    
    # Create file path
    file_path = os.path.join(settings.TEMP_DIR, filename)
    
    # Write content
    with open(file_path, "wb") as f:
        f.write(content)
    
    return file_path


def delete_file(file_path: str) -> bool:
    """
    Delete a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
    
    return False


def get_file_extension(filename: str) -> str:
    """
    Get the file extension
    
    Args:
        filename: Filename
        
    Returns:
        str: File extension (lowercase, without dot)
    """
    _, ext = os.path.splitext(filename)
    return ext.lower().lstrip(".")