from abc import ABC, abstractmethod
from pydantic import BaseModel
import numpy as np


class EmbeddingResult(BaseModel):
    embedding: np.ndarray
    model_name: str
    dimension: int

    class Config:
        arbitrary_types_allowed = True


class EmbeddingBase(ABC):
    def __init__(self, model_name, dimension):
        self.model_name = model_name
        self.dimension = dimension

    @abstractmethod
    def get_embedding(self, text: str) -> EmbeddingResult:
        pass

    def get_embeddings(self, texts: list[str]) -> list[EmbeddingResult]:
        return [self.get_embedding(text) for text in texts]
