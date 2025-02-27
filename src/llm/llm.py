import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")


def query_ollama(prompt, model=OLLAMA_MODEL):
    """ Sends a prompt to the Ollama LLM API and returns the generated answer. """
    url = OLLAMA_HOST  # Updated API endpoint

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Disable streaming to get a single response
    }
    response = requests.post(f"{url}/api/generate", json=payload)

    if response.status_code == 200:
        data = response.json()
        # Extracting the full response
        return data.get("response", "No response received")
    else:
        raise Exception(
            f"Ollama API request failed with status code {response.status_code}: {response.text}")


class LLMProvider:
    """
    Abstract base class for LLM providers.  Defines the common interface.
    """

    def __init__(self, model_name):
        self.model_name = model_name

    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the LLM and returns the response.

        Args:
            prompt: The text prompt to send.

        Returns:
            The LLM's response as a string.
        """
        raise NotImplementedError(
            "Subclasses must implement the query method.")

    def supports_streaming(self) -> bool:
        """
        Indicates whether the provider supports streaming responses.  Default is False.
        """
        return False

    def query_stream(self, prompt: str):
        """
        Sends a prompt to the LLM and yields response chunks as they are generated.
        Only needs to be implemented if supports_streaming() returns True.

        Args:
            prompt: The text prompt to send.

        Yields:
            Response chunks as strings.
        """
        raise NotImplementedError("This provider does not support streaming.")


class OllamaLLMProvider(LLMProvider):
    """
    LLM provider for Ollama.
    """

    def __init__(self, model_name=OLLAMA_MODEL, host=OLLAMA_HOST):
        super().__init__(model_name)
        self.host = host

    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the Ollama LLM API and returns the generated answer.
        """
        return query_ollama(prompt, self.model_name)  # Reuse the existing function

    def supports_streaming(self) -> bool:
        return True

    def query_stream(self, prompt: str):
        """
        Streams responses from the Ollama API.
        """
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True
        }
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        try:
                            json_data = json.loads(decoded_line)
                            if "response" in json_data:
                                # Yield individual tokens
                                yield json_data["response"]
                            elif "error" in json_data:
                                raise Exception(
                                    f"Ollama API error: {json_data['error']}")
                        except json.JSONDecodeError:
                            print(
                                f"Warning: Could not decode JSON: {decoded_line}")
            else:
                raise Exception(
                    f"Ollama API request failed with status code {response.status_code}: {response.text}")


class OpenAIProvider(LLMProvider):
    """LLM provider for OpenAI models."""

    def __init__(self, model_name: str, api_key: str = None):
        super().__init__(model_name)
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OpenAI API key must be provided or set as OPENAI_API_KEY environment variable.")
        import openai
        openai.api_key = self._api_key
        self.client = openai.OpenAI()  # Use the offical client

    def query(self, prompt: str) -> str:
        response = self.client.completions.create(
            prompt=prompt, model=self.model_name)
        return response.choices[0].text

    def supports_streaming(self) -> bool:
        return True

    def query_stream(self, prompt: str):
        response_stream = self.client.completions.create(
            prompt=prompt, model=self.model_name, stream=True)
        for chunk in response_stream:
            if chunk.choices[0].text is not None:
                yield chunk.choices[0].text

# Add other providers as needed (e.g., forCohere, etc.)


class GeminiProvider(LLMProvider):
    """LLM provider for Google's Gemini models via the Vertex AI API."""

    def __init__(self, model_name: str, project_id: str = None, location: str = "us-central1"):
        super().__init__(model_name)
        self.project_id = project_id or os.getenv("GOOGLE_PROJECT_ID")
        self.location = location
        if not self.project_id:
            raise ValueError(
                "Google Cloud project ID must be provided or set as GOOGLE_PROJECT_ID environment variable.")

        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(model_name)  # No need to load every time

    def query(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    def supports_streaming(self) -> bool:
        return True

    def query_stream(self, prompt: str):
        response_stream = self.model.generate_content(prompt, stream=True)
        for chunk in response_stream:
            yield chunk.text


class LMStudioProvider(LLMProvider):
    """
    LLM provider for LM Studio. Assumes LM Studio is running a local OpenAI-compatible server.
    """

    def __init__(self, model_name, base_url="http://localhost", port=1234):
        super().__init__(model_name)
        self.base_url = f"{base_url}:{port}/v1"  # Construct base URL with port

    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the LM Studio server and returns the generated answer.
        """
        import openai

        client = openai.OpenAI(base_url=self.base_url, api_key="not-needed")
        response = client.completions.create(
            prompt=prompt, model=self.model_name)
        return response.choices[0].text

    def supports_streaming(self) -> bool:
        return True

    def query_stream(self, prompt: str):
        """
        Streams responses from the LM Studio server.
        """
        import openai
        client = openai.OpenAI(base_url=self.base_url, api_key="not-needed")
        response_stream = client.completions.create(
            prompt=prompt, model=self.model_name, stream=True)
        for chunk in response_stream:
            if chunk.choices[0].text is not None:
                yield chunk.choices[0].text


class MistralAIProvider(LLMProvider):
    """
    LLM Provider for Mistral AI using their official client.
    """

    def __init__(self, model_name: str, api_key: str = None):
        super().__init__(model_name)
        self._api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Mistral AI API key must be provided or set as MISTRAL_API_KEY environment variable.")

        from mistralai.client import MistralClient
        self.client = MistralClient(api_key=self._api_key)

    def query(self, prompt: str) -> str:
        response = self.client.chat(model=self.model_name, messages=[
                                    {"role": "user", "content": prompt}])
        return response.choices[0].message.content

    def supports_streaming(self) -> bool:
        return True

    def query_stream(self, prompt: str):
        response_stream = self.client.chat_stream(model=self.model_name, messages=[
                                                  {"role": "user", "content": prompt}])
        for chunk in response_stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content


def get_llm_provider(provider_type: str, model_name: str, **kwargs) -> LLMProvider:
    """
    Factory function to create an LLM provider instance.

    Args:
        provider_type:  The type of provider ("ollama", "openai", etc.).
        model_name: The name of the model.
        **kwargs:  Additional provider-specific arguments.

    Returns:
        An instance of the specified LLMProvider.

    Raises:
        ValueError: If an unsupported provider type is requested.
    """
    if provider_type.lower() == "ollama":
        return OllamaLLMProvider(model_name=model_name, **kwargs)
    elif provider_type.lower() == "openai":
        return OpenAIProvider(model_name=model_name, **kwargs)
    # Add other provider types here
    else:
        raise ValueError(f"Unsupported LLM provider type: {provider_type}")


# Example usage (with error handling)
if __name__ == "__main__":
    try:
        # Use Ollama
        ollama_provider = get_llm_provider("ollama", "deepseek-coder:1.3b")
        prompt = "Write a python function that adds two numbers"
        response = ollama_provider.query(prompt)
        print(f"Ollama Response:\n{response}")

        if ollama_provider.supports_streaming():
            print("\nOllama Streaming Response:")
            for chunk in ollama_provider.query_stream(prompt):
                print(chunk, end="", flush=True)  # Flush is important here
            print()  # Newline at the end

        # Use OpenAI
        # use the instruct version with the completions endpoint
        openai_provider = get_llm_provider("openai", "gpt-3.5-turbo-instruct")
        response = openai_provider.query(
            "Explain the theory of relativity in simple terms.")
        print(f"\nOpenAI Response:\n{response}")

        if openai_provider.supports_streaming():
            print("\nOpenai Streaming Response")
            for chunk in openai_provider.query_stream("Explain the theory of relativity in simple terms."):
                print(chunk, end="", flush=True)
            print()

    except Exception as e:
        print(f"An error occurred: {e}")
