import os

import streamlit as st

from enums import EmbeddingModel, Model, Provider
from learning_canvas import LearningCanvas


def process_uploaded_files(canvas: LearningCanvas):
    """Function to process uploaded EPUB, DOCX, and PDF files."""
    if not st.session_state["uploaded_files"]:
        st.sidebar.warning("⚠️ No files to process.")
        return

    # Indicate processing start
    st.session_state["processing_status"] = "Processing files... ⏳"
    st.sidebar.info("Processing files... Please wait.")

    for uploaded_file in st.session_state["uploaded_files"]:
        file_extension = uploaded_file.name.split(".")[-1].lower()

        if file_extension == "epub":
            st.sidebar.info(f"📖 Processing EPUB: {uploaded_file.name}")
            # Call the add_epub function with file-like object
            # Pass file object directly
            canvas.add_epub(uploaded_file, user_id="user_123")

        elif file_extension in ["docx", "pdf"]:
            st.sidebar.info(
                f"📄 Skipping {uploaded_file.name} (Handler not implemented yet)")
            # Placeholder for future DOCX/PDF handling

    # Update processing status
    st.session_state["processing_status"] = "✅ Files processed successfully!"
    st.sidebar.success(st.session_state["processing_status"])


def initialize_session_state():
    """Initialize session state variables if not already set."""
    session_defaults = {
        "selected_model": None,
        "selected_embedding_model": None,
        "uploaded_files": [],
        "processing_status": None,
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def configure_llm():
    """Handles LLM provider and model selection."""
    st.sidebar.subheader("LLM Configuration")

    provider_option = st.sidebar.selectbox(
        "Select Provider",
        options=[provider.value for provider in Provider.llm_providers()],
        index=0,
    )
    selected_provider = Provider(provider_option)

    api_key = handle_api_key_input(selected_provider)

    # Model Selection for LLM
    available_models = [
        model for model in Model if model.provider == selected_provider]
    selected_model = st.sidebar.selectbox(
        "Select LLM Model", options=[model.model_name for model in available_models]
    )

    st.session_state["selected_provider"] = selected_provider

    # Store selected model in session state
    st.session_state["selected_model"] = next(
        (m for m in Model if m.model_name == selected_model), None
    )

    return selected_provider, api_key


def configure_embedding(same_provider):
    """Handles Embedding provider and model selection."""
    st.sidebar.subheader("Embedding Configuration")

    if same_provider:
        selected_embedding_provider = st.session_state["selected_provider"]
    else:
        embedding_provider_option = st.sidebar.selectbox(
            "Select Embedding Provider",
            options=[provider.value for provider in Provider if provider !=
                     st.session_state["selected_provider"]],
            index=0,
        )
        selected_embedding_provider = Provider(embedding_provider_option)
        handle_api_key_input(selected_embedding_provider)

    # Embedding Model Selection
    available_embedding_models = [
        model for model in EmbeddingModel if model.provider == selected_embedding_provider]
    selected_embedding_model = st.sidebar.selectbox(
        "Select Embedding Model", options=[model.model_name for model in available_embedding_models]
    )

    # Store selected embedding model in session state
    st.session_state["selected_embedding_model"] = next(
        (m for m in EmbeddingModel if m.model_name == selected_embedding_model), None
    )


def handle_api_key_input(provider):
    """Handles API key input for a given provider."""
    if provider in {Provider.OPENAI, Provider.GOOGLE, Provider.HUGGINGFACE, Provider.MISTRAL}:
        api_key_name = provider.api_key_env_var
        api_key = st.sidebar.text_input(
            f"Enter {api_key_name}", type="password")
        if api_key:
            os.environ[api_key_name] = api_key
        return api_key
    elif provider == Provider.OLLAMA:
        ollama_host = st.sidebar.text_input(
            "Enter Ollama Host URL (http://localhost:11434)")
        os.environ["OLLAMA_HOST"] = ollama_host
        return ollama_host


def handle_file_upload():
    """Handles file upload functionality."""
    with st.sidebar.expander(":file_folder: Upload Documents", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload a document (EPUB, DOCX, PDF)",
            type=["epub", "docx", "pdf"],
            help="Supports EPUB, DOCX, and PDF formats",
        )

        if uploaded_file and uploaded_file.name not in [f.name for f in st.session_state["uploaded_files"]]:
            st.session_state["uploaded_files"].append(uploaded_file)

        if st.session_state["uploaded_files"]:
            st.markdown("### Uploaded Files")
            for file in st.session_state["uploaded_files"]:
                st.success(f"✅ {file.name}")


def handle_processing_button(canvas):
    """Handles the knowledge-building process button."""
    process_disabled = len(st.session_state["uploaded_files"]) == 0
    st.sidebar.button(
        "🚀 Build Knowledge",
        disabled=process_disabled,
        type="primary",
        on_click=process_uploaded_files,
        args=(canvas,)  # Calls function when clicked
    )

    if st.session_state["processing_status"]:
        st.sidebar.success(st.session_state["processing_status"])


def sidebar(canvas: "LearningCanvas"):
    """Main sidebar function."""
    st.sidebar.title(":gear: Configuration")
    initialize_session_state()

    # Configure LLM and Embedding
    llm_provider, llm_api_key = configure_llm()

    same_provider = st.sidebar.checkbox(
        "Use same provider for LLM & Embedding")

    configure_embedding(same_provider)

    # Handle file upload & processing
    handle_file_upload()
    handle_processing_button(canvas)
