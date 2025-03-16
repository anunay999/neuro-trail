import io
import logging
import os
import tempfile

import streamlit as st

from core.settings_config import settings
from epub_extract import extract_epub
from llm import get_llm
from rag.vector_store_service import VectorStoreService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s"
)
logger = logging.getLogger(__name__)


class LearningCanvas:
    def __init__(self):
        """
        Initializes the LearningCanvas components.
        """
        logger.info("Initializing LearningCanvas")
        self.vector_store_service = None  # Initialized later after model is set

        # Set configured temperature from settings
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens

        self.__initialize_canvas()

    def __initialize_canvas(self):
        # Initialize the Vector Store Service with the selected embedding model
        self.vector_store_service = VectorStoreService(chapter_mode=True)
        logger.info("Vector Store Service initialized with configured settings.")

    def add_epub(self, epub_file, user_id="user_123") -> bool:
        """
        Processes an uploaded EPUB file and adds it to the system.

        Accepts either:
          - a file-like object with a .read() method (from st.file_uploader), or
          - a dict with keys "name" and "data" (serialized from session state).
        """
        logger.info(f"Adding EPUB file for user: {user_id}")

        # Validate vector store service is initialized
        if self.vector_store_service is None:
            error_msg = "Vector store service not initialized. Please set models first."
            logger.error(error_msg)
            st.toast(error_msg)
            return False

        # If epub_file is a dict from session state, wrap its data in a BytesIO stream.
        if isinstance(epub_file, dict) and "data" in epub_file:
            file_stream = io.BytesIO(epub_file["data"])
        else:
            file_stream = epub_file

        # Write the file's content to a temporary file for processing.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp_file:
            temp_file.write(file_stream.read())
            temp_file_path = temp_file.name
            logger.debug(f"Created temporary file: {temp_file_path}")

        try:
            epub_data = extract_epub(temp_file_path)
            metadata = epub_data["metadata"]
            full_text = epub_data["full_text"]
            chapters = epub_data["chapters"]

            logger.info(
                f"Loaded '{metadata['title']}' by {metadata['author']}. Chapters found: {len(chapters)}"
            )

            paragraphs = [
                p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 50
            ]
            self.vector_store_service.add_texts(
                texts=paragraphs, chapter=metadata["title"]
            )
            logger.info("EPUB processed and added to vector store.")
            return True

        except Exception as e:
            logger.exception(f"Error processing EPUB file: {e}")
            st.toast(f"An error occurred while processing the EPUB: {e}", icon="⚠️")
            raise Exception(f"Error processing EPUB file: {e}")

        finally:
            os.remove(temp_file_path)
            logger.debug(f"Removed temporary file: {temp_file_path}")

        return False

    def search_query(self, query, top_k=3):
        """
        Searches for relevant text chunks using the vector store.
        """
        logger.info(
            f"Searching for relevant context for query: '{query}', top_k: {top_k}"
        )
        results = []

        # Validate vector store service is initialized
        if self.vector_store_service is None:
            logger.error(
                "Vector store service not initialized. Please set models first."
            )
            st.toast(
                "Vector store service not initialized. Please set models first.",
                icon="⚠️",
            )
            return results

        try:
            results = self.vector_store_service.search(query, top_k=top_k)
            for i, res in enumerate(results):
                chapter_info = (
                    f"(Chapter: {res['chapter']})" if res.get(
                        "chapter") else ""
                )
                logger.info(
                    f"Result {i + 1} {chapter_info}:\n{res['text'][:200]}...\n")
        except Exception as e:
            logger.exception(f"Error during search query: {e}")
            st.toast(f"An error occurred while searching: {e}", icon="⚠️")
        return results

    def answer_query(self, query, user_id="user_123"):
        """
        Uses the vector store to fetch context and then sends a prompt
        (context + query) to the LLM.
        """
        logger.info(f"Answering query for user {user_id}: {query}")

        context_chunks = []
        try:
            context_chunks = self.search_query(query, top_k=5)
        except Exception as e:  # Catch potential errors in search_query
            logger.exception(f"Error during search in answer_query: {e}")
            st.toast(f"An error occurred while searching for context: {e}", icon="⚠️")
            yield f"Error retrieving context: {str(e)}"
            return

        if not context_chunks:
            logger.info("No relevant context found. Using default prompt.")
            prompt = f"Answer the following question:\n{query}"
        else:
            context_text = "\n".join([chunk["text"] for chunk in context_chunks])
            logger.info(f"Context found. Length: {len(context_text)}")
            prompt = f"Using the following context:\n{context_text}\n\nAnswer the following question:\n{query}"

        try:
            llm = get_llm()
            for token in llm(
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            ):
                yield token
            logger.info("Received response from LLM.")
        except Exception as e:
            logger.exception(f"Error during LLM call: {e}")
            st.toast(f"An error occurred while getting the LLM response: {e}", icon="⚠️")
            yield f"Error: LLM call failed: {str(e)}"


canvas = LearningCanvas()
