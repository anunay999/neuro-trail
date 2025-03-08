import logging

import streamlit as st

from core.learning_canvas import canvas
from core.prompt_templates import prompt_template_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
        expertise=expertise.lower(),
    )

    return formatted_prompt


def chat_ui():
    st.title("Neuro Trail 🧠")
    st.subheader("Memory Augmented Learning")

    if not st.session_state.config_initialized:
        st.warning("⚠️ Please save configuration to interact")
        st.stop()

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # 1) Display all messages in chat history
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 2) This input is automatically pinned to the bottom of the page
    user_input = st.chat_input("Ask me anything...")
    if user_input:
        # Immediately show user’s message
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 3) Stream the assistant’s response
        assistant_message = st.chat_message("assistant")
        assistant_placeholder = assistant_message.empty()

        personalized_prompt = format_prompt_with_personalization(user_input)

        full_response = ""
        for token in canvas.answer_query(personalized_prompt):
            full_response += token
            assistant_placeholder.markdown(full_response)

        # 4) Add assistant’s final response to chat history
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": full_response}
        )

    with st.sidebar:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["chat_error"] = None
            st.rerun()


if __name__ == "__main__":
    # Create tabs for configuration, personalization, and chat
    if st.session_state.get("config_initialized", False):
        chat_ui()
    else:
        st.warning(
            "⚠️ Please complete the configuration in the Configuration tab before using the chat."
        )
        st.info("Go to the Configuration tab and set up your LLM and embedding models.")
