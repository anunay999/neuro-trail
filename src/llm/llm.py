from litellm import completion

from core.settings_config import settings


def get_llm() -> callable:
    """
    Returns a function to invoke the LLM based on the selected model.
    Uses LiteLLM's `completion()` method for interaction.
    """
    model = settings.llm_model
    model_provider = settings.llm_provider
    # Find the correct Model Enum
    if not model:
        raise ValueError(f"Model {model} is not recognized.")

    # Fetch the correct API key or host URL dynamically
    if model_provider == "ollama":
        # Default to local Ollama server
        api_base = settings.llm_base_url
        api_key = None  # Ollama doesn't use an API key
    else:
        api_key = settings.llm_api_key
        api_base = None  # API Base is only needed for Ollama

    def query_llm(messages, temperature=0):
        """
        Calls the LiteLLM API with the specified model and messages.
        Automatically configures API base for Ollama.
        """
        try:
            response = completion(
                model=f"{model_provider}/{model}",
                messages=messages,
                api_key=api_key if api_key else None,  # Pass only if defined
                api_base=api_base
                if model_provider == "ollama"
                else None,  # Only for Ollama
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                stream=True,
            )
            for part in response:
                yield part.choices[0].delta.content or ""
        except Exception as e:
            yield f"Error: {str(e)}"

    return query_llm
