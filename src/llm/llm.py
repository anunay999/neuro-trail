import os

import requests
from dotenv import load_dotenv
from litellm import completion
from enums import Model, ModelProvider

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")


def query_ollama(prompt, model=OLLAMA_MODEL):
    """Sends a prompt to the Ollama LLM API and returns the generated answer."""
    url = OLLAMA_HOST  # Updated API endpoint

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,  # Disable streaming to get a single response
    }
    response = requests.post(f"{url}/api/generate", json=payload)

    if response.status_code == 200:
        data = response.json()
        # Extracting the full response
        return data.get("response", "No response received")
    else:
        raise Exception(
            f"Ollama API request failed with status code {response.status_code}: {response.text}")


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
        return data.get(
            "response", "No response received"
        )  # Extracting the full response
    else:
        raise Exception(
            f"Ollama API request failed with status code {response.status_code}: {response.text}"
        )
