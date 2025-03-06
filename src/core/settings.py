import logging
import os
from typing import Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables with defaults."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password", env="NEO4J_PASSWORD")

    # Vector Store Configuration
    vector_store_provider: str = Field(default="qdrant", env="VECTOR_STORE_PROVIDER")
    vector_store_knowledge_collection: str = Field(
        default="knowledge", env="VECTOR_STORE_KNOWLEDGE_COLLECTION"
    )
    vector_store_user_collection: str = Field(
        default="user", env="VECTOR_STORE_USER_COLLECTION"
    )
    vector_store_host: str = Field(default="localhost", env="VECTOR_STORE_HOST")
    vector_store_port: int = Field(default=6333, env="VECTOR_STORE_PORT")

    # LLM Configuration
    llm_provider: str = Field(default="ollama", env="LLM_PROVIDER")
    llm_model: str = Field(default="deepseek-r1:7b", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.0, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    llm_base_url: str = Field(default="http://localhost:11434", env="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default="", env="LLM_API_KEY")

    # Embedder Configuration
    embedder_provider: str = Field(default="ollama", env="EMBEDDER_PROVIDER")
    embedder_provider_api_key: Optional[str] = Field(
        default="", env="EMBEDDER_PROVIDER_API_KEY"
    )
    embedder_model: str = Field(default="nomic-embed-text:latest", env="EMBEDDER_MODEL")
    embedder_base_url: str = Field(
        default="http://localhost:11434", env="EMBEDDER_BASE_URL"
    )

    def save_to_env(self, env_path: Optional[str] = None) -> bool:
        """
        Save current settings to .env file, preserving existing variables not in this config.

        Args:
            env_path (Optional[str]): Custom path for .env file.
                                      Defaults to .env in current working directory.

        Returns:
            bool: True if successful, False otherwise
        """
        if env_path is None:
            env_path = os.path.join(os.getcwd(), ".env")

        # Read existing .env file if it exists
        existing_env: Dict[str, str] = {}
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, _, value = line.partition("=")
                        existing_env[key] = value

        # Dump current settings
        settings_dict = self.model_dump()

        # Update with new settings
        existing_env.update(
            {key.upper(): str(value) for key, value in settings_dict.items()}
        )

        try:
            # Write back to .env file
            with open(env_path, "w", encoding="utf-8") as f:
                for key, value in existing_env.items():
                    f.write(f"{key}={value}\n")

            logger.info(f"Successfully saved settings to {env_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False


settings = Settings()
