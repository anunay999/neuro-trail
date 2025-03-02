import streamlit as st

from learning_canvas import LearningCanvas
from ui.components import chat_ui, sidebar

# Set page config
st.set_page_config(page_title="🧠 Neuro Trail", page_icon="🧠", layout="wide")

if __name__ == "__main__":
    # Sidebar
    #
    learning_canvas = LearningCanvas()
    sidebar(canvas=learning_canvas)

    # Chat UI
    chat_ui(canvas=learning_canvas)
