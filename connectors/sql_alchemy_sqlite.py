from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import CreateTable
from helpers.validation import is_safe_query
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(override=True)

class SqlAlchemySQLite:
    def __init__(self, db_path=None, db_name='students', uploaded_file=None, file_type=None):
        """
        Initializes SQLite connection and automatically loads an uploaded file if provided.

        :param db_path: Directory path for the SQLite database (default: current directory).
        :param db_name: Name of the SQLite database (default: 'students').
        :param uploaded_file: The uploaded file (BytesIO) from Streamlit.
        :param file_type: File type ('excel' or 'csv').
        """
        self.current_directory = Path.cwd()
        self.db_path = db_path or os.getenv("SQLITE_DB_PATH", str(self.current_directory))
        self.db_name = db_name
        self.connection_string = f"sqlite:///{self.db_path}/{self.db_name}.db"
        self.table_name = self.db_name  # Table name is same as the database name

        try:
            self.engine = create_engine(self.connection_string)
            self.base = declarative_base()
        except Exception as e:
            raise ConnectionError(f"Failed to create SQLAlchemy engine: {e}")

        # Automatically load file if provided
        if uploaded_file and file_type:
            self.load_uploaded_file_to_sqlite(uploaded_file, file_type)

    def load_uploaded_file_to_sqlite(self, file, file_type):
        """
        Loads an uploaded Excel or CSV file directly into SQLite, using the database name as the table name.

        :param file: Uploaded file object (BytesIO).
        :param file_type: File type ('excel' or 'csv').
        """
        try:
            if file_type.lower() == 'excel':
                df = pd.read_excel(file)
            elif file_type.lower() == 'csv':
                df = pd.read_csv(file)
            else:
                raise ValueError("Unsupported file type. Use 'excel' or 'csv'.")

            df.to_sql(self.table_name, con=self.engine, if_exists='replace', index=False)
            print(f"Data successfully loaded into '{self.table_name}'.")
        except Exception as e:
            print(f"Error loading file into SQLite: {e}")

    def run_query(self, query):
        """
        Runs a given SQL query on the SQLite database.

        :param query: SQL query string.
        :return: Query results as a Pandas DataFrame or error message.
        """
        try:
            if not is_safe_query(query):
                return "Query blocked: Potentially unsafe SQL detected."

            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                if query.strip().lower().startswith("select"):
                    data = result.fetchall()
                    return pd.DataFrame(data, columns=result.keys()) if data else "No data found."
                else:
                    return "Query executed successfully."
        except Exception as e:
            return f"An error occurred: {e}"

    def show_db_schema(self):
        """
        Retrieves and returns the database schema information.

        :return: Database schema as a formatted string.
        """
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            schema_info = ""
            for table in tables:
                columns = inspector.get_columns(table)
                schema_info += f"Table: {table.upper()}\n"
                for column in columns:
                    schema_info += f"  Column: {column['name']}, Type: {column['type']}\n"
                schema_info += "\n"
            return schema_info
        except Exception as e:
            return f"Error retrieving schema: {e}"

    def get_db_schema(self, sample_rows=3, include_indexes=False):
        """
        Retrieves detailed database schema, including table structures and sample data.

        :param sample_rows: Number of sample rows to display (default: 3).
        :param include_indexes: Whether to include index information (default: False).
        :return: Database schema as a formatted string.
        """
        try:
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            schema_info = ""
            
            for table in metadata.sorted_tables:
                if table.name.startswith("sqlite_"):
                    continue
                
                create_table_stmt = str(CreateTable(table).compile(self.engine))
                schema_info += create_table_stmt + "\n"
                
                if include_indexes:
                    indexes = self.engine.execute(f"PRAGMA index_list({table.name})").fetchall()
                    schema_info += "Indexes:\n" + "\n".join([f"  {idx[1]} (Unique: {idx[2]})" for idx in indexes]) + "\n"
                
                if sample_rows > 0:
                    schema_info += "Sample Rows:\n" + str(self.get_sample_rows(table.name, sample_rows)) + "\n"
            
            return schema_info
        except Exception as e:
            return f"Error retrieving DB schema: {e}"