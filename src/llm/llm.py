import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama_service:11434")

def is_connected():
    response = requests.get(f"{OLLAMA_HOST}/api/tags")
    if response.status_code == 200:
        print("✅ Ollama is running. Available models:", response.json())
    else:
        print(f"❌ Failed to connect to Ollama: {response.status_code} - {response.text}")

    # Try generating text
    generate_payload = {
        "model": "gemma",  # Replace with the correct model name
        "prompt": "Hello, how are you?"
    }

    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json=generate_payload
    )

    if response.status_code == 200:
        print("✅ Ollama response:", response.json())
        return True
    else:
        print(f"❌ Ollama API request failed: {response.status_code} - {response.text}")
        return False

def query_ollama(prompt, model="deepseek-r1:7b"):
    """ Sends a prompt to the Ollama LLM API and returns the generated answer. """
    url = OLLAMA_HOST  # Updated API endpoint
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Disable streaming to get a single response
    }

    if is_connected():
        return

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data.get("response", "No response received")  # Extracting the full response
    else:
        raise Exception(f"Ollama API request failed with status code {response.status_code}: {response.text}")


