import logging
import os
from typing import Dict, List, Optional, Union

import faiss
import litellm
import numpy as np
import streamlit as st
from chromadb import PersistentClient

from enums.models import EmbeddingModel, Provider
from core.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(
        self,
        embedding_model: EmbeddingModel,
        chapter_mode: bool = False,
        persist: bool = True,
        collection_name: str = "vector_store_collection",
    ):
        """
        Initializes the VectorStore.

        Args:
            embedding_model: The embedding model.
            chapter_mode: If True, store chapter information.
            persist: Whether to use persistent ChromaDB storage.
            collection_name: ChromaDB collection name.
        """
        logger.info(
            f"Initializing VectorStore with embedding model: {embedding_model}, chapter_mode: {chapter_mode}, persist: {persist}, collection_name: {collection_name}")
        self.embedding_model = embedding_model
        self.embedding_provider = embedding_model.provider
        self.api_base = settings.ollama_host if self.embedding_model.provider == Provider.OLLAMA else None
        self.chapter_mode = chapter_mode

        # Initialize the embedding model
        self._initialize_embedding_model()

        # Initialize persistent storage (ChromaDB)
        self.persist = persist
        if self.persist:
            self._initialize_chromadb(collection_name)
        else:
            self.index = None  # FAISS index (only initialized when needed)

    def _initialize_embedding_model(self):
        """Initializes the embedding model based on the selected provider."""
        logger.info(
            f"Initializing embedding model with provider: {self.embedding_provider}")
        if self.embedding_provider.value in Provider.all_providers():
            self.dimension = None  # Determined dynamically when first used
        else:
            error_msg = f"Unsupported embedding provider: {self.embedding_provider}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _initialize_chromadb(self, collection_name: str):
        """Initializes ChromaDB for persistent storage."""
        logger.info(
            f"Initializing ChromaDB with collection name: {collection_name}")
        persist_dir = os.path.join(".data", "chromadb")
        os.makedirs(persist_dir, exist_ok=True)
        logger.debug(f"ChromaDB persistence directory: {persist_dir}")
        self.chroma_client = PersistentClient(path=persist_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name)
        logger.info(f"ChromaDB collection '{collection_name}' initialized.")

    def _get_embedding_with_retries(self, text_chunks: Union[str, List[str]], retries=3) -> np.ndarray:
        """Generates embeddings for a list of text chunks with retries."""
        if isinstance(text_chunks, str):
            text_chunks = [text_chunks]

        logger.info(
            f"Generating embeddings for {len(text_chunks)} text chunks using model: {self.embedding_model.model_name}")

        if self.embedding_provider:
            for attempt in range(retries):
                try:
                    response = litellm.embedding(
                        input=text_chunks,
                        model=self.embedding_model.model_name,
                        api_base=self.api_base if self.embedding_provider == Provider.OLLAMA else None
                    )
                    embeddings = [item["embedding"]
                                  for item in response["data"]]
                    embeddings_np = np.array(embeddings, dtype=np.float32)

                    if self.dimension is None:
                        self.dimension = embeddings_np.shape[1]
                        logger.info(
                            f"Embedding dimension determined: {self.dimension}")
                        self.index = faiss.IndexFlatL2(self.dimension)
                        logger.info("FAISS index initialized.")

                    return embeddings_np
                except litellm.APIConnectionError as e:
                    logger.warning(
                        f"API Connection Error (attempt {attempt + 1}/{retries}): {e}")
                    if attempt == retries - 1:
                        logger.error(
                            f"API Connection Error after {retries} retries: {e}")
                        st.error(
                            f"API Connection Error: {e}.  Please check your connection and API configuration.")
                        # Re-raise to stop further processing.  Critical error.
                        raise
                except Exception as e:  # Catch other potential litellm exceptions
                    # added general exception for unexpected errors
                    logger.exception(
                        f"Unexpected error during embedding (attempt {attempt + 1}/{retries}): {e}")
                    if attempt == retries - 1:
                        logger.error(
                            f"Embedding failed after {retries} retries")
                        st.error(
                            f"Embedding failed: {e}")
                        raise

        else:
            error_msg = f"Unsupported embedding provider: {self.embedding_provider}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def add_text_chunks(
        self,
        text_chunks: List[str],
        chapter: Optional[str] = None,
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict]] = None
    ):
        """Adds text chunks to the vector store with optional metadata."""
        logger.info(
            f"Adding {len(text_chunks)} text chunks to the vector store.")
        if self.chapter_mode and chapter is None:
            error_msg = "Chapter must be provided when chapter_mode is enabled"
            logger.error(error_msg)
            raise ValueError(error_msg)

        embeddings = self._get_embedding_with_retries(text_chunks)

        if ids is None:
            ids = [str(self.collection.count() + i)
                   for i in range(len(text_chunks))]
            logger.debug(f"Generated IDs for text chunks: {ids}")

        if metadata is None:
            metadata = [{"chapter": chapter} if self.chapter_mode else {}
                        for _ in text_chunks]
        elif self.chapter_mode:
            for data in metadata:
                data["chapter"] = chapter
        logger.debug(f"Metadata for text chunks: {metadata}")

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=text_chunks,
            metadatas=metadata,
            ids=ids,
        )
        logger.info("Text chunks added to ChromaDB.")

        if self.index is not None:
            self.index.add(embeddings)
            logger.info("Text chunks added to FAISS index.")

    def search(self, query: str, top_k: int = 3, metadata_filter: Optional[Dict] = None) -> List[Dict]:
        """Searches the vector store for the most similar chunks to the query."""
        logger.info(
            f"Searching for similar chunks to query: '{query}', top_k: {top_k}, metadata_filter: {metadata_filter}")
        query_embedding = self._get_embedding_with_retries(query)

        if query_embedding is None:
            logger.warning("Failed to fetch query embedding.")
            st.toast("Failed to fetch related documents.", icon="⚠️")
            return []

        # Step 1: Query ChromaDB to get relevant documents based on metadata filter
        chroma_query_params = {
            "query_embeddings": query_embedding.tolist(),
            # Fetch more from Chroma for refinement
            "n_results": min(top_k * 5, self.collection.count())
        }

        # Only add `where` if `metadata_filter` is not empty
        if metadata_filter:
            chroma_query_params["where"] = metadata_filter

        try:
            chroma_results = self.collection.query(**chroma_query_params)
            logger.debug(f"ChromaDB query results: {chroma_results}")

            if not chroma_results["ids"][0]:  # Handle empty results
                logger.info("No results found in ChromaDB.")
                return []

            # Extract ChromaDB document IDs
            chroma_ids = chroma_results["ids"][0]

            # Step 2: Use FAISS to refine results
            if self.index is not None and self.index.ntotal > 0:
                distances, indices = self.index.search(
                    query_embedding, min(top_k, self.index.ntotal))
                logger.debug(
                    f"FAISS search results - distances: {distances}, indices: {indices}")

                refined_results = []
                for i, idx in enumerate(indices[0]):
                    if idx >= len(chroma_ids):  # Ensure index is valid
                        logger.warning(
                            f"FAISS index out of range. Index: {idx}, Chroma IDs length: {len(chroma_ids)}")
                        continue
                    original_chroma_id = chroma_ids[idx]
                    doc_data = self.collection.get(ids=[original_chroma_id], include=[
                                                   "documents", "metadatas"])
                    logger.debug(
                        f"Retrieved document data from ChromaDB: {doc_data}")

                    refined_results.append({
                        "text": doc_data["documents"][0],
                        **doc_data["metadatas"][0]
                    })

                logger.info(f"Returning top {top_k} refined results.")
                return refined_results[:top_k]

            # If FAISS is not available, return raw ChromaDB results
            logger.info(
                "FAISS index not available, returning raw ChromaDB results.")
            results = [
                {"text": doc, **meta}
                for doc, meta in zip(chroma_results["documents"][0], chroma_results["metadatas"][0])
            ]
            return results

        except TypeError as e:
            logger.exception(
                f"TypeError occurred while fetching documents: {e}")
            # added error for type errors
            st.error(
                f"An error occurred while processing your request.  Please check the logs for details.")
            return []
        except Exception as e:
            logger.exception(
                f"Error occurred while fetching documents: {e}")
            st.error(
                f"An error occurred while processing your request. Please check the logs for details.")
            return []

    def get_all_documents(self, metadata_filter: Optional[Dict] = None):
        """Retrieves all documents, optionally filtered by metadata."""
        logger.info(
            f"Retrieving all documents with metadata filter: {metadata_filter}")
        try:
            if metadata_filter:
                result = self.collection.get(
                    where=metadata_filter, include=["documents", "metadatas"])
            else:
                result = self.collection.get(
                    include=["documents", "metadatas"])
            logger.debug(f"Retrieved {len(result['documents'])} documents.")
            return result
        except Exception as e:
            logger.exception(f"Error retrieving all documents: {e}")
            # added error handling
            st.error(f"An error occurred while retrieving documents: {e}")
            return []

    def clear_all(self):
        """Deletes all data and resets the FAISS index."""
        logger.info("Clearing all data from the vector store.")
        try:
            self.chroma_client.delete_collection(self.collection.name)
            logger.info("ChromaDB collection deleted.")
            self.collection = self.chroma_client.get_or_create_collection(
                name="vector_store_collection")
            logger.info("New ChromaDB collection created.")
            if self.dimension is not None:
                self.index = faiss.IndexFlatL2(self.dimension)
                logger.info("FAISS index reset.")
        except Exception as e:
            logger.exception(f"Error clearing all data: {e}")
            st.error(f"An error occurred while clearing data: {e}")
