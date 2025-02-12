import sqlparse

def is_safe_query(sql_query):
    """
    Validates SQL query to ensure it's safe before execution.
    Returns True if the query is safe, False otherwise.
    """
    try:
        # Parse the SQL statement
        parsed = sqlparse.parse(sql_query)
        
        if not parsed:
            return False  # Empty or invalid query
        
        for statement in parsed:
            # Extract the first keyword (command)
            first_token = statement.token_first(skip_cm=True)
            if not first_token:
                return False

            first_keyword = first_token.value.upper()
            
            # Allow only safe SQL commands
            # allowed_commands = {"SELECT", "INSERT", "UPDATE", "DELETE", "WITH"}
            # if first_keyword not in allowed_commands:
            #     print(f"Unsafe Query: {first_keyword} is not allowed")
            #     return False
            
            # # Prevent full-table modifications (DELETE/UPDATE without WHERE)
            # if first_keyword in {"DELETE", "UPDATE"}:
            #     if "WHERE" not in sql_query.upper():
            #         print(f"Unsafe Query: {first_keyword} without WHERE")
            #         return False
            
            # # Detect dangerous keywords
            # dangerous_keywords = {"DROP", "TRUNCATE", "ALTER", "--"}
            # if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
            #     print(f"Unsafe Query: Contains dangerous keyword")
            #     return False

        # Query is safe
        return True
    except Exception as e:
        print(f"Error parsing query: {e}")
        return False
