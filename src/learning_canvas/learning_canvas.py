import os
import tempfile
import logging

from enums import EmbeddingModel, Model
from epub_extract import extract_epub
from knowledge_graph import KnowledgeGraph
from llm import get_llm
from rag import VectorStore
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LearningCanvas:
    def __init__(self):
        """
        Initializes the LearningCanvas components.
        """
        logger.info("Initializing LearningCanvas")
        self.kg = KnowledgeGraph()
        self.model = None
        self.embedding_model = None
        self.vector_store = None  # Initialized later after model is set

    def set_model(self, model: Model, embedding_model: EmbeddingModel):
        """
        Sets the LLM model and embedding model dynamically, and initializes the VectorStore.
        """
        logger.info(
            f"Setting LLM model: {model}, Embedding model: {embedding_model}")
        self.model = model
        self.embedding_model = embedding_model

        # Initialize the Vector Store with the selected embedding model
        self.vector_store = VectorStore(
            embedding_model=self.embedding_model,
            chapter_mode=True
        )
        logger.info("VectorStore initialized.")

    def add_epub(self, epub_file, user_id="user_123"):
        """
        Processes an uploaded EPUB file and adds it to the system.
        """
        logger.info(f"Adding EPUB file for user: {user_id}")

        # Use a 'with' statement for automatic cleanup of the temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp_file:
            temp_file.write(epub_file.read())
            temp_file_path = temp_file.name
            logger.debug(f"Created temporary file: {temp_file_path}")

        try:
            metadata, full_text, chapters = extract_epub(temp_file_path)
            logger.info(
                f"Loaded '{metadata['title']}' by {metadata['author']}. Chapters found: {len(chapters)}"
            )

            self.kg.add_book(metadata["title"], metadata["author"])
            if chapters:
                self.kg.add_chapters(metadata["title"], chapters)
                logger.info(
                    f"Added {len(chapters)} chapters to knowledge graph.")
            else:
                logger.warning("No chapters found in EPUB.")

            paragraphs = [p.strip() for p in full_text.split(
                "\n\n") if len(p.strip()) > 50]
            logger.info(f"Extracted {len(paragraphs)} paragraphs from EPUB.")
            self.vector_store.add_text_chunks(
                paragraphs, chapter=metadata["title"])
            logger.info("EPUB processed and added to vector store.")

        except Exception as e:
            logger.exception(f"Error processing EPUB file: {e}")
            st.toast(
                f"An error occurred while processing the EPUB: {e}", icon="⚠️")
            raise Exception(f"Error processing EPUB file: {e}")

        finally:
            os.remove(temp_file_path)
            logger.debug(f"Removed temporary file: {temp_file_path}")

    def search_query(self, query, top_k=3):
        """
        Searches for relevant text chunks using the vector store.
        """
        logger.info(
            f"Searching for relevant context for query: '{query}', top_k: {top_k}")
        results = []
        try:
            results = self.vector_store.search(query, top_k=top_k)
            for i, res in enumerate(results):
                chapter_info = f"(Chapter: {res['chapter']})" if res.get(
                    "chapter") else ""
                logger.info(
                    f"Result {i+1} {chapter_info}:\n{res['text'][:200]}...\n")
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
            st.toast(
                f"An error occurred while searching for context: {e}", icon="⚠️")
            return None  # Or some other appropriate error handling

        if not context_chunks:
            logger.info("No relevant context found.  Using default prompt.")
            prompt = f"Answer the following question:\n{query}"
        else:
            context_text = "\n".join([chunk["text"]
                                     for chunk in context_chunks])
            logger.info(f"Context found.  Length: {len(context_text)}")
            prompt = f"Using the following context:\n{context_text}\n\nAnswer the following question:\n{query}"

        try:
            llm = get_llm(self.model)
            response = llm(
                messages=[{"role": "user", "content": prompt}], temperature=0.7
            )
            logger.info("Received response from LLM.")
            return response
        except Exception as e:
            logger.exception(f"Error during LLM call: {e}")
            st.toast(
                f"An error occurred while getting the LLM response: {e}", icon="⚠️")
            return None

    def get_user_history(self, user_id="user_123"):
        """
        Retrieves the user's learning history.
        """
        logger.info(f"Retrieving user history for user: {user_id}")
        # TODO : Add knowledge graph for user memory
        pass

    def close(self):
        """Closes connections to any resources."""
        logger.info("Closing LearningCanvas resources.")
        try:
            self.kg.close()
            logger.info("Knowledge graph connection closed.")
        except Exception as e:
            logger.exception(f"Error closing KnowledgeGraph connection: {e}")
            # added error handling
            st.toast(
                f"Error closing knowledge graph connection: {e}", icon="⚠️")
