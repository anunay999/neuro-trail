import logging
from typing import List, Union

import litellm
import numpy as np
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

from v2.core.settings_config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings from text."""

    def __init__(
        self,
    ):
        """
        Initialize the embedding service.

        Args:
            embedding_model: The embedding model to use.
        """
        self.embedding_model = settings.embedder_model
        self.provider = settings.embedder_provider

        # Set API base URL for embeddings
        if self.provider == "ollama":
            self.api_base = settings.embedder_base_url or "http://localhost:11434"
            self.api_key = None
        else:
            self.api_base = None
            # Get API key from model or settings
            self.api_key = settings.embedder_model_api_key

        self.ollama_client = ollama.Client(host=self.api_base)

        logger.info(
            f"Initialized EmbeddingService with model {self.embedding_model_val}"
        )

    @property
    def embedding_model_val(self):
        """Get the embedding model"""
        return f"{self.provider}/{self.embedding_model}"

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def generate(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for the provided texts.

        Args:
            texts: A single text or list of texts to embed.

        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]

        logger.info(
            f"Generating embeddings for {len(texts)} texts using model: {self.embedding_model}"
        )

        try:
            embeddings = []
            batch_size = 250  # TODO: make this configurable via config.

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                if self.provider == "ollama":
                    response = self.ollama_client.embed(
                        model=self.embedding_model,
                        input=batch,
                    )
                    embeddings.extend(response.embeddings)
                else:
                    response = litellm.embedding(
                        input=batch,
                        model=self.embedding_model_val,
                        api_key=self.api_key if self.api_key else None,
                        api_base=self.api_base if self.provider == "ollama" else None,
                    )
                    embeddings.extend([item["embedding"] for item in response["data"]])

            embeddings_np = np.array(embeddings, dtype=np.float32)

            return embeddings_np

        except litellm.APIConnectionError as e:
            logger.error(f"API Connection Error: {e}")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error during embedding generation: {e}")
            raise

    # For compatibility with langchain api spec
    def embed_documents(self, texts: Union[str, List[str]]) -> np.ndarray:
        return self.generate(texts)

    def embed_query(self, text: str) -> np.ndarray:
        return self.generate([text])[0]
