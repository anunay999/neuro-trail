import os

import ebooklib
from ebooklib import epub


def flatten_toc(toc_list):
    """Recursively flatten the EPUB table of contents."""
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


def extract_epub(epub_path):
    """
    Reads an EPUB file and returns:
      - metadata (title, author)
      - full text content
      - list of chapters with sequence numbers (as simple strings)
    """
    book = epub.read_epub(epub_path)

    # Extract metadata
    title_list = book.get_metadata("DC", "title")
    author_list = book.get_metadata("DC", "creator")
    title = title_list[0][0] if title_list else os.path.basename(epub_path)
    author = author_list[0][0] if author_list else "Unknown Author"

    # Extract full text from document items
    text_parts = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            try:
                part = item.get_body_content().decode("utf-8")
            except Exception:
                part = item.get_content().decode("utf-8", errors="ignore")
            text_parts.append(part)
    full_text = "\n".join(text_parts)

    # Extract chapters from the TOC, converting objects to simple strings.
    toc = book.toc
    chapters = []
    if toc:
        flat_chapters = flatten_toc(toc)
        processed = []
        for chap in flat_chapters:
            if isinstance(chap, epub.Link):
                chapter_title = chap.title  # Use the title attribute of Link
            else:
                chapter_title = str(chap)
            processed.append(chapter_title)
        chapters = [
            {"title": chap, "seq": idx + 1} for idx, chap in enumerate(processed)
        ]
    return {"title": title, "author": author}, full_text, chapters
