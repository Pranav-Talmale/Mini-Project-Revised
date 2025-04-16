from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from connectors.sql_alchemy_sqlite import SqlAlchemySQLite
from textgen.factory import LLMClientFactory
from helpers.query_history import *
from helpers.config_store import *
from helpers.supported_models import *
from pathlib import Path
import socket

load_dotenv(override=True)

app = FastAPI(title="DocGene API", description="API to interact with databases using natural language.")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configurations
db_config = load_from_env()
print(db_config)
query_history = load_query_history()

db_instance = None  # Initialize as None until a file is uploaded

# Models
class QueryRequest(BaseModel):
    question: str

class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, str]

class ChatRequest(BaseModel):
    message: str
    
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # Dummy connection
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

ip = get_local_ip()
print(f"""
      __________________________________________
      ==========================================
      ✅ API is running at: http://{ip}:8000
      
      Enter it when prompted in the DocGene App
      ==========================================
      __________________________________________
      """)

@app.get("/")
def home():
    return {"message": "Welcome to DocGene API"}

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    global db_instance
    file_location = os.path.join("F:\Mini-Project-Revised", file.filename)
    with open(file_location, "wb") as buffer:
        buffer.write(file.file.read())
    
    file_extension = file.filename.split(".")[-1].lower()
    file_type = "excel" if file_extension in ["xls", "xlsx"] else "csv" if file_extension == "csv" else None
    
    if not file_type:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only Excel and CSV files are allowed.")
    
    db_instance = SqlAlchemySQLite(db_path=db_config["SQLITE_DB_PATH"], db_name=db_config["SQLITE_DB_NAME"], uploaded_file=file_location, file_type=file_type)
    
    return {"message": "File uploaded and database initialized successfully", "filename": file.filename}

@app.post("/query")
def execute_query(request: QueryRequest):
    if db_instance is None:
        raise HTTPException(status_code=400, detail="No database available. Please upload a file first.")
    
    schema_info = db_instance.get_db_schema()
    backend = db_config.get("LLM_BACKEND")
    model_name = db_config.get("MODEL")
    inference_client = LLMClientFactory.get_client(
        backend=backend, server_url=db_config.get("LLM_ENDPOINT"), model_name=model_name,
        api_key=db_config.get("LLM_API_KEY"))
    sql_query = inference_client.generate_sql(request.question, schema_info)
    
    if not sql_query:
        raise HTTPException(status_code=400, detail="SQL Query generation failed")
    
    query_result = db_instance.run_query(sql_query)
    query_history.append((request.question, sql_query))
    save_query_history(query_history)
    
    return {"query": sql_query, "result": query_result.to_markdown()}

@app.get("/schema")
def get_schema():
    if db_instance is None:
        raise HTTPException(status_code=400, detail="No database available. Please upload a file first.")
    return {"schema": db_instance.show_db_schema_md()}

@app.post("/config/update")
async def update_config(request: Request):
    body = await request.json()
    print("Received JSON:", body)  # Debugging: Print full request body
    return {"message": "Check logs for JSON"}

@app.get("/export")
def export_data(output_path: Optional[str] = None):
    if db_instance is None:
        raise HTTPException(status_code=400, detail="No database available. Please upload a file first.")
    
    # Set a default path if none provided
    output_path = Path(output_path or (Path.cwd() / "exported_data.xlsx"))

    # Generate the Excel file
    result_path = db_instance.export_to_excel(str(output_path))

    # Check if the file was actually created
    if not Path(result_path).exists():
        raise HTTPException(status_code=500, detail="Failed to export Excel file.")

    # Open file as binary stream for download
    file_stream = open(result_path, "rb")

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{Path(result_path).name}"'
        }
    )

@app.get("/history")
def get_query_history():
    return {"history": query_history}

@app.post("/chat")
async def chat(request: ChatRequest):
    backend = db_config.get("LLM_BACKEND")
    model_name = "gemini-2.0-flash-exp"
    inference_client = LLMClientFactory.get_client(
        backend=backend,
        server_url=db_config.get("LLM_ENDPOINT"),
        model_name=model_name,
        api_key=db_config.get("LLM_API_KEY")
    )
    response = inference_client.generate_generic_response(request.message)
    
    return {"response": response}
