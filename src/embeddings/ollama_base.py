import numpy as np
import requests

from embeddings.base import EmbeddingBase, EmbeddingResult


class OllamaBase(EmbeddingBase):
    def __init__(self, model_name="bge-m3:latest"):
        super().__init__(model_name=model_name, dimension=1024)

    def get_embedding(self, text: str) -> EmbeddingResult:
        response = requests.post(
            "http://ollama_service:11434/api/embed",
            json={"model": self.model_name, "input": text}
        )
        if response.status_code == 200:
            response_json = response.json()
            embedding = np.array(response_json["embeddings"][0], dtype=np.float32)
            return EmbeddingResult(embedding=embedding, model_name=self.model_name, dimension=self.dimension)
        else:
            print(f"Error getting embedding: {response.text}")
            raise Exception(f"Error getting embedding: {response.text}")
