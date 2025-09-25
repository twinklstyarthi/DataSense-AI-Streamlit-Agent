import streamlit as st
import pandas as pd
from ui_components import apply_custom_css, render_sidebar, render_chat_message, render_follow_up_buttons
from data_handler import load_data, generate_eda_report
from llm_agent import DataSenseAgent
from utils import save_session, load_session, get_session_id

# --- Page Config ---
st.set_page_config(page_title="DataSense AI", page_icon="🤖", layout="wide")
apply_custom_css()

# --- Initialize Session State ---
def init_session_state():
    defaults = {
        "chat_history": [], "df": None, "agent": None, "session_id": None,
        "df_info": None, "dashboard_charts": [], "session_to_load": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Session Loading Logic ---
if st.session_state.session_to_load:
    session_data = load_session(st.session_state.session_to_load)
    if session_data:
        st.session_state.chat_history = session_data["chat_history"]
        df_info = session_data["dataframe_info"]
        # Recreate the dataframe from the dictionary
        st.session_state.df = pd.DataFrame.from_dict(df_info)
        st.session_state.agent = DataSenseAgent(st.session_state.df)
        st.session_state.session_id = st.session_state.session_to_load
        st.session_state.dashboard_charts = [
            msg['content'] for msg in st.session_state.chat_history
            if isinstance(msg['content'], list)
        ]
        if st.session_state.dashboard_charts:
            st.session_state.dashboard_charts = st.session_state.dashboard_charts[0]

    st.session_state.session_to_load = None # Reset after loading


# --- UI Rendering ---
render_sidebar()
st.title("🤖 DataSense AI")

# --- Main App Flow ---
if st.session_state.df is None:
    uploaded_file = st.file_uploader(
        "Upload your structured data (CSV/Excel)", type=["csv", "xls", "xlsx"]
    )
    if uploaded_file:
        data_sheets = load_data(uploaded_file)
        if data_sheets:
            if len(data_sheets) > 1:
                sheet_name = st.selectbox("Multiple sheets found. Please select one:", list(data_sheets.keys()))
                if st.button("Confirm Sheet"):
                    st.session_state.df = data_sheets[sheet_name]
                    st.rerun()
            else:
                st.session_state.df = list(data_sheets.values())[0]
                st.rerun()
else:
    # --- Main Interface with Tabs ---
    st.session_state.agent = DataSenseAgent(st.session_state.df)
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "🗂️ Data View", "📊 Dashboard"])

    with tab2:
        st.dataframe(st.session_state.df)
        if st.button("Generate Data Profile"):
            with st.spinner("Profiling data... This may take a moment."):
                profile = generate_eda_report(st.session_state.df)
                if profile:
                    #st.components.v1.html(profile.to_html(), height=800, scrolling=True)
                    #st.html(profile.to_html(), height=800, scroll=True)
                    report_html = profile.to_html()
                    st.html(f'<div style="height:800px; overflow-y: scroll;">{report_html}</div>')

    with tab3:
        st.subheader("Dashboard")
        if not st.session_state.dashboard_charts:
            st.info("Ask for a 'dashboard' in the chat to populate this view.")
        else:
            charts = st.session_state.dashboard_charts
            if isinstance(charts, list):
                cols = st.columns(2)
                for i, fig in enumerate(charts):
                    cols[i % 2].plotly_chart(fig, use_container_width=True)
            else: # Handle single plot case if needed
                st.plotly_chart(charts, use_container_width=True)

    with tab1:
        for message in st.session_state.chat_history:
            render_chat_message(message)

        prompt = st.chat_input("Ask about your data...")
        if "prompt_from_follow_up" in st.session_state and st.session_state.prompt_from_follow_up:
            prompt = st.session_state.prompt_from_follow_up
            st.session_state.prompt_from_follow_up = None

         # Replace the entire 'if prompt:' block in app.py with this one:

        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            render_chat_message(st.session_state.chat_history[-1])

            with st.spinner("Thinking..."):
                # Run the agent
                response = st.session_state.agent.query(prompt)
                st.session_state.last_agent_response = response # Store for follow-ups

                # Prepare the message for display
                response_type = response.get("type")
                content = response.get("content")
                
                assistant_message = {"role": "assistant"}

                if response_type == "dashboard":
                    st.session_state.dashboard_charts = content
                    # Create a user-friendly message for the chat, as the dashboard is in another tab
                    assistant_message["content"] = f"I've created a dashboard with {len(content)} charts. You can view it in the '📊 Dashboard' tab."
                else:
                    assistant_message["content"] = content

                st.session_state.chat_history.append(assistant_message)
                
                # --- Session Saving Logic ---
                if not st.session_state.session_id:
                    st.session_state.session_id = get_session_id(prompt)
                    st.session_state.df_info = st.session_state.df.to_dict()
                
                save_session(
                    st.session_state.session_id,
                    st.session_state.chat_history,
                    st.session_state.df_info
                )
            
            # Rerun to display the new messages and follow-up buttons
            st.rerun()
        # Display follow-up questions from the last response if they exist
        last_message = st.session_state.chat_history[-1] if st.session_state.chat_history else {}
        if last_message.get("role") == "assistant":
            # Check if the agent's response object is stored with the message
            # This requires modifying how we store responses if we want to persist follow-ups
            # For simplicity, we'll assume the follow-ups are tied to the last agent call
            if 'last_agent_response' in st.session_state:
                 render_follow_up_buttons(st.session_state.last_agent_response.get("follow_up_questions", []))

# We need to store the last agent response to render follow-ups after a rerun
if 'response' in locals() and response:
    st.session_state.last_agent_response = response