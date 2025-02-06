from .base import TextGenBase
import logging

logger = logging.getLogger(__name__)

class OllamaClient(TextGenBase):
    def override_server_url(self, server_url):
        logger.info("Overriding server URL for Ollama")
        return f"http://{server_url}/api/chat"

    def construct_sql_payload(self, user_question, db_schema):
        logger.info("Constructing payload for Ollama")
        
        prompt = f"""You are a SQL expert working with a SQLite database. 
        Given the following table schema, generate a correct, safe, and structured SQL query for the user's request.

        ### IMPORTANT:
        - If the query involves **UPDATE** or **DELETE**, use **WHERE** clauses to prevent modifying all records.
        - If **joining multiple tables**, use **Common Table Expressions (CTEs)**.
        - Always use **WHERE** conditions to avoid modifying all rows in UPDATE/DELETE.
        - If **joins** are needed, infer relationships between tables logically.
        - **For nested queries**, always ensure that subqueries return a valid dataset.
        - Always return the query inside SQL markdown format: 
        sql\n[query]\n

        - Do **not** explain your answer.

        **User Question:** {user_question}
        **Table Schema:** 
        {db_schema}
        SQL Query:
        """
        # prompt = (
        #     "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
        #     f"Generate a SQL query only to answer this question without explanation: `{user_question}`\n"
        #     "considering values like true,TRUE,yes,Yes,YES in a case-insensitive manner.\n"
        #     "considering values like false,FALSE,no,No,NO in a case-insensitive manner.\n"
        #     "DDL statements:\n"
        #     f"{db_schema}<|start_header_id|>assistant<|end_header_id|>\n\n"
        # )
        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0
        }
    def construct_generic_payload(self, user_question):
        prompt = user_question
        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_new_tokens": 4096,
            "max_length": 4096,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
            "stream": False,
            "max_tokens": 1024

        }
        
    def parse_response(self, response):
        logger.info(f"Parsing response for Ollama {response}")
        return response.get('message', {}).get('content', '').strip()
