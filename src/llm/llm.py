import os

import requests
from dotenv import load_dotenv

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
        return data.get(
            "response", "No response received"
        )  # Extracting the full response
    else:
        raise Exception(
            f"Ollama API request failed with status code {response.status_code}: {response.text}"
        )
