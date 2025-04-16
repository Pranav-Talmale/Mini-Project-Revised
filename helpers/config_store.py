from dotenv import load_dotenv
import os
import streamlit as st
from pathlib import Path


def save_to_env(config):
    env_file = Path(".env")
    with env_file.open("w") as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    

def load_from_env():
    current_directory = Path.cwd()
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file,override=True)
        return {
            "SQLITE_DB_DRIVER": os.getenv("SQLITE_DB_DRIVER",'sqlite'),
            "SQLITE_DB_PATH": os.getenv("SQLITE_DB_PATH", current_directory),
            "SQLITE_DB_NAME": os.getenv("SQLITE_DB_NAME",'students'),
            "DB_DRIVER": os.getenv("DB_DRIVER",'postgres'),
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_PORT": os.getenv("DB_PORT"),
            "LLM_BACKEND": os.getenv("LLM_BACKEND", 'ollama'),
            "LLM": os.getenv("LLM"),
            "LLM_API_KEY": os.getenv("LLM_API_KEY"),
            "LLM_ENDPOINT": os.getenv("LLM_ENDPOINT"),
            "MODEL": os.getenv("MODEL")
        }
    

