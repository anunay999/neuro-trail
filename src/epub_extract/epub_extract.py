import os
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s"
)
logger = logging.getLogger(__name__)


def flatten_toc(toc_list):
    """Recursively flatten the EPUB table of contents into simple strings."""
    flat = []

    def _flatten(items):
        for item in items:
            if isinstance(item, tuple):
                section, children = item[0], item[1]
                if isinstance(section, epub.Link):
                    flat.append({"title": section.title, "href": section.href})
                elif isinstance(section, epub.Section):
                    # For sections, add their title if available
                    if hasattr(section, "title") and section.title:
                        flat.append({"title": section.title, "href": None})
                _flatten(children)
            elif isinstance(item, epub.Link):
                flat.append({"title": item.title, "href": item.href})
            elif isinstance(item, epub.Section):
                if hasattr(item, "title") and item.title:
                    flat.append({"title": item.title, "href": None})

    _flatten(toc_list)
    return flat


def clean_html_content(html_content):
    """
    Clean HTML content to extract only the readable text.
    Removes HTML tags, scripts, styles, and unnecessary whitespace.
    """
    if not html_content:
        return ""

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script_or_style in soup(["script", "style", "head", "nav", "footer"]):
        script_or_style.decompose()

    # Get text and normalize whitespace
    text = soup.get_text(separator=" ")

    # Clean up excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_chapter_content(book, href):
    """Extract and clean content for a specific chapter by href."""
    if not href:
        return ""

    # Remove fragment identifier if present
    href = href.split("#")[0]

    for item in book.get_items():
        if item.get_name() == href:
            try:
                html_content = item.get_content().decode("utf-8", errors="ignore")
                return clean_html_content(html_content)
            except Exception as e:
                logging.error(f"Error extracting chapter content: {e}")
                return ""

    return ""


def extract_epub(epub_path):
    """
    Reads an EPUB file and returns:
      - metadata (title, author)
      - cleaned text content
      - list of chapters with sequence numbers and content
    """
    try:
        book = epub.read_epub(epub_path)
        logging.info(f"Successfully opened EPUB file: {epub_path}")

        # Extract metadata
        title_list = book.get_metadata("DC", "title")
        author_list = book.get_metadata("DC", "creator")
        title = title_list[0][0] if title_list else os.path.basename(epub_path)
        author = author_list[0][0] if author_list else "Unknown Author"

        logging.info(f"Extracted metadata: Title='{title}', Author='{author}'")

        # Get the table of contents
        toc = book.toc
        chapters = []

        if toc:
            logging.info("Table of Contents found.")
            flat_chapters = flatten_toc(toc)
            for idx, chapter in enumerate(flat_chapters):
                chapter_title = (
                    chapter["title"] if chapter["title"] else f"Chapter {idx + 1}"
                )
                chapter_content = extract_chapter_content(book, chapter["href"])

                chapters.append(
                    {"title": chapter_title, "seq": idx + 1, "content": chapter_content}
                )
            logging.info(f"Extracted {len(chapters)} chapters from Table of Contents.")

        # If no TOC is available, extract content from all document items
        if not chapters:
            logging.info(
                "No Table of Contents found. Extracting from all document items."
            )
            all_text = []
            for idx, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
                try:
                    html_content = item.get_content().decode("utf-8", errors="ignore")
                    clean_text = clean_html_content(html_content)
                    if clean_text:
                        all_text.append(clean_text)
                        chapters.append(
                            {
                                "title": f"Section {idx + 1}",
                                "seq": idx + 1,
                                "content": clean_text,
                            }
                        )
                except Exception as e:
                    logging.error(f"Error processing document item: {e}")
            logging.info(f"Extracted {len(chapters)} sections from document items.")

        # Full text is the concatenation of all chapter content
        full_text = "\n\n".join([chapter["content"] for chapter in chapters])
        logging.info("Full text assembled.")

        return {
            "metadata": {"title": title, "author": author},
            "full_text": full_text,
            "chapters": chapters,
        }

    except Exception as e:
        logging.error(f"Error extracting EPUB: {e}")
        return {
            "metadata": {"title": os.path.basename(epub_path), "author": "Unknown"},
            "full_text": "",
            "chapters": [],
        }
