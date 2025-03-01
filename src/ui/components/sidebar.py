import os

import streamlit as st

from enums import Model, ModelProvider


def sidebar():
    st.sidebar.title(":gear: Configuration")

    # Ensure session state is initialized
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = None
    if "uploaded_file" not in st.session_state:
        st.session_state["uploaded_file"] = None

    # Model Provider Selection
    provider_option = st.sidebar.selectbox(
        "Select Model Provider",
        options=[provider.value for provider in ModelProvider],
        index=0,
    )

    # Get Enum reference for provider
    selected_provider = ModelProvider(provider_option)

    # API Key Input (or Host URL for Ollama)
    if selected_provider in {ModelProvider.OPENAI, ModelProvider.GOOGLE}:
        api_key_name = selected_provider.api_key_env_var
        api_key = st.sidebar.text_input(f"Enter {api_key_name}", type="password")
        if api_key:
            os.environ[api_key_name] = api_key
    elif selected_provider == ModelProvider.OLLAMA:
        ollama_host = st.sidebar.text_input(
            "Enter Ollama Host URL (http://localhost:11434)"
        )
        os.environ["OLLAMA_HOST"] = ollama_host

    # Model Selection
    available_models = [model for model in Model if model.provider == selected_provider]
    selected_model = st.sidebar.selectbox(
        "Select Model", options=[model.model_name for model in available_models]
    )

    # Store the selected model in session state
    st.session_state["selected_model"] = next(
        (m for m in Model if m.model_name == selected_model), None
    )

    # File Upload Section
    with st.sidebar.expander(":file_folder: Upload Documents", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload a document (EPUB, DOCX, PDF)",
            type=["epub", "docx", "pdf"],
            help="Supports EPUB, DOCX, and PDF formats",
        )

        # Persist file in session state
        if uploaded_file is not None:
            st.session_state["uploaded_file"] = uploaded_file

        # Display uploaded file name persistently
        if st.session_state["uploaded_file"]:
            st.success(f"Uploaded: {st.session_state['uploaded_file'].name} ✅")
