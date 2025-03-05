import streamlit as st
import logging

from learning_canvas import LearningCanvas
from core.config_manager import ConfigManager

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



def render_advanced_configuration(config_manager: ConfigManager):
    """Renders the advanced configuration interface with multiple sections."""
    st.title("⚙️ Neuro Trail Configuration")

    # Configuration tabs
    config_tabs = st.tabs(
        ["🤖 LLM", "🧠 Embeddings", "🔄 Vector Store", "🗄️ Neo4j", "📚 Knowledge Base"])

    # 1. LLM Configuration
    with config_tabs[0]:
        st.subheader("Language Model Configuration")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.session_state.llm_provider = st.selectbox(
                "LLM Provider",
                options=["ollama", "openai", "google",
                         "mistral", "huggingface"],
                index=["ollama", "openai", "google", "mistral",
                       "huggingface"].index(st.session_state.llm_provider),
                help="Provider for the language model"
            )

            st.session_state.llm_model = st.text_input(
                "Model Name",
                value=st.session_state.llm_model,
                help="Name/ID of the specific model"
            )

        with col2:
            if st.session_state.llm_provider.lower() in ["openai", "google", "mistral", "huggingface"]:
                st.session_state.llm_api_key = st.text_input(
                    f"{st.session_state.llm_provider.capitalize()} API Key",
                    type="password",
                    value=st.session_state.llm_api_key,
                    help="API key for accessing the service"
                )
            else:  # Ollama
                st.session_state.llm_base_url = st.text_input(
                    "Ollama Host URL",
                    value=st.session_state.llm_base_url,
                    help="URL for Ollama server"
                )

            st.session_state.llm_temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.llm_temperature),
                step=0.1,
                help="Controls randomness in responses (0 = deterministic, 1 = creative)"
            )

            st.session_state.llm_max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=8000,
                value=int(st.session_state.llm_max_tokens),
                step=100,
                
                help="Maximum length of generated responses"
            )
        save_configuration(config_manager=config_manager)


    # 2. Embeddings Configuration
    with config_tabs[1]:
        st.subheader("Embedding Model Configuration")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.session_state.embedder_provider = st.selectbox(
                "Embedder Provider",
                options=["ollama", "openai", "google",
                         "mistral", "huggingface", "jina_ai"],
                index=["ollama", "openai", "google", "mistral", "huggingface", "jina_ai"].index(
                    st.session_state.embedder_provider if st.session_state.embedder_provider in
                    ["ollama", "openai", "google", "mistral", "huggingface", "jina_ai"] else "ollama"
                ),
                help="Provider for text embeddings"
            )

            st.session_state.embedder_model = st.text_input(
                "Embedder Model",
                value=st.session_state.embedder_model,
                help="Name of the embedding model"
            )

        with col2:
            st.session_state.embedder_base_url = st.text_input(
                "Embedder Base URL",
                value=st.session_state.embedder_base_url,
                help="Base URL for the embedding service (mainly for Ollama)"
            )

            if st.session_state.embedder_provider.lower() in ["openai", "google", "mistral", "huggingface"]:
                st.session_state.vector_store_embedding_provider_api_key = st.text_input(
                    f"{st.session_state.embedder_provider.capitalize()} API Key",
                    type="password",
                    value=st.session_state.vector_store_embedding_provider_api_key,
                    help="API key for accessing the embedding service"
                )
        save_configuration(config_manager=config_manager)



    # 3. Vector Store Configuration
    with config_tabs[2]:
        st.subheader("Vector Store Configuration")

        st.session_state.vector_store_provider = st.selectbox(
            "Vector Store Provider",
            options=["qdrant", "chroma", "pinecone", "weaviate"],
            index=["qdrant", "chroma", "pinecone", "weaviate"].index(
                st.session_state.vector_store_provider if st.session_state.vector_store_provider in
                ["qdrant", "chroma", "pinecone", "weaviate"] else "qdrant"
            ),
            help="Vector database for storing embeddings"
        )

        st.session_state.vector_store_host = st.text_input(
            "Vector Store Host",
            value=st.session_state.vector_store_host,
            help="Hostname or IP address of the vector store"
        )


        if st.session_state.vector_store_host in ["qdrant", "pinecone", "weaviate"]:
            st.session_state.vector_store_port = st.number_input(
                "Vector Store Port",
                min_value=1,
                value=int(st.session_state.vector_store_port),
                help="Port number for the vector store"
                )
        save_configuration(config_manager=config_manager)


    
    # 4. Neo4j Configuration
    with config_tabs[3]:
        st.subheader("Neo4j Graph Database Configuration")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.session_state.neo4j_uri = st.text_input(
                "Neo4j URI",
                value=st.session_state.neo4j_uri,
                help="URI for connecting to Neo4j (e.g., bolt://localhost:7687)"
            )

        with col2:
            st.session_state.neo4j_user = st.text_input(
                "Neo4j Username",
                value=st.session_state.neo4j_user,
                help="Username for Neo4j authentication"
            )

            st.session_state.neo4j_password = st.text_input(
                "Neo4j Password",
                type="password",
                value=st.session_state.neo4j_password,
                help="Password for Neo4j authentication"
            )
        save_configuration(config_manager=config_manager)

    # 5. Knowledge Base
    with config_tabs[4]:
        st.subheader("Knowledge Base Management")

        # File uploader for documents
        st.markdown("### Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload documents (EPUB, DOCX, PDF)",
            accept_multiple_files=True,
            type=["epub", "docx", "pdf"],
            help="Supports EPUB, DOCX, and PDF formats"
        )

        # Process uploaded files
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

            # Display list of files to process
            if st.session_state["uploaded_files"]:
                st.markdown("### Files Ready to Process")
                for idx, file_info in enumerate(st.session_state["uploaded_files"]):
                    st.text(f"{idx+1}. {file_info['name']}")

                # Process button
                if st.button(
                    "Process Files",
                    type="primary",
                    use_container_width=True
                ):
                    process_uploaded_files(
                        st.session_state.get("_learning_canvas"))

    

def save_configuration(config_manager):
    # Save all configuration changes
    if st.button("Save Configuration", type="primary", use_container_width=True):
        if config_manager.save_configuration():
            st.success("✅ Configuration saved successfully!")
            # Recheck configuration status after saving
            config_manager._check_configuration_status()
            st.toast("Settings updated successfully!", icon="✅")
        else:
            st.error("❌ Failed to save configuration. Please check the logs.")



def configuration_ui(canvas: LearningCanvas):
    """
    Main configuration UI handler that shows either first-time setup
    or advanced configuration based on state.
    """
    # Store canvas reference in session state for callbacks
    st.session_state._learning_canvas = canvas

    # Initialize configuration manager
    config_manager = ConfigManager()

    render_advanced_configuration(config_manager)

    # After configuration is complete, initialize the LearningCanvas with selected models
    if config_manager.is_configured():
        logger.info("Canvas initialized")
        
