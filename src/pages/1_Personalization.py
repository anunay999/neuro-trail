import logging

import streamlit as st

from core.prompt_templates import prompt_template_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


st.title("🎨 Personalization Settings")

# Create columns to organize the UI

# Response style settings
# Get all templates
templates = prompt_template_manager.get_all_templates()
template_options = {tid: t["name"] for tid, t in templates.items()}

# Get current active template
active_template = prompt_template_manager.get_active_template_id()

# Allow user to select a template
selected_template = st.selectbox(
    "Response Style",
    options=list(template_options.keys()),
    format_func=lambda x: template_options[x],
    index=list(template_options.keys()).index(active_template),
    help="Choose the style of responses",
)

# Update active template if changed
if selected_template != active_template:
    prompt_template_manager.set_active_template(selected_template)
    st.success(f"Updated to {template_options[selected_template]} style")

# Show template description
template = prompt_template_manager.get_template(selected_template)
if template and "description" in template:
    st.info(template["description"])

# Response length slider
if "response_length" not in st.session_state:
    st.session_state["response_length"] = "Balanced"

st.session_state["response_length"] = st.select_slider(
    "Response Length",
    options=["Very Brief", "Brief", "Balanced", "Detailed", "Comprehensive"],
    value=st.session_state["response_length"],
    help="Control how detailed the responses should be",
)

# Create custom template UI
st.subheader("Custom Templates")

create_template = st.checkbox(
    "Create new template",
    value=st.session_state.get("show_template_editor", False),
    key="toggle_template_editor",
)

st.session_state["show_template_editor"] = create_template

if st.session_state.get("show_template_editor", False):
    with st.form("template_form"):
        st.subheader("Custom Template Editor")

        template_name = st.text_input("Template Name", value="My Custom Template")
        template_desc = st.text_area(
            "Description", value="Custom response style", height=70
        )
        template_content = st.text_area(
            "Template Content",
            value="""
                    You are a helpful assistant for the Neuro Trail learning platform.
                    Answer in the following style: {style}
                    Keep your response {length} with detail appropriate for {expertise} level.
                    Goal: {goal}

                    Context: {context}

                    Question: {question}
                                        """,
            height=200,
        )

        template_vars = st.text_input(
            "Template Variables (comma-separated)",
            value="context,question,style,length,expertise,goal",
        )

        submit_template = st.form_submit_button(
            "Save Template", use_container_width=True
        )

        if submit_template:
            # Parse variables
            variables = [v.strip() for v in template_vars.split(",") if v.strip()]

            # Create template
            template_id = prompt_template_manager.create_template(
                name=template_name,
                description=template_desc,
                template=template_content,
                input_variables=variables,
            )

            if template_id:
                # Set as active
                prompt_template_manager.set_active_template(template_id)
                st.success(f"Template '{template_name}' created and activated!")
                st.session_state["show_template_editor"] = False
                st.rerun()
            else:
                st.error("Failed to create template")
