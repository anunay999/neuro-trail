import streamlit as st

from learning_canvas import LearningCanvas


def chat_ui(canvas: LearningCanvas):
    st.title("Neuro Trail 🧠")
    st.subheader("Memory Augmented Learning")

    if "selected_model" not in st.session_state:
        st.warning("⚠️ Please configure the model provider in the sidebar.")
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
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 3) Stream the assistant’s response
        assistant_message = st.chat_message("assistant")
        assistant_placeholder = assistant_message.empty()

        full_response = ""
        for token in canvas.answer_query(user_input):
            full_response += token
            assistant_placeholder.markdown(full_response)

        # 4) Add assistant’s final response to chat history
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": full_response}
        )
