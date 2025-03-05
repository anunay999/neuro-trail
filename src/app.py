import streamlit as st

from learning_canvas import LearningCanvas
from ui.components import chat_ui, configuration_ui, personalization_ui

# Set page config
st.set_page_config(
    page_title="Neuro Trail", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)


if __name__ == "__main__":
    # Initialize learning canvas
    learning_canvas = LearningCanvas()
    
    # Create tabs for configuration, personalization, and chat
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuration", "🎨 Personalization", "💬 Chat"])
    
    with tab1:
        # Configuration UI
        configuration_ui(canvas=learning_canvas)
    
    with tab2:
        # Personalization UI (moved from sidebar)
        personalization_ui()
    
    with tab3:
        # Chat UI - Only enabled if configuration is complete
        if st.session_state.get("config_initialized", False):
            chat_ui(canvas=learning_canvas)
        else:
            st.warning("⚠️ Please complete the configuration in the Configuration tab before using the chat.")
            st.info("Go to the Configuration tab and set up your LLM and embedding models.")