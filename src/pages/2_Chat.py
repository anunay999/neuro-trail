import logging

import streamlit as st

from memory import initialize_memory_system

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Updated chat interface function that uses the memory system
def memory_augmented_chat_ui():
    """Enhanced chat UI that leverages the memory system."""
    st.title("Neuro Trail 🧠")
    st.subheader("Memory Augmented Learning")

    if not st.session_state.get("config_initialized", False):
        st.warning("⚠️ Please save configuration to interact")
        st.stop()

    # Initialize memory system if not already done
    if "memory_system" not in st.session_state:
        initialize_memory_system()

    memory_system = st.session_state.memory_system
    user_id = st.session_state.user_id

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display all messages in chat history
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    user_input = st.chat_input("Ask me anything...")
    if user_input:
        # Immediately show user's message
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Stream the assistant's response using memory-augmented processing
        assistant_message = st.chat_message("assistant")
        assistant_placeholder = assistant_message.empty()

        full_response = ""
        for token in memory_system.answer_query(user_input, user_id=user_id):
            full_response += token
            assistant_placeholder.markdown(full_response)

        # Add assistant's final response to chat history
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": full_response}
        )

    with st.sidebar:
        # Chat controls
        if st.button("Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()

        # Learning goals section
        st.subheader("Learning Goals")

        # Show existing goals
        if st.button("View My Goals", use_container_width=True):
            goals = memory_system.user_memory.get_all_goals(user_id)
            if goals:
                for goal in goals:
                    with st.expander(f"📚 {goal.goal_description} ({goal.completion_percentage:.0f}%)"):
                        st.progress(goal.completion_percentage / 100.0)
                        st.write(f"Status: {goal.status}")
                        st.write("Milestones:")
                        for m in goal.milestones:
                            if m.get("completed"):
                                st.markdown(f"✅ {m.get('description')}")
                            else:
                                st.markdown(f"⬜ {m.get('description')}")
            else:
                st.info("No learning goals set yet.")

        # Create new goal section
        with st.expander("Create New Learning Goal"):
            goal_description = st.text_input("Goal Description")
            milestone1 = st.text_input("Milestone 1")
            milestone2 = st.text_input("Milestone 2", value="")
            milestone3 = st.text_input("Milestone 3", value="")

            milestones = [m for m in [milestone1, milestone2, milestone3] if m]

            if st.button("Create Goal", use_container_width=True) and goal_description:
                memory_system.track_learning_goal(
                    user_id=user_id,
                    goal_description=goal_description,
                    milestones=milestones
                )
                st.success(
                    "Learning goal created! Keep track of your progress here.")


if __name__ == "__main__":
    # Create tabs for configuration, personalization, and chat
    if st.session_state.get("config_initialized", False):
        memory_augmented_chat_ui()
    else:
        st.warning(
            "⚠️ Please complete the configuration in the Configuration tab before using the chat."
        )
        st.info("Go to the Configuration tab and set up your LLM and embedding models.")
