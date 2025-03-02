import os
from enum import Enum


class Provider(Enum):
    """Enum representing model providers."""

    OPENAI = ("OpenAI", True)
    GOOGLE = ("Google", True)
    OLLAMA = ("Ollama", True)
    HUGGINGFACE = ("HuggingFace", True)
    MISTRAL = ("Mistral", True)
    JINA_AI = ("JinaAI", False)  # Not an LLM provider

    def __new__(cls, value: str, is_llm_provider: bool):
        """Customize Enum creation to include additional attributes."""
        obj = object.__new__(cls)
        obj._value_ = value  # Standard enum value
        obj.is_llm_provider = is_llm_provider  # Custom attribute
        return obj

    @property
    def api_key_env_var(self) -> str:
        """Dynamically get the API key environment variable name."""
        return {
            Provider.OPENAI: "OPENAI_API_KEY",
            Provider.GOOGLE: "GEMINI_API_KEY",
            Provider.HUGGINGFACE: "HUGGINGFACE_API_KEY",
            Provider.MISTRAL: "MISTRAL_API_KEY",
            Provider.JINA_AI: "JINA_AI_API_KEY",
        }.get(self, "")

    @classmethod
    def llm_providers(cls):
        """Returns a list of providers that are LLM providers."""
        return [provider for provider in cls if provider.is_llm_provider]

    @classmethod
    def all_providers(cls):
        """Returns a list of providers that are LLM providers."""
        return [provider.value for provider in cls]


class Model(Enum):
    """Enum mapping models to providers."""

    GPT_4O = ("openai/gpt-4o", Provider.OPENAI)
    GPT_3_5 = ("openai/gpt-3.5-turbo", Provider.OPENAI)
    GEMINI_PRO = ("gemini/gemini-1.5-pro", Provider.GOOGLE)
    GEMINI_1_5_PRO = ("gemini/gemini-1.5-pro", Provider.GOOGLE)
    OLLAMA_DEEPSEEK_R1_7B = ("ollama/deepseek-r1:7b", Provider.OLLAMA)
    OLLAMA_DEEPSEEK_R1_1_5B = ("ollama/deepseek-r1:1.5b", Provider.OLLAMA)
    OLLAMA_LLAMA3_2 = ("ollama/llama3.2", Provider.OLLAMA)
    OLLAMA_MISTRAL = ("ollama/mistral", Provider.OLLAMA)
    OLLAMA_PHI4 = ("ollama/phi4", Provider.OLLAMA)

    def __init__(self, model_name: str, provider: Provider):
        self.model_name = model_name
        self.provider = provider

    @property
    def api_key(self) -> str:
        """Fetch API key name."""
        return self.provider.api_key_env_var

    @property
    def get_api_key_val(self) -> str:
        """Fetch API key dynamically from the correct environment variable."""
        api_key = os.environ.get(self.provider.api_key_env_var)
        if not api_key:
            return ""
        return api_key

    def __str__(self) -> str:
        return self.model_name

    def __repr__(self) -> str:
        return f"Model({self.model_name}, {self.provider})"


class EmbeddingModel(Enum):
    """Enum mapping embedding models to their providers."""

    # OpenAI Embeddings
    TEXT_EMBEDDING_ADA_002 = (
        "openai/text-embedding-ada-002", Provider.OPENAI)

    # Google Gemini Embeddings
    GEMINI_TEXT_EMBEDDING_004 = (
        "gemini/text-embedding-004", Provider.GOOGLE)

    # Ollama Embeddings
    OLLAMA_NOMIC_EMBED_TEXT = ("ollama/nomic-embed-text", Provider.OLLAMA)

    # HuggingFace Embeddings
    HUGGINGFACE_CODEBERT = (
        "huggingface/microsoft/codebert-base", Provider.HUGGINGFACE)

    # Mistral Embeddings
    MISTRAL_EMBED = ("mistral/mistral-embed", Provider.MISTRAL)

    JINA_AI_EMBED = ("jina_ai/jina-embeddings-v3", Provider.JINA_AI)

    def __init__(self, model_name: str, provider: Provider):
        self.model_name = model_name
        self.provider = provider

    @property
    def api_key(self) -> str:
        """Fetch API key name."""
        return self.provider.api_key_env_var

    @property
    def get_api_key_val(self) -> str:
        """Fetch API key dynamically from the correct environment variable."""
        return os.getenv(self.provider.api_key_env_var, "")

    def __str__(self) -> str:
        return self.model_name

    def __repr__(self) -> str:
        return f"EmbeddingModel({self.model_name}, {self.provider})"
