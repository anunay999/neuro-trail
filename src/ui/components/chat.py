import streamlit as st

from llm import get_llm


def chat_ui():
    st.title("🧠 Neuro Trail - Memory Augmented Learning Assistant")

    # Check if a model is selected
    if "selected_model" not in st.session_state:
        st.warning("⚠️ Please configure the model provider in the sidebar.")
        st.stop()

    model = st.session_state["selected_model"]

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Chat input
    user_input = st.chat_input("Ask me anything..")

    if user_input:
        # Get LLM instance
        llm = get_llm(model=model.model_name)

        # Query model
        with st.spinner("Generating response..."):
            response = llm(
                messages=[{"role": "user", "content": user_input}], temperature=0.7
            )

        # Update chat history
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": response}
        )

    # Display chat history
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
