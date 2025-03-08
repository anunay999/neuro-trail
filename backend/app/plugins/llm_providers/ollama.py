import logging
import aiohttp
import json
from typing import Dict, List, Any, Optional, AsyncGenerator

from app.core.plugin_base import LLMPlugin
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class OllamaLLM(LLMPlugin):
    """Plugin for Ollama LLM integration"""
    
    plugin_type = "llm"
    plugin_name = "ollama"
    plugin_version = "0.1.0"
    plugin_description = "Ollama LLM provider"
    
    def __init__(self):
        """Initialize Ollama LLM plugin"""
        self.initialized = False
        self.base_url = settings.LLM_BASE_URL
        self.model = settings.LLM_MODEL
        
    async def initialize(self, **kwargs) -> bool:
        """
        Initialize the plugin
        
        Args:
            **kwargs: Additional parameters
                - base_url: Optional base URL override
                - model: Optional model name override
            
        Returns:
            bool: True if initialization successful
        """
        try:
            # Get settings from kwargs or use defaults
            self.base_url = kwargs.get("base_url") or self.base_url
            self.model = kwargs.get("model") or self.model
            
            # Check if base URL is valid
            if not self.base_url:
                logger.error("Ollama base URL not provided")
                return False
            
            # Check if model is valid
            if not self.model:
                logger.error("Ollama model name not provided")
                return False
            
            # Check if Ollama is running
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        logger.error(f"Ollama service not available at {self.base_url}")
                        return False
                    
                    # Check if model is available
                    tags = await response.json()
                    models = [tag["name"] for tag in tags.get("models", [])]
                    
                    if self.model not in models:
                        logger.warning(f"Model {self.model} not found in Ollama. Available models: {models}")
                        # Note: We don't return False here as the model might be pulled later
            
            self.initialized = True
            logger.info(f"Ollama LLM initialized with model: {self.model}")
            return True
            
        except Exception as e:
            logger.exception(f"Error initializing Ollama LLM: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Shutdown the plugin
        
        Returns:
            bool: True if shutdown successful
        """
        self.initialized = False
        logger.info("Ollama LLM shutdown")
        return True
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """
        Generate text using the LLM
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
                - model: Optional model override
                - system_prompt: Optional system prompt
                
        Returns:
            str: Generated text
        """
        if not self.initialized:
            logger.error("Ollama LLM not initialized")
            return "Error: Ollama LLM not initialized. Please check if Ollama is running."
        
        try:
            # Prepare request parameters
            model = kwargs.get("model") or self.model
            system_prompt = kwargs.get("system_prompt")
            
            # Prepare request payload
            if system_prompt:
                # Use chat API with system prompt
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens
                    }
                }
                api_endpoint = f"{self.base_url}/api/chat"
            else:
                # Use completion API
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens
                    }
                }
                api_endpoint = f"{self.base_url}/api/generate"
            
            # Make request to Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(api_endpoint, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {error_text}")
                        return f"Error: Ollama API returned status {response.status}: {error_text}"
                    
                    result = await response.json()
                    
                    if system_prompt:
                        # Extract text from chat response
                        return result.get("message", {}).get("content", "")
                    else:
                        # Extract text from completion response
                        return result.get("response", "")
                    
        except Exception as e:
            logger.exception(f"Error generating text with Ollama: {e}")
            return f"Error: Failed to generate text with Ollama: {str(e)}"
    
    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream generated text from the LLM
        
        Args:
            prompt: Input prompt
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
                - model: Optional model override
                - system_prompt: Optional system prompt
                
        Yields:
            str: Chunks of generated text
        """
        if not self.initialized:
            logger.error("Ollama LLM not initialized")
            yield "Error: Ollama LLM not initialized. Please check if Ollama is running."
            return
        
        try:
            # Prepare request parameters
            model = kwargs.get("model") or self.model
            system_prompt = kwargs.get("system_prompt")
            
            # Prepare request payload
            if system_prompt:
                # Use chat API with system prompt
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens
                    }
                }
                api_endpoint = f"{self.base_url}/api/chat"
            else:
                # Use completion API
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens
                    }
                }
                api_endpoint = f"{self.base_url}/api/generate"
            
            # Make streaming request to Ollama API
            async with aiohttp.ClientSession() as session:
                async with session.post(api_endpoint, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error: {error_text}")
                        yield f"Error: Ollama API returned status {response.status}: {error_text}"
                        return
                    
                    # Process streaming response
                    async for line in response.content:
                        if not line.strip():
                            continue
                        
                        try:
                            data = json.loads(line)
                            
                            if system_prompt:
                                # Extract text from chat stream
                                chunk = data.get("message", {}).get("content", "")
                            else:
                                # Extract text from completion stream
                                chunk = data.get("response", "")
                                
                            if chunk:
                                yield chunk
                                
                            # Check if done
                            if data.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON from Ollama stream: {line}")
                    
        except Exception as e:
            logger.exception(f"Error streaming text from Ollama: {e}")
            yield f"Error: Failed to stream text from Ollama: {str(e)}"