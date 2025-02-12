from .base import TextGenBase
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GoogleGeminiClient(TextGenBase):

    def construct_sql_payload(self, user_question, db_schema):
        
        prompt = f"""You are a SQL expert working with a SQLite database. 
        Given the following table schema, generate a correct, safe, and structured SQL query for the user's request.

        ### IMPORTANT:
        - If the query involves **UPDATE** or **DELETE**, use **WHERE** clauses to prevent modifying all records.
        - If **joining multiple tables**, use **Common Table Expressions (CTEs)**.
        - Always use **WHERE** conditions to avoid modifying all rows in UPDATE/DELETE.
        - If **joins** are needed, infer relationships between tables logically.
        - **For nested queries**, always ensure that subqueries return a valid dataset.
        - Always return the query inside SQL markdown format.

        - Do **not** explain your answer.

        **User Question:** {user_question}
        **Table Schema:** 
        {db_schema}
        SQL Query:
        """
        
        return prompt
    
    def construct_generic_payload(self, user_question):
        return user_question

    def generate_sql(self, user_question, db_schema):
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(self.construct_sql_payload(user_question, db_schema))
    
        parsed_response = self.parse_response(response)  # Get the response text
        return self._extract_sql_statement(parsed_response)  # Extract the SQL statement
    
    def generate_generic_response(self, user_question):
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(user_question)
        return self.parse_response(response)
                

    def parse_response(self, response):
        logger.info(f"Parsing response of {self.model_name} with Google Gemini")
        return response.text
        