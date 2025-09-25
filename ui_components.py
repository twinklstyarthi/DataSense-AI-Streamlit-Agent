import streamlit as st
from utils import list_sessions, export_chart_to_png_bytes, export_chat_to_html

def apply_custom_css():
    """Loads and applies the custom CSS."""
    try:
        with open("styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("styles.css not found. App will run with default styling.")

def render_sidebar():
    """Renders the sidebar with session management controls."""
    with st.sidebar:
        st.markdown("## DataSense AI")
        if st.button("➕ New Analysis", use_container_width=True, key="new_analysis"):
            st.session_state.clear()
            st.rerun()

        st.markdown("---")

        # Export chat button
        if st.session_state.get("chat_history"):
            html_bytes = export_chat_to_html(st.session_state.chat_history)
            st.download_button(
                label="Export Chat to HTML",
                data=html_bytes,
                file_name="chat_history.html",
                mime="text/html",
                use_container_width=True
            )

        st.markdown("### Saved Analyses")
        sessions = list_sessions()
        if not sessions:
            st.info("No saved sessions found.")
        
        for session_file in sessions:
            session_name = session_file.replace(".json", "").replace("_", " ").title()
            if st.button(session_name, key=f"load_{session_file}", use_container_width=True):
                st.session_state.session_to_load = session_file
                st.rerun()

# In ui_components.py, replace the entire render_chat_message function with this:
import streamlit as st
from utils import list_sessions, export_chart_to_png_bytes, export_chat_to_html
import plotly.graph_objects as go # Make sure this import is at the top of the file

def render_chat_message(message: dict):
    """Renders a single chat message with the specified card-based design."""
    role = message["role"]
    content = message["content"]
    
    card_class = "user" if role == "user" else "assistant"
    
    with st.container():
        st.markdown(f'<div class="chat-card {card_class}">', unsafe_allow_html=True)
        
        if role == "user":
            st.markdown(f"**You**")
            st.markdown(content)
        else: # Assistant
            st.markdown(f"**DataSense AI**")
            
            if isinstance(content, dict) and content.get("type") == "plot":
                fig = content.get("data")
                
                # --- NEW: Final Safety Check ---
                # This check ensures we only try to render valid Plotly figures.
                if isinstance(fig, go.Figure):
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                    # Add download button for the plot
                    png_bytes = export_chart_to_png_bytes(fig)
                    if png_bytes:
                        st.download_button(
                            label="Download Chart as PNG",
                            data=png_bytes,
                            file_name="chart.png",
                            mime="image/png"
                        )
                else:
                    # If it's not a valid figure, show an error inside the chat.
                    st.error("I was unable to generate a valid plot. Please try rephrasing your request.")

            elif isinstance(content, str):
                st.markdown(content)
            else: # Fallback for other data types, e.g., raw dataframes
                st.write(content)
                
        st.markdown('</div>', unsafe_allow_html=True)
def render_follow_up_buttons(questions: list):
    """Renders follow-up questions as clean, clickable buttons."""
    if questions:
        cols = st.columns(len(questions))
        for i, question in enumerate(questions):
            if cols[i].button(question, use_container_width=True, key=f"follow_up_{i}"):
                st.session_state.prompt_from_follow_up = question
                st.rerun()