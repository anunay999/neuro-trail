import streamlit as st
import requests
import os
import logging
from typing import Dict, Any, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# API URL
API_URL = os.getenv("API_URL", "http://localhost:8000/api")

# Set page config
st.set_page_config(
    page_title="Neuro Trail",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Chat"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "documents" not in st.session_state:
    st.session_state.documents = []
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = None
if "templates" not in st.session_state:
    st.session_state.templates = []
if "config" not in st.session_state:
    st.session_state.config = None
if "api_initialized" not in st.session_state:
    st.session_state.api_initialized = False


# Helper functions for API calls
def api_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make a GET request to the API"""
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API GET error: {e}")
        st.error(f"API error: {str(e)}")
        return {}


def api_post(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make a POST request to the API"""
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API POST error: {e}")
        st.error(f"API error: {str(e)}")
        return {}


def api_put(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make a PUT request to the API"""
    try:
        response = requests.put(f"{API_URL}{endpoint}", json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API PUT error: {e}")
        st.error(f"API error: {str(e)}")
        return {}


def api_delete(endpoint: str) -> bool:
    """Make a DELETE request to the API"""
    try:
        response = requests.delete(f"{API_URL}{endpoint}")
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"API DELETE error: {e}")
        st.error(f"API error: {str(e)}")
        return False


def upload_file(file, endpoint: str) -> Dict[str, Any]:
    """Upload a file to the API"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{API_URL}{endpoint}", files=files)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API upload error: {e}")
        st.error(f"Upload error: {str(e)}")
        return {}


def check_api_connection() -> bool:
    """Check if API is available"""
    try:
        response = requests.get(f"{API_URL}/health")
        return response.status_code == 200
    except:
        return False


# Load initial data
def load_initial_data():
    """Load initial data from API"""
    # Check API connection
    if not check_api_connection():
        st.error("⚠️ Cannot connect to API. Please check if the API is running.")
        st.session_state.api_initialized = False
        return

    # Load config
    config = api_get("/config")
    if config:
        st.session_state.config = config
    
    # Load user preferences
    preferences = api_get("/preferences")
    if preferences:
        st.session_state.user_preferences = preferences
    
    # Load documents
    documents = api_get("/documents")
    if documents:
        st.session_state.documents = documents
    
    # Load templates
    templates = api_get("/templates")
    if templates:
        st.session_state.templates = templates
    
    # API successfully initialized
    st.session_state.api_initialized = True


# Main sidebar
def render_sidebar():
    """Render sidebar with navigation options"""
    st.sidebar.title("🧠 Neuro Trail")
    st.sidebar.subheader("Memory Augmented Learning")
    
    # Navigation
    tabs = ["Chat", "Knowledge Base", "Personalization", "Configuration"]
    st.session_state.active_tab = st.sidebar.radio("Navigation", tabs, index=tabs.index(st.session_state.active_tab))
    
    # API connection status
    api_status = check_api_connection()
    status_color = "green" if api_status else "red"
    status_text = "Connected" if api_status else "Disconnected"
    st.sidebar.markdown(f"API Status: :{status_color}[{status_text}]")
    
    # Reload data button
    if st.sidebar.button("Reload Data"):
        with st.spinner("Reloading data..."):
            load_initial_data()
        st.sidebar.success("Data reloaded")
    
    # Display version info
    st.sidebar.markdown("---")
    st.sidebar.caption("Neuro Trail v0.1.0")


# Chat interface
def render_chat():
    """Render chat interface"""
    st.title("💬 Neuro Trail Chat")
    
    # Conversation selector
    conversations = api_get("/chat/conversations")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        conversation_options = ["New Conversation"] + [
            f"{c.get('title', 'Untitled')} ({c.get('id')})" 
            for c in conversations
        ]
        selected_conversation = st.selectbox(
            "Select Conversation", 
            conversation_options,
            index=0 if not st.session_state.current_conversation_id else 
                  next((i for i, c in enumerate(conversations) 
                        if c.get("id") == st.session_state.current_conversation_id), 0) + 1
        )
    
    with col2:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.current_conversation_id = None
            st.experimental_rerun()
    
    # Get selected conversation ID
    if selected_conversation != "New Conversation":
        conv_id = selected_conversation.split("(")[-1].strip(")")
        
        # Load conversation if changed
        if st.session_state.current_conversation_id != conv_id:
            st.session_state.current_conversation_id = conv_id
            messages = api_get(f"/chat/history/{conv_id}")
            st.session_state.chat_history = messages
    else:
        st.session_state.current_conversation_id = None
        st.session_state.chat_history = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            role = message.get("role", "user")
            with st.chat_message(role):
                st.markdown(message.get("content", ""))
    
    # Chat input
    user_input = st.chat_input("Ask me anything...")
    if user_input:
        # Add user message to UI
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Add to history for display
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Prepare API request
        chat_request = {
            "message": user_input,
            "conversation_id": st.session_state.current_conversation_id
        }
        
        # Send to API
        with st.status("Thinking..."):
            response = api_post("/chat/query", chat_request)
        
        if response:
            # Update conversation ID if new
            if not st.session_state.current_conversation_id:
                st.session_state.current_conversation_id = response.get("conversation_id")
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(response.get("message", "Sorry, I couldn't generate a response."))
            
            # Add to history for display
            st.session_state.chat_history.append({"role": "assistant", "content": response.get("message", "")})
            
            # Show context sources if any
            context_sources = response.get("context_sources", [])
            if context_sources:
                with st.expander("Context Sources"):
                    for i, source in enumerate(context_sources):
                        st.markdown(f"**Source {i+1}:** {source.get('document_name', 'Unknown')}")
                        st.markdown(f"*Excerpt:* {source.get('content', '')}")
                        st.markdown("---")


# Knowledge base interface
def render_knowledge_base():
    """Render knowledge base interface for document upload and management"""
    st.title("📚 Knowledge Base")
    
    # Document upload section
    st.subheader("Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Upload documents (EPUB, DOCX, PDF)",
        accept_multiple_files=True,
        type=["epub", "docx", "pdf"],
        help="Supports EPUB, DOCX, and PDF formats",
    )
    
    if uploaded_files:
        for file in uploaded_files:
            # Create progress bar for each file
            progress_bar = st.progress(0, text=f"Uploading {file.name}...")
            
            # Upload file to API
            response = upload_file(file, "/documents")
            
            if response:
                progress_bar.progress(50, text=f"Processing {file.name}...")
                
                # Wait for processing to complete
                document_id = response.get("id")
                if document_id:
                    # Poll document status
                    status = "processing"
                    for i in range(10):  # Timeout after 10 attempts
                        doc_info = api_get(f"/documents/{document_id}")
                        status = doc_info.get("status")
                        
                        if status == "completed":
                            progress_bar.progress(100, text=f"✅ {file.name} processed successfully")
                            break
                        elif status == "failed":
                            progress_bar.progress(100, text=f"❌ {file.name} processing failed")
                            break
                        
                        # Update progress
                        progress = 50 + (i+1) * 5
                        progress_bar.progress(progress, text=f"Processing {file.name}... ({status})")
                        time.sleep(1)
                        
                    # Refresh documents list
                    st.session_state.documents = api_get("/documents")
                    
    # Display documents
    st.subheader("Your Documents")
    
    # Refresh documents list
    documents = api_get("/documents")
    if documents:
        st.session_state.documents = documents
    
    if not st.session_state.documents:
        st.info("No documents uploaded yet. Upload documents to get started.")
    else:
        # Create tabs for document statuses
        status_tabs = st.tabs(["All", "Completed", "Processing", "Failed"])
        
        with status_tabs[0]:  # All
            for doc in st.session_state.documents:
                render_document_card(doc)
        
        with status_tabs[1]:  # Completed
            completed_docs = [doc for doc in st.session_state.documents if doc.get("status") == "completed"]
            if not completed_docs:
                st.info("No completed documents.")
            else:
                for doc in completed_docs:
                    render_document_card(doc)
        
        with status_tabs[2]:  # Processing
            processing_docs = [doc for doc in st.session_state.documents if doc.get("status") == "processing"]
            if not processing_docs:
                st.info("No documents currently processing.")
            else:
                for doc in processing_docs:
                    render_document_card(doc)
        
        with status_tabs[3]:  # Failed
            failed_docs = [doc for doc in st.session_state.documents if doc.get("status") == "failed"]
            if not failed_docs:
                st.info("No failed documents.")
            else:
                for doc in failed_docs:
                    render_document_card(doc)


def render_document_card(doc):
    """Render a document card"""
    status_emoji = {
        "pending": "⏳",
        "processing": "🔄",
        "completed": "✅",
        "failed": "❌"
    }
    
    status = doc.get("status", "pending")
    filename = doc.get("filename", "Unknown")
    metadata = doc.get("metadata", {})
    
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            file_type = doc.get("file_type", "").lower()
            if file_type == "pdf":
                st.markdown("📄")
            elif file_type == "epub":
                st.markdown("📚")
            elif file_type == "docx":
                st.markdown("📝")
            else:
                st.markdown("📄")
        
        with col2:
            title = metadata.get("title", filename)
            author = metadata.get("author", "Unknown Author")
            st.markdown(f"**{title}**")
            st.caption(f"Author: {author}")
            
            # Display chapters if available
            chapters = metadata.get("chapters", [])
            if chapters and len(chapters) > 0:
                with st.expander(f"Chapters ({len(chapters)})"):
                    chapters_text = "\n".join([f"- {ch.get('title', 'Untitled')}" for ch in chapters[:10]])
                    if len(chapters) > 10:
                        chapters_text += f"\n- ... and {len(chapters) - 10} more"
                    st.markdown(chapters_text)
        
        with col3:
            st.markdown(f"{status_emoji.get(status, '❓')} {status.capitalize()}")
            
            # Display any error message
            if status == "failed":
                error_msg = doc.get("message", "Unknown error")
                st.error(error_msg)
        
        st.markdown("---")


# Personalization interface
def render_personalization():
    """Render personalization interface for user preferences and templates"""
    st.title("🎨 Personalization")
    
    # Load user preferences if not loaded
    if not st.session_state.user_preferences:
        preferences = api_get("/preferences")
        if preferences:
            st.session_state.user_preferences = preferences
    
    # Load templates if not loaded
    if not st.session_state.templates:
        templates = api_get("/templates")
        if templates:
            st.session_state.templates = templates
    
    # Create tabs for different personalization options
    tabs = st.tabs(["Response Style", "Learning Goals", "Templates"])
    
    with tabs[0]:  # Response Style
        st.header("Response Style Preferences")
        
        # Create form for preferences
        with st.form("preferences_form"):
            preferences = st.session_state.user_preferences or {}
            
            # Response style selection
            style_options = ["default", "friendly", "academic", "concise", "socratic", "beginner", "expert"]
            response_style = st.selectbox(
                "Response Style",
                options=style_options,
                index=style_options.index(preferences.get("response_style", "default")),
                help="Choose the style of responses"
            )
            
            # Response length selection
            length_options = ["very_brief", "brief", "balanced", "detailed", "comprehensive"]
            response_length = st.selectbox(
                "Response Length",
                options=length_options,
                index=length_options.index(preferences.get("response_length", "balanced")),
                help="Control how detailed the responses should be"
            )
            
            # Expertise level selection
            expertise_options = ["beginner", "intermediate", "advanced", "expert"]
            expertise_level = st.selectbox(
                "Expertise Level",
                options=expertise_options,
                index=expertise_options.index(preferences.get("expertise_level", "intermediate")),
                help="Set the expertise level for content"
            )
            
            # Submit button
            submit = st.form_submit_button("Save Preferences", use_container_width=True)
            
            if submit:
                # Update preferences
                updated_prefs = {
                    "response_style": response_style,
                    "response_length": response_length,
                    "expertise_level": expertise_level,
                    "active_template_id": preferences.get("active_template_id", "default")
                }
                
                # Send to API
                response = api_put("/preferences", updated_prefs)
                if response:
                    st.session_state.user_preferences = response
                    st.success("Preferences updated successfully!")
    
    with tabs[1]:  # Learning Goals
        st.header("Learning Goals")
        
        # Get user goals
        goals = api_get("/preferences/goals")
        
        # Display current goals
        st.subheader("Your Learning Goals")
        
        if not goals or not goals.get("learning_goals"):
            st.info("You haven't set any learning goals yet.")
        else:
            learning_goals = goals.get("learning_goals", [])
            
            for i, goal in enumerate(learning_goals):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{goal.get('title', 'Untitled Goal')}**")
                        if goal.get("description"):
                            st.caption(goal.get("description"))
                    
                    with col2:
                        progress = goal.get("progress", 0)
                        st.progress(progress / 100)
                        st.caption(f"{progress}% complete")
                    
                    with col3:
                        if goal.get("completed"):
                            st.markdown("✅ Completed")
                        else:
                            st.markdown("🔄 In Progress")
        
        # Add new goal form
        st.subheader("Add New Learning Goal")
        
        with st.form("add_goal_form"):
            goal_title = st.text_input("Goal Title")
            goal_description = st.text_area("Description")
            goal_related = st.text_input("Related Topics (comma separated)")
            
            submit_goal = st.form_submit_button("Add Goal", use_container_width=True)
            
            if submit_goal and goal_title:
                # Prepare goal data
                new_goal = {
                    "title": goal_title,
                    "description": goal_description,
                    "related_topics": [topic.strip() for topic in goal_related.split(",") if topic.strip()],
                    "progress": 0,
                    "completed": False
                }
                
                # Update goals
                updated_goals = goals.copy() if goals else {"learning_goals": []}
                updated_goals["learning_goals"].append(new_goal)
                
                # Send to API
                response = api_put("/preferences/goals", updated_goals)
                if response:
                    st.success("Goal added successfully!")
                    st.experimental_rerun()
    
    with tabs[2]:  # Templates
        st.header("Prompt Templates")
        
        # Display available templates
        templates = st.session_state.templates or []
        
        if not templates:
            st.info("No templates available.")
        else:
            # Group templates by system vs. user
            system_templates = [t for t in templates if t.get("is_system", False)]
            user_templates = [t for t in templates if not t.get("is_system", False)]
            
            # Display active template
            active_template_id = st.session_state.user_preferences.get("active_template_id") if st.session_state.user_preferences else "default"
            active_template = next((t for t in templates if t.get("id") == active_template_id), None)
            
            if active_template:
                st.subheader("Active Template")
                with st.container():
                    st.markdown(f"**{active_template.get('name', 'Unnamed')}**")
                    st.caption(active_template.get("description", ""))
                    with st.expander("Template Content"):
                        st.code(active_template.get("template_content", ""), language="markdown")
            
            # Display system templates
            st.subheader("System Templates")
            for template in system_templates:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{template.get('name', 'Unnamed')}**")
                        st.caption(template.get("description", ""))
                    
                    with col2:
                        # Set active button
                        if template.get("id") != active_template_id:
                            if st.button("Set Active", key=f"set_active_{template.get('id')}"):
                                response = api_post(f"/templates/{template.get('id')}/set-active", {})
                                if response:
                                    # Update active template in preferences
                                    if st.session_state.user_preferences:
                                        st.session_state.user_preferences["active_template_id"] = template.get("id")
                                    st.success(f"Template '{template.get('name')}' set as active")
                                    st.experimental_rerun()
                        else:
                            st.markdown("✓ Active")
                    
                    # Show template content
                    with st.expander("Template Content"):
                        st.code(template.get("template_content", ""), language="markdown")
                    
                    st.markdown("---")
            
            # Display user templates
            if user_templates:
                st.subheader("Your Custom Templates")
                for template in user_templates:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{template.get('name', 'Unnamed')}**")
                            st.caption(template.get("description", ""))
                        
                        with col2:
                            # Set active button
                            if template.get("id") != active_template_id:
                                if st.button("Set Active", key=f"set_active_{template.get('id')}"):
                                    response = api_post(f"/templates/{template.get('id')}/set-active", {})
                                    if response:
                                        # Update active template in preferences
                                        if st.session_state.user_preferences:
                                            st.session_state.user_preferences["active_template_id"] = template.get("id")
                                        st.success(f"Template '{template.get('name')}' set as active")
                                        st.experimental_rerun()
                            else:
                                st.markdown("✓ Active")
                        
                        with col3:
                            # Delete button
                            if st.button("Delete", key=f"delete_{template.get('id')}"):
                                if api_delete(f"/templates/{template.get('id')}"):
                                    # Update templates
                                    st.session_state.templates = [t for t in st.session_state.templates if t.get("id") != template.get("id")]
                                    st.success(f"Template '{template.get('name')}' deleted")
                                    st.experimental_rerun()
                        
                        # Show template content
                        with st.expander("Template Content"):
                            st.code(template.get("template_content", ""), language="markdown")
                        
                        st.markdown("---")
        
        # Create new template form
        st.subheader("Create New Template")
        
        with st.form("create_template_form"):
            template_name = st.text_input("Template Name")
            template_description = st.text_area("Description")
            template_content = st.text_area("Template Content", height=200)
            template_variables = st.text_input("Variables (comma separated)", value="context,question")
            
            st.info("Use variables in your template with curly braces, e.g., {context}, {question}")
            
            submit_template = st.form_submit_button("Create Template", use_container_width=True)
            
            if submit_template and template_name and template_content:
                # Prepare template data
                variables = [var.strip() for var in template_variables.split(",") if var.strip()]
                new_template = {
                    "name": template_name,
                    "description": template_description,
                    "template_content": template_content,
                    "input_variables": variables
                }
                
                # Send to API
                response = api_post("/templates", new_template)
                if response:
                    # Update templates
                    st.session_state.templates.append(response)
                    st.success(f"Template '{template_name}' created successfully!")
                    st.experimental_rerun()


# Configuration interface
def render_configuration():
    """Render configuration interface for system settings"""
    st.title("⚙️ Configuration")
    
    # Load configuration if not loaded
    if not st.session_state.config:
        config = api_get("/config")
        if config:
            st.session_state.config = config
    
    if not st.session_state.config:
        st.error("Could not load configuration. Please check API connection.")
        return
    
    # Check if system is configured
    is_configured = st.session_state.config.get("is_configured", False)
    
    if is_configured:
        st.success("System is configured and ready to use!")
    else:
        st.warning("System needs configuration. Please configure all required components.")
    
    # Create tabs for different configuration sections
    config_tabs = st.tabs(["LLM", "Embeddings", "Vector Store", "Knowledge Graph"])
    
    with config_tabs[0]:  # LLM Configuration
        st.header("Language Model Configuration")
        
        # Get LLM config
        llm_config = st.session_state.config.get("llm", {})
        
        with st.form("llm_config_form"):
            # Provider selection
            providers = ["ollama", "openai", "google", "mistral", "huggingface"]
            llm_provider = st.selectbox(
                "LLM Provider",
                options=providers,
                index=providers.index(llm_config.get("provider", "ollama")),
                help="Provider for the language model"
            )
            
            # Model name
            llm_model = st.text_input(
                "Model Name",
                value=llm_config.get("model", ""),
                help="Name/ID of the specific model"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Temperature
                llm_temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(llm_config.get("temperature", 0.0)),
                    step=0.1,
                    help="Controls randomness in responses (0 = deterministic, 1 = creative)"
                )
            
            with col2:
                # Max tokens
                llm_max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=100,
                    max_value=8000,
                    value=int(llm_config.get("max_tokens", 2000)),
                    step=100,
                    help="Maximum length of generated responses"
                )
            
            # Provider-specific settings
            if llm_provider != "ollama":
                llm_api_key = st.text_input(
                    f"{llm_provider.capitalize()} API Key",
                    type="password",
                    value=llm_config.get("api_key", ""),
                    help="API key for accessing the service"
                )
            else:
                # Ollama host
                llm_base_url = st.text_input(
                    "Ollama Host URL",
                    value=llm_config.get("base_url", "http://localhost:11434"),
                    help="URL for Ollama server"
                )
                # For Ollama we don't use API key
                llm_api_key = ""
            
            # Submit button
            submit_llm = st.form_submit_button("Save LLM Configuration", use_container_width=True)
            
            if submit_llm:
                # Prepare config data
                updated_config = {
                    "provider": llm_provider,
                    "model": llm_model,
                    "temperature": llm_temperature,
                    "max_tokens": llm_max_tokens,
                    "api_key": llm_api_key
                }
                
                # Add base_url for Ollama
                if llm_provider == "ollama":
                    updated_config["base_url"] = llm_base_url
                
                # Send to API
                response = api_put("/config/llm", updated_config)
                if response:
                    # Update config
                    if st.session_state.config:
                        st.session_state.config["llm"] = response
                    st.success("LLM configuration updated successfully!")
    
    with config_tabs[1]:  # Embeddings Configuration
        st.header("Embedding Model Configuration")
        
        # Get embedding config
        embedding_config = st.session_state.config.get("embedding", {})
        
        with st.form("embedding_config_form"):
            # Provider selection
            providers = ["ollama", "openai", "google", "mistral", "huggingface", "jina_ai"]
            embedder_provider = st.selectbox(
                "Embedding Provider",
                options=providers,
                index=providers.index(embedding_config.get("provider", "ollama")),
                help="Provider for text embeddings"
            )
            
            # Model name
            embedder_model = st.text_input(
                "Embedding Model",
                value=embedding_config.get("model", ""),
                help="Name of the embedding model"
            )
            
            # Provider-specific settings
            if embedder_provider != "ollama":
                embedder_api_key = st.text_input(
                    f"{embedder_provider.capitalize()} API Key",
                    type="password",
                    value=embedding_config.get("api_key", ""),
                    help="API key for accessing the embedding service"
                )
            else:
                # Ollama host
                embedder_base_url = st.text_input(
                    "Embedding Base URL",
                    value=embedding_config.get("base_url", "http://localhost:11434"),
                    help="URL for embedding service (mainly for Ollama)"
                )
                # For Ollama we don't use API key
                embedder_api_key = ""
            
            # Submit button
            submit_embedding = st.form_submit_button("Save Embedding Configuration", use_container_width=True)
            
            if submit_embedding:
                # Prepare config data
                updated_config = {
                    "provider": embedder_provider,
                    "model": embedder_model,
                    "api_key": embedder_api_key
                }
                
                # Add base_url for Ollama
                if embedder_provider == "ollama":
                    updated_config["base_url"] = embedder_base_url
                
                # Send to API
                response = api_put("/config/embedding", updated_config)
                if response:
                    # Update config
                    if st.session_state.config:
                        st.session_state.config["embedding"] = response
                    st.success("Embedding configuration updated successfully!")
    
    with config_tabs[2]:  # Vector Store Configuration
        st.header("Vector Store Configuration")
        
        # Get vector store config
        vector_store_config = st.session_state.config.get("vector_store", {})
        
        with st.form("vector_store_config_form"):
            # Provider selection
            providers = ["qdrant", "chroma", "pinecone", "weaviate"]
            vs_provider = st.selectbox(
                "Vector Store Provider",
                options=providers,
                index=providers.index(vector_store_config.get("provider", "chroma")),
                help="Vector database for storing embeddings"
            )
            
            # Host and port
            vs_host = st.text_input(
                "Vector Store Host",
                value=vector_store_config.get("host", "localhost"),
                help="Hostname or IP address of the vector store"
            )
            
            vs_port = st.number_input(
                "Vector Store Port",
                min_value=1,
                max_value=65535,
                value=int(vector_store_config.get("port", 6333)),
                help="Port number for the vector store"
            )
            
            # Collection names
            col1, col2 = st.columns(2)
            
            with col1:
                vs_collection = st.text_input(
                    "Knowledge Collection",
                    value=vector_store_config.get("collection_name", "knowledge"),
                    help="Collection name for document knowledge"
                )
            
            with col2:
                vs_user_collection = st.text_input(
                    "User Collection",
                    value=vector_store_config.get("user_collection_name", "user"),
                    help="Collection name for user data"
                )
            
            # Submit button
            submit_vs = st.form_submit_button("Save Vector Store Configuration", use_container_width=True)
            
            if submit_vs:
                # Prepare config data
                updated_config = {
                    "provider": vs_provider,
                    "host": vs_host,
                    "port": vs_port,
                    "collection_name": vs_collection,
                    "user_collection_name": vs_user_collection
                }
                
                # Send to API
                response = api_put("/config/vector-store", updated_config)
                if response:
                    # Update config
                    if st.session_state.config:
                        st.session_state.config["vector_store"] = response
                    st.success("Vector store configuration updated successfully!")
    
    with config_tabs[3]:  # Knowledge Graph Configuration
        st.header("Knowledge Graph Configuration")
        
        # Get knowledge graph config
        kg_config = st.session_state.config.get("knowledge_graph", {})
        
        with st.form("kg_config_form"):
            # Neo4j connection settings
            kg_uri = st.text_input(
                "Neo4j URI",
                value=kg_config.get("uri", "bolt://localhost:7687"),
                help="URI for connecting to Neo4j (e.g., bolt://localhost:7687)"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                kg_user = st.text_input(
                    "Neo4j Username",
                    value=kg_config.get("user", "neo4j"),
                    help="Username for Neo4j authentication"
                )
            
            with col2:
                kg_password = st.text_input(
                    "Neo4j Password",
                    type="password",
                    value=kg_config.get("password", ""),
                    help="Password for Neo4j authentication"
                )
            
            # Submit button
            submit_kg = st.form_submit_button("Save Knowledge Graph Configuration", use_container_width=True)
            
            if submit_kg:
                # Prepare config data
                updated_config = {
                    "provider": "neo4j",  # Only support Neo4j for now
                    "uri": kg_uri,
                    "user": kg_user,
                    "password": kg_password
                }
                
                # Send to API
                response = api_put("/config/knowledge-graph", updated_config)
                if response:
                    # Update config
                    if st.session_state.config:
                        st.session_state.config["knowledge_graph"] = response
                    st.success("Knowledge graph configuration updated successfully!")


# Main app
def main():
    """Main application function"""
    # Render sidebar
    render_sidebar()
    
    # Try to load initial data if not done yet
    if not st.session_state.api_initialized:
        with st.spinner("Loading initial data..."):
            load_initial_data()
    
    # Render active tab
    if st.session_state.active_tab == "Chat":
        render_chat()
    elif st.session_state.active_tab == "Knowledge Base":
        render_knowledge_base()
    elif st.session_state.active_tab == "Personalization":
        render_personalization()
    elif st.session_state.active_tab == "Configuration":
        render_configuration()


if __name__ == "__main__":
    main()