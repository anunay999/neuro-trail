from sentence_transformers import SentenceTransformer
from src.embeddings.base import EmbeddingBase, EmbeddingResult
from pydantic import BaseModel
import numpy as np

# self.model = SentenceTransformer(model_name)
# self.dimension = self.model.get_sentence_embedding_dimension()


class SentenceTransformerBase(EmbeddingBase):
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        super().__init__(model_name=model_name, dimension=384)
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.model_name = model_name

    def get_embedding(self, text: str) -> EmbeddingResult:
        embedding = self.model.encode(text, convert_to_tensor=True)
        return EmbeddingResult(embedding=embedding, model_name=self.model_name, dimension=self.dimension)
