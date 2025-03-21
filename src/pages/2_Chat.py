import logging
import time

import streamlit as st

from memory import MemoryAugmentedChat, initialize_memory_system

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s"
)
logger = logging.getLogger(__name__)


def initialize_memory_if_needed():
    """Initialize the memory system with a status display if not already done."""
    if "memory_system" not in st.session_state:
        with st.status("Waking up your learning buddy... 🧠", expanded=True) as status:
            # Show fun loading messages
            st.write("Remembering our past conversations... 🔍")
            initialize_memory_system()
            st.write("Getting your personal info ready...")
            time.sleep(1)
            st.write("Almost there! Applying final touches of genius... ✨")
            time.sleep(1)
            status.update(
                label="Brain successfully caffeinated! Ready to go! 🚀",
                state="complete",
                expanded=False,
            )


def setup_welcome_message():
    """Set up the welcome message if chat history is empty."""
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if len(st.session_state["chat_history"]) == 0:
        welcome_message = {
            "role": "assistant",
            "content": "👋 Welcome to Neuro Trail! I'm your learning assistant. You can ask me questions about the documents you've uploaded, and I'll use my memory-augmented capabilities to provide helpful responses.",
        }
        st.session_state.chat_history.append(welcome_message)


def display_chat_history():
    """Display all messages in the chat history."""
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def handle_user_input(memory_system: MemoryAugmentedChat, user_id: str):
    """Process user input and generate response."""
    user_input = st.chat_input("Ask me anything...")
    if user_input:
        # Show user message
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate and display response
        generate_response(memory_system, user_input, user_id)


def generate_response(
    memory_system: MemoryAugmentedChat, user_input: str, user_id: str
):
    """Generate and display the assistant's response."""
    assistant_message = st.chat_message("assistant")
    assistant_placeholder = assistant_message.empty()

    full_response = ""
    with st.spinner("Generating...", show_time=True):
        for token in memory_system.answer_query(user_input, user_id=user_id):
            # for token in canvas.answer_query(user_input, user_id=user_id):
            full_response += token
            assistant_placeholder.markdown(full_response)

        # Add to chat history
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": full_response}
        )


def create_sidebar_controls(memory_system, user_id):
    """Create sidebar with chat controls and learning goals."""
    with st.sidebar:
        # Clear chat button
        if st.button("Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()
        # Learning goals section


def memory_augmented_chat_ui():
    """Enhanced chat UI that leverages the memory system, broken into smaller components."""
    st.title("Neuro Trail 🧠")
    st.subheader("Memory Augmented Learning")

    # Check configuration
    if not st.session_state.get("config_initialized", False):
        st.warning("⚠️ Please save configuration to interact")
        st.stop()

    # Initialize memory if needed
    initialize_memory_if_needed()

    # Get memory system and user ID
    memory_system = st.session_state.memory_system
    user_id = "user_123"

    # Setup welcome message if needed
    setup_welcome_message()

    # Display existing chat history
    display_chat_history()

    # Handle user input and generate response
    handle_user_input(memory_system, user_id)

    # Create sidebar controls
    create_sidebar_controls(memory_system, user_id)


if __name__ == "__main__":
    # Create tabs for configuration, personalization, and chat
    if st.session_state.get("config_initialized", False):
        memory_augmented_chat_ui()
    else:
        st.warning(
            "⚠️ Please complete the configuration in the Configuration tab before using the chat."
        )
        st.info("Go to the Configuration tab and set up your LLM and embedding models.")
