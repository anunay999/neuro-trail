from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables with defaults."""
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password", env="NEO4J_PASSWORD")

    # Vector Store Configuration
    vector_store_provider: str = Field(
        default="qdrant", env="VECTOR_STORE_PROVIDER")
    vector_store_knowledge_collection: str = Field(
        default="knowledge", env="VECTOR_STORE_KNOWLEDGE_COLLECTION")
    vector_store_user_collection: str = Field(
        default="user", env="VECTOR_STORE_USER_COLLECTION")
    vector_store_host: str = Field(
        default="localhost", env="VECTOR_STORE_HOST")
    vector_store_port: int = Field(default=6333, env="VECTOR_STORE_PORT")
    

    # LLM Configuration
    llm_provider: str = Field(default="ollama", env="LLM_PROVIDER")
    llm_model: str = Field(default="deepseek-r1:7b", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.0, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    llm_base_url: str = Field(
        default="http://localhost:11434", env="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default="", env="LLM_API_KEY")

    # Embedder Configuration
    embedder_provider: str = Field(default="ollama", env="EMBEDDER_PROVIDER")
    embedder_provider_api_key: Optional[str] = Field(default="", env="EMBEDDER_PROVIDER_API_KEY")
    embedder_model: str = Field(
        default="nomic-embed-text:latest", env="EMBEDDER_MODEL")
    embedder_base_url: str = Field(
        default="http://localhost:11434", env="EMBEDDER_BASE_URL")


    def save_to_env(self):
        """Save current settings to .env file, preserving existing variables not in this config"""
        # Read existing .env content if it exists
        env_content = {}
        try:
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env_content[key.strip()] = value.strip()
        except Exception:
            # If file can't be read, start with empty dict
            pass

        # Update with current settings
        all_settings = self.model_dump()
        for key, value in all_settings.items():
            # Convert to uppercase with underscore format
            env_key = ''.join(['_' + c.upper() if c.isupper()
                              else c.upper() for c in key]).lstrip('_')
            if value is not None:
                env_content[env_key] = str(value)

        # Write back to .env
        with open(".env", "w") as f:
            for key, value in sorted(env_content.items()):
                f.write(f"{key}={value}\n")


settings = Settings()
