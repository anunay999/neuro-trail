from litellm import completion

from core.settings_config import settings
import logging
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s"
)
logger = logging.getLogger(__name__)


def get_llm(streaming=True) -> callable:
    """
    Returns a function to invoke the LLM based on the selected model.
    Uses LiteLLM's `completion()` method for interaction.
    """

    model = (
        st.session_state.llm_model
        if "llm_model" in st.session_state
        else settings.llm_model
    )
    model_provider = (
        st.session_state.llm_provider
        if "llm_provider" in st.session_state
        else settings.llm_provider
    )
    # Find the correct Model Enum
    if not model:
        raise ValueError(f"Model {model} is not recognized.")

    # Fetch the correct API key or host URL dynamically
    if model_provider == "ollama":
        # Default to local Ollama server
        api_base = (
            st.session_state.llm_base_url
            if "llm_base_url" in st.session_state
            else settings.llm_base_url
        )
        api_key = None  # Ollama doesn't use an API key
    else:
        api_key = (
            st.session_state.llm_api_key
            if "llm_api_key" in st.session_state
            else settings.llm_api_key
        )
        api_base = None  # API Base is only needed for Ollama

    temp = (
        st.session_state.llm_temperature
        if "llm_temperature" in st.session_state
        else settings.llm_temperature
    )
    max_tokens = (
        st.session_state.llm_max_tokens
        if "llm_max_tokens" in st.session_state
        else settings.llm_max_tokens
    )

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
                temperature=temp,
                max_tokens=max_tokens,
                stream=True,
            )
            for part in response:
                yield part.choices[0].delta.content or ""
        except Exception as e:
            yield f"Error: {str(e)}"

    def query_llm_without_streaming(messages, temperature=0) -> str:
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
                temperature=temp,
                max_tokens=max_tokens,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Error: {str(e)}")

    return query_llm if streaming else query_llm_without_streaming
