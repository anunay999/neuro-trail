import faiss
import numpy as np

from embeddings.base import EmbeddingBase


class VectorStore:
    def __init__(self, embedding_model: EmbeddingBase):
        self.embedding_model = embedding_model
        self.dimension = self.embedding_model.dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_mapping: list[
            dict[str, str | None]
        ] = []  # Each element is {'text': ..., 'chapter': optional}

    def add_text_chunks(self, text_chunks: list[str], chapter: str | None = None):
        for chunk in text_chunks:
            self.chunk_mapping.append({"text": chunk, "chapter": chapter})

        embeddings = [
            self.embedding_model.get_embedding(chunk).embedding for chunk in text_chunks
        ]
        self.index.add(np.array(embeddings, dtype=np.float32))

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str | None]]:
        query_embedding = self.embedding_model.get_embedding(query).embedding
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32), top_k
        )
        results = [self.chunk_mapping[idx] for idx in indices[0]]
        return results
