import streamlit as st
import logging
import uuid
from streamlit.runtime.state import session_state

from learning_canvas import LearningCanvas
from ui.components.prompt_templates import prompt_template_manager

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def initialize_chat_state():
    """Initialize chat-related session state variables if not already set."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str("user1234")
    
    # Typing indicator state
    if "is_typing" not in st.session_state:
        st.session_state["is_typing"] = False
        
    # Error state
    if "chat_error" not in st.session_state:
        st.session_state["chat_error"] = None


def format_prompt_with_personalization(prompt, context=""):
    """Format the user's prompt with personalization settings using the active template."""
    # Get personalization settings from session state
    length = st.session_state.get("response_length", "Balanced")
    expertise = st.session_state.get("expertise_level", "Intermediate")
    
    # Format prompt using template manager
    formatted_prompt = prompt_template_manager.format_prompt(
        context=context,
        question=prompt,
        length=length.lower(),
        expertise=expertise.lower()
    )
    
    return formatted_prompt


def chat_ui(canvas: LearningCanvas):
    """Simplified chat UI with single-line input."""
    # Initialize chat state
    initialize_chat_state()
    
    # Setup the page
    st.title("Neuro Trail 🧠")
    st.subheader("Memory Augmented Learning")
    
    # Check if configuration is complete
    if not st.session_state.get("config_initialized", False):
        st.warning("⚠️ Please complete the configuration before using the chat interface.")
        return
    
    # Add welcome message if this is the first chat interaction
    if not st.session_state["messages"]:
        welcome_message = {
            "role": "assistant", 
            "content": "👋 Welcome to Neuro Trail! I'm your learning assistant. You can ask me questions about the documents you've uploaded, and I'll use my memory-augmented capabilities to provide helpful responses."
        }
        st.chat_message("assistant").markdown(welcome_message["content"])
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": welcome_message["content"]})


    # 2) This input is automatically pinned to the bottom of the page
    if user_input:=st.chat_input("Ask me anything..."):

        st.chat_message("user").markdown(user_input)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        personalized_prompt = format_prompt_with_personalization(user_input)

        full_response = ""
        for token in canvas.answer_query(personalized_prompt):
            full_response += token
            with st.chat_message("assistant"):
                st.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})


    
    with st.sidebar:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["chat_error"] = None
            st.rerun()
