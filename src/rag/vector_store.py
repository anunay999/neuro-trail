import os
from typing import Dict, List, Optional

from chromadb import PersistentClient
import faiss
import litellm
import numpy as np
from enums.models import Provider, EmbeddingModel
from typing import Union


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
            embedding_model_name: The embedding model name.
            embedding_provider: Embedding provider
            api_base: API base URL for providers like Ollama.
            chapter_mode: If True, store chapter information.
            persist: Whether to use persistent ChromaDB storage.
            collection_name: ChromaDB collection name.
        """
        self.embedding_model = embedding_model
        self.embedding_provider = embedding_model.provider
        self.api_base = os.getenv(
            "OLLAMA_HOST") if self.embedding_model.provider == Provider.OLLAMA else None
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
        if self.embedding_provider.value in Provider.all_providers():
            self.dimension = None  # Determined dynamically when first used
        else:
            raise ValueError(
                f"Unsupported embedding provider: {self.embedding_provider}")

    def _initialize_chromadb(self, collection_name: str):
        """Initializes ChromaDB for persistent storage."""
        persist_dir = os.path.join(".data", "chromadb")
        os.makedirs(persist_dir, exist_ok=True)
        self.chroma_client = PersistentClient(path=persist_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name)

    def _get_embedding_with_retries(self, text_chunks: Union[str, List[str]], retries=3) -> np.ndarray:
        """Generates embeddings for a list of text chunks."""
        if isinstance(text_chunks, str):
            text_chunks = [text_chunks]

        if self.embedding_provider:
            try:
                response = litellm.embedding(
                    input=text_chunks,
                    model=self.embedding_model.model_name,
                    api_base=self.api_base if self.embedding_provider == Provider.OLLAMA else None
                )
                embeddings = [item["embedding"] for item in response["data"]]
                embeddings_np = np.array(embeddings, dtype=np.float32)

                if self.dimension is None:
                    self.dimension = embeddings_np.shape[1]
                    self.index = faiss.IndexFlatL2(self.dimension)

                return embeddings_np
            except litellm.APIConnectionError as e:
                print(f"API Connection Error: {e} retrying...")
                if retries > 0:
                    return self._get_embedding_with_retries(text_chunks, retries - 1)

        else:
            raise ValueError(
                f"Unsupported embedding provider: {self.embedding_provider}")

    def add_text_chunks(
        self,
        text_chunks: List[str],
        chapter: Optional[str] = None,
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict]] = None
    ):
        """Adds text chunks to the vector store with optional metadata."""
        if self.chapter_mode and chapter is None:
            raise ValueError(
                "Chapter must be provided when chapter_mode is enabled")

        embeddings = self._get_embedding(text_chunks)

        if ids is None:
            ids = [str(self.collection.count() + i)
                   for i in range(len(text_chunks))]

        if metadata is None:
            metadata = [{"chapter": chapter} if self.chapter_mode else {}
                        for _ in text_chunks]
        elif self.chapter_mode:
            for data in metadata:
                data["chapter"] = chapter

        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=text_chunks,
            metadatas=metadata,
            ids=ids,
        )

        if self.index is not None:
            self.index.add(embeddings)

    def search(self, query: str, top_k: int = 3, metadata_filter: Optional[Dict] = None) -> List[Dict]:
        """Searches the vector store for the most similar chunks to the query."""
        query_embedding = self._get_embedding_with_retries(query)

        # Step 1: Query ChromaDB to get relevant documents based on metadata filter
        chroma_query_params = {
            "query_embeddings": query_embedding.tolist(),
            # Fetch more from Chroma for refinement
            "n_results": min(top_k * 5, self.collection.count())
        }

        # Only add `where` if `metadata_filter` is not empty
        if metadata_filter:
            chroma_query_params["where"] = metadata_filter

        chroma_results = self.collection.query(**chroma_query_params)

        if not chroma_results["ids"][0]:  # Handle empty results
            return []

        # Extract ChromaDB document IDs
        chroma_ids = chroma_results["ids"][0]

        # Step 2: Use FAISS to refine results
        if self.index is not None and self.index.ntotal > 0:
            distances, indices = self.index.search(
                query_embedding, min(top_k, self.index.ntotal))

            refined_results = []
            for i, idx in enumerate(indices[0]):
                if idx >= len(chroma_ids):  # Ensure index is valid
                    continue
                original_chroma_id = chroma_ids[idx]
                doc_data = self.collection.get(ids=[original_chroma_id], include=[
                                               "documents", "metadatas"])

                refined_results.append({
                    "text": doc_data["documents"][0],
                    **doc_data["metadatas"][0]
                })

            return refined_results[:top_k]

        # If FAISS is not available, return raw ChromaDB results
        return [
            {"text": doc, **meta}
            for doc, meta in zip(chroma_results["documents"][0], chroma_results["metadatas"][0])
        ]

    def get_all_documents(self, metadata_filter: Optional[Dict] = None):
        """Retrieves all documents, optionally filtered by metadata."""
        return self.collection.get(where=metadata_filter, include=["documents", "metadatas"]) if metadata_filter else self.collection.get(include=["documents", "metadatas"])

    def clear_all(self):
        """Deletes all data and resets the FAISS index."""
        self.chroma_client.delete_collection(self.collection.name)
        self.collection = self.chroma_client.get_or_create_collection(
            name="vector_store_collection")
        if self.dimension is not None:
            self.index = faiss.IndexFlatL2(self.dimension)
