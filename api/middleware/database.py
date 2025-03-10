from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pandas as pd
from fastapi import HTTPException
import logging

# Load environment variables
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Database connection settings
DB_DRIVER = os.getenv("SQLITE_DB_DRIVER", "sqlite")
DB_PATH = os.getenv("SQLITE_DB_PATH", ".")
DB_NAME = os.getenv("SQLITE_DB_NAME", "students")

# Configure database connection
if DB_DRIVER == "sqlite":
    DATABASE_URL = f"sqlite:///{DB_PATH}/{DB_NAME}.db"
else:
    # Support for other database types could be added here
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    
    if DB_DRIVER == "postgres":
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif DB_DRIVER == "mysql":
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Default to SQLite if unsupported driver
        logger.warning(f"Unsupported database driver: {DB_DRIVER}. Falling back to SQLite.")
        DATABASE_URL = f"sqlite:///{DB_PATH}/{DB_NAME}.db"

# Create SQLAlchemy engine and session factory
try:
    logger.info(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("Database connection established successfully")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    raise Exception(f"Database connection error: {e}")

# Function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to execute raw SQL queries safely
def execute_query(query: str, db):
    """
    Execute SQL queries and return results in a standardized format.
    For SELECT queries, returns a list of dictionaries.
    For other queries, returns a message.
    """
    try:
        logger.debug(f"Executing query: {query}")
        result = db.execute(text(query))
        
        if query.strip().lower().startswith("select"):
            data = result.fetchall()
            if not data:
                logger.info("Query returned no data")
                return []
            
            # Convert to DataFrame and then to dict
            df = pd.DataFrame(data, columns=result.keys())
            return df.to_dict(orient="records")
        else:
            db.commit()
            affected_rows = result.rowcount if hasattr(result, 'rowcount') else 0
            logger.info(f"Query executed successfully. Affected rows: {affected_rows}")
            return {"message": f"Query executed successfully", "affected_rows": affected_rows}
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Function to sanitize input for SQL queries
def sanitize_input(value):
    """
    Sanitize input to prevent SQL injection.
    This is a basic implementation - a more comprehensive solution would be preferred in production.
    """
    if value is None:
        return "NULL"
    
    if isinstance(value, (int, float)):
        return str(value)
    
    # Escape single quotes and remove potentially dangerous characters
    return value.replace("'", "''").replace(";", "")

# Connection testing function
def test_connection():
    """Test database connection and return status"""
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).fetchone()
        db.close()
        return {"status": "connected", "details": "Successfully connected to database"}
    except Exception as e:
        return {"status": "error", "details": str(e)}