import logging
from typing import List, Union

import litellm
import numpy as np
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

from core.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
            response = litellm.embedding(
                input=texts,
                model=self.embedding_model_val,
                api_key=self.api_key if self.api_key else None,
                api_base=self.api_base if self.provider == "ollama" else None,
            )

            embeddings = [item["embedding"] for item in response["data"]]
            embeddings_np = np.array(embeddings, dtype=np.float32)

            return embeddings_np

        except litellm.APIConnectionError as e:
            logger.error(f"API Connection Error: {e}")
            st.toast(
                f"API Connection Error: {e}. Please check your connection and API configuration."
            )
            raise

        except Exception as e:
            logger.exception(f"Unexpected error during embedding generation: {e}")
            st.toast(f"Embedding failed: {e}")
            raise
