from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import CreateTable
from helpers.validation import is_safe_query
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
import re
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

    @staticmethod
    def clean_column_names(df):
        """
        Cleans column names to be SQL-friendly:
        - Strips leading/trailing spaces
        - Replaces spaces with underscores
        - Removes special characters except underscores
        - Ensures lowercase formatting
        """
        df.columns = [
            re.sub(r'[^a-zA-Z0-9_]', '', col.strip().replace(' ', '_')).lower()
            for col in df.columns
        ]
        return df

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

            # Clean column names
            df = self.clean_column_names(df)

            # Load data into SQLite
            df.to_sql(self.table_name, con=self.engine, if_exists='replace', index=False)
            print(f"Data successfully loaded into '{self.table_name}'.")
        except Exception as e:
            print(f"Error loading file into SQLite: {e}")

    def run_query(self, query):
        """
        Runs a given SQL query on the SQLite database without using a session.

        :param query: SQL query string.
        :return: Query results as a Pandas DataFrame or success/error message.
        """
        try:
            with self.engine.connect() as connection:
                transaction = connection.begin()  # Begin transaction (for non-SELECT queries)
                
                try:
                    result = connection.execute(text(query))

                    if query.strip().lower().startswith("select"):
                        data = result.fetchall()
                        return pd.DataFrame(data, columns=result.keys()) if data else "No data found."
                    
                    else:
                        affected_rows = result.rowcount  # ✅ Get number of rows affected
                        transaction.commit()  # ✅ Commit changes for UPDATE/INSERT/DELETE
                        
                        if affected_rows == 0:
                            message = "Query executed successfully, but no rows were affected."
                            print("Warning:", message)
                            return message
                        
                        message = f"Query executed successfully. Rows affected: {affected_rows}"
                        print(message)
                        return message

                except Exception as inner_e:
                    transaction.rollback()  # ❌ Rollback if error occurs
                    error_message = f"Query execution failed: {inner_e}"
                    print("Error:", error_message)
                    return error_message

        except Exception as e:
            error_message = f"An error occurred: {e}"
            print("Critical Error:", error_message)
            return error_message

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
        
    def show_db_schema_md(self):
        """
        Retrieves and returns the database schema information in Markdown format.

        :return: Database schema as a Markdown formatted string.
        """
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            schema_info = ""

            for table in tables:
                schema_info += f"### Table: `{table.upper()}`\n\n"
                schema_info += "| Column Name | Data Type |\n"
                schema_info += "|------------|----------|\n"

                columns = inspector.get_columns(table)
                for column in columns:
                    schema_info += f"| `{column['name']}` | `{column['type']}` |\n"

                schema_info += "\n"  # Add space between tables

            return schema_info
        except Exception as e:
            return f"**Error retrieving schema:** `{e}`"

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
        
    def export_to_excel(self, output_path=None):
        """
        Exports the SQLite database into an Excel file with each table as a separate sheet.

        :param output_path: The directory where the Excel file will be saved (default: current directory).
        :return: Path to the saved Excel file or an error message.
        """
        try:
            output_path = output_path or self.db_path
            excel_file = os.path.join(output_path, f"{self.db_name}.xlsx")
            inspector = inspect(self.engine)
            table_names = [table for table in inspector.get_table_names() if not table.startswith("sqlite_")]
            
            if not table_names:
                return "No tables found in the database to export."
            
            with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
                for table in table_names:
                    df = pd.read_sql(f"SELECT * FROM {table}", self.engine)
                    df.to_excel(writer, sheet_name=table, index=False)
            
            return f"Database successfully exported to {excel_file}"        
        except Exception as e:
            return f"Error exporting database to Excel: {e}"