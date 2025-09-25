import streamlit as st # <-- ADD THIS LINE
import os
import json
import re
from datetime import datetime
import pandas as pd
from plotly import io as pio
import plotly.graph_objects as go

CHAT_HISTORY_DIR = "chat_history"

def get_session_id(first_query: str) -> str:
    """Generates a unique session ID from the date and the first user query."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    sanitized_query = re.sub(r'[^\w\s-]', '', first_query).strip()
    sanitized_query = re.sub(r'[-\s]+', '_', sanitized_query).lower()
    query_part = sanitized_query[:40]
    return f"{date_str}_{query_part}"

def save_session(session_id: str, chat_history: list, df_info: dict):
    """Saves the chat history and dataframe info to a JSON file."""
    if not os.path.exists(CHAT_HISTORY_DIR):
        os.makedirs(CHAT_HISTORY_DIR)
    
    serializable_history = []
    for msg in chat_history:
        new_msg = msg.copy()
        content = new_msg.get("content")

        if isinstance(content, dict) and content.get("type") == "plot":
            fig = content.get("data")
            if isinstance(fig, go.Figure):
                content["data"] = pio.to_json(fig)
        
        elif isinstance(content, list) and all(isinstance(item, go.Figure) for item in content):
             new_msg["content"] = [pio.to_json(fig) for fig in content]

        serializable_history.append(new_msg)

    session_data = {
        "chat_history": serializable_history,
        "dataframe_info": df_info
    }
    filepath = os.path.join(CHAT_HISTORY_DIR, f"{session_id}.json")
    with open(filepath, 'w') as f:
        json.dump(session_data, f, indent=4)

def load_session(session_id: str):
    """Loads a chat history and dataframe info from a JSON file."""
    filepath = os.path.join(CHAT_HISTORY_DIR, session_id)
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, 'r') as f:
        session_data = json.load(f)

    loaded_history = session_data.get("chat_history", [])
    for msg in loaded_history:
        content = msg.get("content")
        
        if isinstance(content, dict) and content.get("type") == "plot":
            fig_json = content.get("data")
            if isinstance(fig_json, str):
                content["data"] = pio.from_json(fig_json)
        
        elif isinstance(content, list) and all(isinstance(item, str) for item in content):
            try:
                msg["content"] = [pio.from_json(fig_json) for fig_json in content]
            except Exception:
                pass
                
    return session_data

def list_sessions() -> list:
    """Lists all saved session files, newest first."""
    if not os.path.exists(CHAT_HISTORY_DIR):
        return []
    files = os.listdir(CHAT_HISTORY_DIR)
    json_files = [f for f in files if f.endswith('.json')]
    return sorted(
        json_files,
        key=lambda f: os.path.getmtime(os.path.join(CHAT_HISTORY_DIR, f)),
        reverse=True
    )

def export_chart_to_png_bytes(fig):
    """Exports a Plotly figure to PNG bytes."""
    try:
        return pio.to_image(fig, format='png', engine='kaleido')
    except Exception as e:
        st.error(f"Error exporting chart: {e}")
        return None

def export_chat_to_html(chat_history: list) -> bytes:
    """Exports the entire chat log to a clean HTML string."""
    html = """
    <html><head><title>DataSense AI Chat Export</title><style>
    body { font-family: Arial, sans-serif; background-color: #f8f9fa; color: #212529; padding: 20px; }
    .message-container { margin-bottom: 20px; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .user { background-color: #e9d5ff; border-left: 5px solid #8A2BE2; }
    .assistant { background-color: #ffffff; border-left: 5px solid #5A5A5A; }
    h3 { color: #8A2BE2; margin-top: 0; }
    p { margin-bottom: 0; }
    </style></head><body><h1>DataSense AI Chat Export</h1>
    """
    for msg in chat_history:
        role = msg['role'].capitalize()
        content = msg['content']
        html += f'<div class="message-container {msg["role"]}">'
        html += f'<h3>{role}</h3>'
        if isinstance(content, dict) and content.get("type") == "plot":
            html += "<p><em>[Plot was generated here.]</em></p>"
        elif isinstance(content, list):
            html += "<p><em>[Dashboard was generated here.]</em></p>"
        else:
            html += f'<p>{str(content)}</p>'
        html += '</div>'
    html += "</body></html>"
    return html.encode('utf-8')