import os
import logging

import streamlit as st

from enums import EmbeddingModel, Model, Provider  # Assuming enums.models exists
from learning_canvas import LearningCanvas  # Assuming learning_canvas exists

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_uploaded_files(canvas: LearningCanvas):
    """Function to process uploaded EPUB, DOCX, and PDF files."""
    logger.info("Processing uploaded files.")

    if not st.session_state["uploaded_files"]:
        logger.warning("No files to process.")
        st.toast("No files to process.", icon="⚠️")
        return

    # Indicate processing start
    st.session_state["processing_status"] = "Processing files..."
    st.info("Processing files...", icon="⏳")

    for file_info in st.session_state["uploaded_files"]:
        file_name = file_info["name"]
        file_extension = file_name.split(".")[-1].lower()

        logger.info(
            f"Processing file: {file_name}, extension: {file_extension}")

        if file_extension == "epub":
            st.info(f"Processing EPUB: {file_name}", icon="📖")
            try:
                # Pass file name & bytes to your canvas method
                if canvas.add_epub(file_info, user_id="user_123"):
                    logger.info(f"Successfully processed EPUB: {file_name}")

            except Exception as e:
                logger.exception(f"Error processing EPUB {file_name}: {e}")
                st.error(f"Failed to process EPUB {file_name}: {e}")
                st.session_state["processing_status"] = False

        elif file_extension in ["docx", "pdf"]:
            logger.info(f"Skipping {file_name} (Handler not implemented yet)")
            st.info(
                f"Skipping {file_name} (Handler not implemented yet)", icon="📄")
            st.session_state["processing_status"] = True
        else:
            logger.warning(f"Unsupported file type: {file_extension}")
            st.warning(f"Unsupported file type: {file_extension}")
            st.session_state["processing_status"] = False

    # Update processing status
    if st.session_state["processing_status"]:
        st.info(f"Processing complete for {file_name}", icon="✅")
        st.balloons()
        logger.info("File processing complete.")


def initialize_session_state():
    """Initialize session state variables if not already set."""
    logger.info("Initializing session state.")
    session_defaults = {
        "selected_model": None,
        "selected_embedding_model": None,
        "uploaded_files": [],
        "processing_status": None,
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            logger.debug(
                f"Initialized session state variable: {key} = {value}")


def configure_llm():
    """Handles LLM provider and model selection."""
    st.sidebar.subheader("LLM Configuration")
    logger.info("Configuring LLM.")

    provider_option = st.sidebar.selectbox(
        "Select Provider",
        options=[provider.value for provider in Provider.llm_providers()],
        index=0,
    )
    selected_provider = Provider(provider_option)
    logger.info(f"Selected LLM provider: {selected_provider}")

    api_key = handle_api_key_input(selected_provider)

    # Model Selection for LLM
    available_models = [
        model for model in Model if model.provider == selected_provider]
    selected_model = st.sidebar.selectbox(
        "Select LLM Model", options=[model.model_name for model in available_models]
    )
    logger.info(f"Selected LLM model: {selected_model}")

    st.session_state["selected_provider"] = selected_provider

    # Store selected model in session state
    st.session_state["selected_model"] = next(
        (m for m in Model if m.model_name == selected_model), None
    )

    return selected_provider, api_key


def configure_embedding(same_provider):
    """Handles Embedding provider and model selection."""
    st.sidebar.subheader("Embedding Configuration")
    logger.info(
        f"Configuring Embedding.  Same provider as LLM: {same_provider}")

    if same_provider:
        selected_embedding_provider = st.session_state["selected_provider"]
        logger.info(
            f"Using same provider for embedding: {selected_embedding_provider}")
    else:
        embedding_provider_option = st.sidebar.selectbox(
            "Select Embedding Provider",
            options=[provider.value for provider in Provider if provider !=
                     st.session_state["selected_provider"]],
            index=0,
        )
        selected_embedding_provider = Provider(embedding_provider_option)
        logger.info(
            f"Selected embedding provider: {selected_embedding_provider}")
        # Ensure API key is handled
        handle_api_key_input(selected_embedding_provider)

    # Embedding Model Selection
    available_embedding_models = [
        model for model in EmbeddingModel if model.provider == selected_embedding_provider]
    selected_embedding_model = st.sidebar.selectbox(
        "Select Embedding Model", options=[model.model_name for model in available_embedding_models]
    )
    logger.info(f"Selected embedding model: {selected_embedding_model}")

    # Store selected embedding model in session state
    st.session_state["selected_embedding_model"] = next(
        (m for m in EmbeddingModel if m.model_name == selected_embedding_model), None
    )


def handle_api_key_input(provider):
    """Handles API key input for a given provider."""
    logger.info(f"Handling API key input for provider: {provider}")
    if provider in {Provider.OPENAI, Provider.GOOGLE, Provider.HUGGINGFACE, Provider.MISTRAL}:
        api_key_name = provider.api_key_env_var
        api_key = st.sidebar.text_input(
            f"Enter {api_key_name}", type="password")
        if api_key:
            os.environ[api_key_name] = api_key
            logger.info(f"Set environment variable: {api_key_name}")
        else:
            logger.warning(f"No API Key provided for {provider}")
        return api_key
    elif provider == Provider.OLLAMA:
        ollama_host = st.sidebar.text_input(
            "Enter Ollama Host URL (http://localhost:11434)")
        if ollama_host:
            os.environ["OLLAMA_HOST"] = ollama_host
            logger.info(
                f"Set environment variable: OLLAMA_HOST to {ollama_host}")
        else:
            logger.warning("No Ollama host was provided")
        return ollama_host
    else:
        logger.warning(
            f"API key handling not implemented for provider: {provider}")
        return None


@st.dialog(title="Upload Knowledge", width="large")
def handle_file_upload(canvas: LearningCanvas):
    """Handles file upload functionality."""
    logger.info("Handling file upload.")

    with st.expander(":file_folder: Upload Documents", expanded=True):
        uploaded_files = st.file_uploader(
            "Upload a document (EPUB, DOCX, PDF)",
            accept_multiple_files=True,
            type=["epub", "docx", "pdf"],
            help="Supports EPUB, DOCX, and PDF formats",
        )

        # If user has uploaded one or more files
        if uploaded_files:
            for uf in uploaded_files:
                # Read the file bytes immediately
                file_data = uf.read()
                # Check if we already have a file with the same name
                existing_names = [f["name"]
                                  for f in st.session_state["uploaded_files"]]
                if uf.name not in existing_names:
                    # Store only serializable data: name + bytes
                    st.session_state["uploaded_files"].append({
                        "name": uf.name,
                        "data": file_data
                    })
                    logger.info(f"Added file to upload queue: {uf.name}")

            if st.session_state["uploaded_files"]:
                st.button(
                    "Process files",
                    on_click=process_uploaded_files,
                    args=(canvas,),
                    use_container_width=True,
                    type="primary"
                )


def handle_build_knowledge_button(canvas):
    """Handles the knowledge-building process button."""
    logger.info("Handling 'Build Knowledge' button.")
    if st.sidebar.button(
        "🚀 Build Knowledge",
        type="primary", use_container_width=True
    ):
        handle_file_upload(canvas)


def sidebar(canvas: "LearningCanvas"):
    """Main sidebar function."""
    st.sidebar.title(":gear: Configuration")
    logger.info("Rendering sidebar.")
    initialize_session_state()

    # Configure LLM and Embedding
    llm_provider, llm_api_key = configure_llm()

    same_provider = st.sidebar.checkbox(
        "Use same provider for LLM & Embedding")

    configure_embedding(same_provider)

    # Handle file upload & processing
    handle_build_knowledge_button(canvas)

    try:
        canvas.set_model(st.session_state["selected_model"],
                         st.session_state["selected_embedding_model"])
    except Exception as e:
        logger.exception(f"Error setting model: {e}")
        # Added error message
        st.error("Error initializing model, check configuration")
