import os

from litellm import completion

from enums import Model, ModelProvider


def get_llm(model: str) -> callable:
    """
    Returns a function to invoke the LLM based on the selected model.
    Uses LiteLLM's `completion()` method for interaction.
    """

    # Find the correct Model Enum
    model_enum = next((m for m in Model if m.model_name == model), None)
    if not model_enum:
        raise ValueError(f"Model {model} is not recognized.")

    provider = model_enum.provider

    # Fetch the correct API key or host URL dynamically
    if provider == ModelProvider.OLLAMA:
        # Default to local Ollama server
        api_base = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        api_key = None  # Ollama doesn't use an API key
    else:
        api_key = os.getenv(provider.api_key_env_var, "")
        api_base = None  # API Base is only needed for Ollama

    def query_llm(messages, temperature=0):
        """
        Calls the LiteLLM API with the specified model and messages.
        Automatically configures API base for Ollama.
        """
        try:
            response = completion(
                model=model,
                messages=messages,
                api_key=api_key if api_key else None,  # Pass only if defined
                api_base=api_base if provider == ModelProvider.OLLAMA else None,  # Only for Ollama
                temperature=temperature
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"

    return query_llm
