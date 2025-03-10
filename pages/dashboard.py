import streamlit as st
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
from connectors.sql_alchemy import SqlAlchemy
from connectors.sql_alchemy_sqlite import SqlAlchemySQLite
from helpers.config_store import load_from_env
from helpers.css_settings import custom_css
from dashboard_integration import create_dashboard_page

def main():
    load_dotenv(override=True)
    
    st.set_page_config(page_title="DocGene - Analytics Dashboard", page_icon="assets/logo.png", layout="wide")
    st.markdown(custom_css, unsafe_allow_html=True)
    
    # Initialize session state
    if "config" not in st.session_state:
        st.session_state["config"] = load_from_env()
    
    # Initialize database connection
    try:
        # Check if we're using SQLite or another database
        if "SQLITE_DB_DRIVER" in st.session_state["config"] and st.session_state["config"]["SQLITE_DB_DRIVER"] == "sqlite":
            sql_alchemy = SqlAlchemySQLite(
                db_path=st.session_state.config["SQLITE_DB_PATH"],
                db_name=st.session_state.config["SQLITE_DB_NAME"]
            )
        else:
            sql_alchemy = SqlAlchemy()
        
        # Create the dashboard interface
        create_dashboard_page(st, sql_alchemy)
        
    except Exception as e:
        st.error(f"Failed to initialize dashboard: {e}")

if __name__ == "__main__":
    main()