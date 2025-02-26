import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")

def query_ollama(prompt, model="deepseek-r1:7b"):
    """ Sends a prompt to the Ollama LLM API and returns the generated answer. """
    url = OLLAMA_URL  # Updated API endpoint
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Disable streaming to get a single response
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data.get("response", "No response received")  # Extracting the full response
    else:
        raise Exception(f"Ollama API request failed with status code {response.status_code}: {response.text}")
