import streamlit as st

from ui.components import chat_ui, sidebar

# Set page config
st.set_page_config(page_title="🧠 Neuro Trail", page_icon="🧠", layout="wide")

if __name__ == "__main__":
    # Sidebar
    sidebar()

    # Chat UI
    chat_ui()
