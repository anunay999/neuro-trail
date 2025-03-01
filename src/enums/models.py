from enum import Enum
import os


class ModelProvider(Enum):
    """Enum representing model providers."""
    OPENAI = "OpenAI"
    GOOGLE = "Google"
    OLLAMA = "Ollama"

    @property
    def api_key_env_var(self) -> str:
        """Dynamically get the API key environment variable name."""
        return {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.GOOGLE: "GEMINI_API_KEY"
        }[self]


class Model(Enum):
    """Enum mapping models to providers."""
    GPT_4O = ("openai/gpt-4o", ModelProvider.OPENAI)
    GPT_3_5 = ("openai/gpt-3.5-turbo", ModelProvider.OPENAI)
    GEMINI_PRO = ("gemini/gemini-1.5-pro", ModelProvider.GOOGLE)
    GEMINI_1_5_PRO = ("gemini/gemini-1.5-pro", ModelProvider.GOOGLE)
    OLLAMA_DEEPSEEK_R1_7B = ("ollama/deepseek-r1:7b", ModelProvider.OLLAMA)

    def __init__(self, model_name: str, provider: ModelProvider):
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
