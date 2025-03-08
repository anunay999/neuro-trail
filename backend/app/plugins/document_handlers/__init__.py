# Export plugins
from app.plugins.document_handlers.epub_handler import EPUBHandler
from app.plugins.document_handlers.pdf_handler import PDFHandler
from app.plugins.document_handlers.docx_handler import DOCXHandler

__all__ = [
    "EPUBHandler",
    "PDFHandler",
    "DOCXHandler"
]