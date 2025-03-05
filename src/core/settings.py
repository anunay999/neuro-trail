from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str = Field(default="bolt://neo4j:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="password", env="NEO4J_PASSWORD")

    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")


settings = Settings()
