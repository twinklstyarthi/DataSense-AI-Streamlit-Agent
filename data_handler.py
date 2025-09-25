import pandas as pd
import streamlit as st
from ydata_profiling import ProfileReport

@st.cache_data(show_spinner="Loading data...")
def load_data(uploaded_file):
    """Loads data from a CSV or Excel file, handling multiple sheets."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            return {"data": df}
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            if not sheet_names:
                st.error("Excel file contains no sheets.")
                return None
            return {sheet: pd.read_excel(xls, sheet) for sheet in sheet_names}
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def generate_eda_report(df: pd.DataFrame):
    """Generates a comprehensive EDA report using ydata-profiling."""
    if df is not None:
        try:
            profile = ProfileReport(df,
                title="DataSense AI: Data Profile Report",
                explorative=True,
                dark_mode=False,
                minimal=False
            )
            return profile
        except Exception as e:
            st.error(f"Error generating EDA report: {e}")
            return None
    return None