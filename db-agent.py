import streamlit as st
import pandas as pd
from connectors.sql_alchemy import SqlAlchemy
from connectors.sql_alchemy_sqlite import SqlAlchemySQLite  # Import SQLite handler
from textgen.factory import LLMClientFactory

from helpers.query_history import * 
from helpers.config_store import *
from helpers.css_settings import *
from helpers.dp_charts import *
from helpers.supported_models import *
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("application.log"),  
        logging.StreamHandler()  
    ]
)

logger = logging.getLogger(__name__)
logger.info("Logging initialized successfully!")

load_dotenv()

st.set_page_config(page_title="DocGene", page_icon="assets/logo.png")

st.title("Talk to your DB in Natural Language")
st.markdown(custom_css, unsafe_allow_html=True)

with st.sidebar:
    st.page_link('db-agent.py', label='DB Agent', icon='📊')
    st.page_link('pages/ChatBot.py', label='Yet Another ChatBot', icon='🤖')

# Initialize query history in session state
if "query_history" not in st.session_state:
    st.session_state["query_history"] = load_query_history()

if "config" not in st.session_state:
    st.session_state["config"] = load_from_env()

# Handle File Upload
with st.sidebar:
    with st.expander("Import Data From Excel or CSV"):
        uploaded_file = st.file_uploader("Select Excel or CSV file", type=["xlsx", "xls", "csv"], key="file_upload")
        
        if uploaded_file:
            db_options = ["sqlite"]
            st.session_state.config["SQLITE_DB_DRIVER"] = st.selectbox(
                "SELECT DATABASE:", db_options,
                db_options.index(st.session_state.config["SQLITE_DB_DRIVER"])
            )
            st.session_state.config["SQLITE_DB_PATH"] = st.text_input(
                "DB_PATH:", st.session_state.config["SQLITE_DB_PATH"]
            )
            st.session_state.config["SQLITE_DB_NAME"] = st.text_input(
                "DB_NAME:", st.session_state.config["SQLITE_DB_NAME"]
            )

            if st.button("Save Config"):
                save_to_env(st.session_state["config"])
                st.success("Database configuration saved!")

@st.cache_resource
def get_sqlalchemy_instance(uploaded_file):
    if uploaded_file:
        st.session_state["db_class"] = "sqlite"
        return SqlAlchemySQLite(
            uploaded_file=uploaded_file, 
            file_type="excel", 
            db_path=st.session_state.config["SQLITE_DB_PATH"], 
            db_name=st.session_state.config["SQLITE_DB_NAME"]
        )
    else:
        st.session_state["db_class"] = "generic"
        return SqlAlchemy()  # Default to generic SQLAlchemy class


sql_alchemy = get_sqlalchemy_instance(uploaded_file)

with st.sidebar:
    with st.expander("Database Configuration"):
        db_options = ["postgres", "mysql", "mssql", "oracle"]
        st.session_state.config["DB_DRIVER"] = st.selectbox(
            "SELECT DATABASE:", db_options,
            db_options.index(st.session_state.config["DB_DRIVER"])
        )
        st.session_state.config["DB_HOST"] = st.text_input("DB_HOST:", st.session_state.config["DB_HOST"])
        st.session_state.config["DB_PORT"] = st.text_input("DB_PORT:", st.session_state.config["DB_PORT"])
        st.session_state.config["DB_USER"] = st.text_input("DB_USER:", st.session_state.config["DB_USER"])
        st.session_state.config["DB_PASSWORD"] = st.text_input("DB_PASS:", st.session_state.config["DB_PASSWORD"])
        st.session_state.config["DB_NAME"] = st.text_input("DB_NAME:", st.session_state.config["DB_NAME"])

        if st.button("Save DB Config"):
            save_to_env(st.session_state["config"])
            st.success("Database configuration saved!")

    with st.expander("Model Selection"):
        st.session_state["config"] = load_from_env()

    # Dropdown to select the backend
        st.session_state.config["LLM_BACKEND"] = st.selectbox(
            "LLM_BACKEND:", 
            llm_backend, 
            index=llm_backend.index(st.session_state.config.get("LLM_BACKEND", llm_backend[0]))
        )

        # Dynamically update model options based on selected backend
        selected_backend = st.session_state.config["LLM_BACKEND"]
        filtered_model_options = supported_models.get(selected_backend, [])

        # Dropdown to select the model
        st.session_state.config["MODEL"] = st.selectbox(
            "SELECT Model:", 
            filtered_model_options, 
            index=filtered_model_options.index(st.session_state.config.get("MODEL", filtered_model_options[0])) 
            if filtered_model_options else 0
        )

        # Input for API key
        st.session_state.config["LLM_API_KEY"] = st.text_input(
            "API KEY:", 
            value=st.session_state.config.get("LLM_API_KEY", "")
        )
        
        # Input for LLM endpoint
        st.session_state.config["LLM_ENDPOINT"] = st.text_input(
            "LLM_ENDPOINT:", 
            value=st.session_state.config.get("LLM_ENDPOINT", "")
        )
        token_size = st.slider("Total Token", 1024, 2048, 4096)
        
        if st.button("Save LLM Config"):
            save_to_env(st.session_state.config)
            st.success("LLM configuration saved!")

    with st.expander("Show Database Schema"):
        schema_info = sql_alchemy.show_db_schema()
        st.text(schema_info)

    with st.expander("Export Data as Excel file"):
        output_path = st.text_input("Select Output Path:", value=str(Path.cwd()))
        if st.button("Export"):
            result = sql_alchemy.export_to_excel(output_path)
            st.success(result)

# Natural Language Query Input
nl_query = st.text_area("Ask a question about your data:")

if st.button("▶️  Execute"):
    if nl_query:
        model_name = st.session_state.config.get("MODEL")
        backend = st.session_state.config.get("LLM_BACKEND")

        with st.spinner(f"Generating SQL Query using {model_name}"):
            inference_client = LLMClientFactory.get_client(
                backend=backend,
                server_url=st.session_state.config.get("LLM_ENDPOINT"),
                model_name=model_name,
                api_key=st.session_state.config.get("LLM_API_KEY")
            )
            schema_info_detail = sql_alchemy.get_db_schema
            sql_query = inference_client.generate_sql(nl_query, schema_info_detail)  # ✅ Moved here

        if not sql_query:  # ✅ Check if query generation failed
            st.error("SQL Query generation failed. Please try again.")
            st.stop()

        st.text(f"Generated SQL Query: LLM backend {backend} serving {model_name}")
        st.code(sql_query, language="sql")

        # ✅ Ensure query history exists before appending
        if "query_history" not in st.session_state:
            st.session_state.query_history = []
        st.session_state.query_history.append((nl_query, sql_query))
        save_query_history(st.session_state["query_history"])

        with st.spinner(f"Executing SQL on {st.session_state.config['DB_DRIVER']}"):
            query_result = sql_alchemy.run_query(sql_query)

            if isinstance(query_result, str) and "error" in query_result.lower():
                st.error(f"SQL Execution Error: {query_result}")
            else:
                st.success("Query executed successfully!")

                if isinstance(query_result, pd.DataFrame):
                    st.subheader("Query Results")
                    if not query_result.empty:
                        st.dataframe(query_result)
                    else:
                        st.info("Query executed successfully, but no data was returned.")

    else:
        st.warning("Please enter a natural language query.")

display_query_history()
