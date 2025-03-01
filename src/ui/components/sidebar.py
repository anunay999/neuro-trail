import os
import time

import streamlit as st

from enums import Model, ModelProvider


def process_uploaded_files():
    """Function to process uploaded files when button is clicked."""
    if not st.session_state["uploaded_files"]:
        st.sidebar.warning("⚠️ No files to process.")
        return

    # Indicate processing start
    st.session_state["processing_status"] = "Processing files... ⏳"

    # Simulated processing delay (Replace this with real file processing logic)
    time.sleep(2)

    # Mark files as processed
    st.session_state["processing_status"] = "✅ Files processed successfully!"


def sidebar():
    st.sidebar.title(":gear: Configuration")

    # Ensure session state is initialized
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = None
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = []  # Store multiple files
    if "processing_status" not in st.session_state:
        st.session_state["processing_status"] = None  # Track file processing

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
        api_key = st.sidebar.text_input(
            f"Enter {api_key_name}", type="password")
        if api_key:
            os.environ[api_key_name] = api_key
    elif selected_provider == ModelProvider.OLLAMA:
        ollama_host = st.sidebar.text_input(
            "Enter Ollama Host URL (http://localhost:11434)"
        )
        os.environ["OLLAMA_HOST"] = ollama_host

    # Model Selection
    available_models = [
        model for model in Model if model.provider == selected_provider]
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

        # Append new file without overwriting previous uploads
        if uploaded_file is not None:
            if uploaded_file.name not in [f.name for f in st.session_state["uploaded_files"]]:
                st.session_state["uploaded_files"].append(uploaded_file)

        # Display all uploaded files persistently
        if st.session_state["uploaded_files"]:
            st.markdown("### Uploaded Files")
            for file in st.session_state["uploaded_files"]:
                st.success(f"✅ {file.name}")

    # Processing Button (Disabled if no file is uploaded)
    process_disabled = len(st.session_state["uploaded_files"]) == 0
    st.sidebar.button(
        "🚀 Build Knowledge",
        disabled=process_disabled,
        type="primary",
        on_click=process_uploaded_files,  # Calls function when clicked
    )

    # Show processing status
    if st.session_state["processing_status"]:
        st.sidebar.success(st.session_state["processing_status"])
