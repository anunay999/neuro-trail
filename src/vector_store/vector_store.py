import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunk_mapping = []  # Each element is {'text': ..., 'chapter': optional}

    def add_text_chunks(self, text_chunks, chapter=None):
        for chunk in text_chunks:
            self.chunk_mapping.append({"text": chunk, "chapter": chapter})
        embeddings = self.model.encode(text_chunks)
        self.index.add(np.array(embeddings, dtype=np.float32))

    def search(self, query, top_k=3):
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding, dtype=np.float32), top_k
        )
        results = [self.chunk_mapping[idx] for idx in indices[0]]
        return results
