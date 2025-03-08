from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables with defaults."""
    
    # API Settings
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "Neuro Trail"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/neurotrail"
    
    # Neo4j Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Vector Store Settings
    VECTOR_STORE_PROVIDER: str = "chroma"
    VECTOR_STORE_KNOWLEDGE_COLLECTION: str = "knowledge"
    VECTOR_STORE_USER_COLLECTION: str = "user"
    VECTOR_STORE_HOST: str = "localhost"
    VECTOR_STORE_PORT: int = 6333
    
    # LLM Settings
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "deepseek-r1:7b"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 2000
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_API_KEY: Optional[str] = None
    
    # Embedder Settings
    EMBEDDER_PROVIDER: str = "ollama"
    EMBEDDER_MODEL: str = "nomic-embed-text"
    EMBEDDER_BASE_URL: str = "http://localhost:11434"
    EMBEDDER_PROVIDER_API_KEY: Optional[str] = None
    
    # File Storage Settings
    UPLOAD_DIR: str = "./.data/uploads"
    TEMP_DIR: str = "./.data/temp"
    
    # Plugin Settings
    PLUGINS_DIR: str = "./plugins"
    ENABLED_PLUGINS: List[str] = []
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )
    
    def get_database_url(self) -> str:
        """Get database URL with optional SSL configuration for production"""
        if self.DEBUG:
            return self.DATABASE_URL
        
        # For production, you might want to add SSL
        return f"{self.DATABASE_URL}?sslmode=require"
    
    def save_to_env(self, env_path: Optional[str] = None) -> bool:
        """
        Save current settings to .env file, preserving existing variables not in this config.
        
        Args:
            env_path: Custom path for .env file.
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
        settings_dict = {}
        for field, field_info in self.model_fields.items():
            settings_dict[field] = getattr(self, field)
        
        # Update with new settings
        existing_env.update(
            {key: str(value) for key, value in settings_dict.items() if value is not None}
        )
        
        try:
            # Write back to .env file
            with open(env_path, "w", encoding="utf-8") as f:
                for key, value in existing_env.items():
                    f.write(f"{key}={value}\n")
            
            return True
        except Exception as e:
            print(f"Failed to save settings: {e}")
            return False


# Create settings instance
settings = Settings()