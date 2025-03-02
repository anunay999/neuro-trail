import streamlit as st

from learning_canvas import LearningCanvas


def chat_ui(canvas: LearningCanvas):
    st.title("Neuro Trail 🧠 - Memory Augmented Learning")

    # Check if a model is selected
    if "selected_model" not in st.session_state:
        st.warning("⚠️ Please configure the model provider in the sidebar.")
        st.stop()

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Chat input
    user_input = st.chat_input("Ask me anything..")

    if user_input:
        # Query model
        with st.spinner("Generating response..."):
            response = canvas.answer_query(user_input)

        # Update chat history
        st.session_state["chat_history"].append(
            {"role": "user", "content": user_input})
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": response}
        )

    # Display chat history
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
