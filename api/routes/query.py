from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from pydantic import BaseModel
from api.middleware.database import get_db, execute_query
import logging

logger = logging.getLogger(__name__)

# Pydantic model for custom queries
class QueryRequest(BaseModel):
    query: str

# Create router
router = APIRouter(tags=["Admin"])

@router.post("/query", response_model=List[Dict[str, Any]])
def execute_custom_query(query_request: QueryRequest, db=Depends(get_db)):
    """Execute a custom SQL query (Note: In production, restrict this endpoint to admins only)"""
    logger.info(f"Executing custom query: {query_request.query}")
    
    # Security check: only allow SELECT queries
    if not query_request.query.strip().lower().startswith("select"):
        logger.warning("Attempted non-SELECT query, blocking request")
        raise HTTPException(status_code=403, detail="Only SELECT queries are allowed")
    
    # Execute the query
    try:
        results = execute_query(query_request.query, db)
        logger.info(f"Custom query executed successfully, returned {len(results) if isinstance(results, list) else 0} results")
        return results
    except Exception as e:
        logger.error(f"Custom query execution failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")

@router.post("/query/explain", response_model=List[Dict[str, Any]])
def explain_query(query_request: QueryRequest, db=Depends(get_db)):
    """Get query execution plan (EXPLAIN) for a SQL query"""
    logger.info(f"Explaining query: {query_request.query}")
    
    # Security check: only allow SELECT queries
    if not query_request.query.strip().lower().startswith("select"):
        logger.warning("Attempted to explain non-SELECT query, blocking request")
        raise HTTPException(status_code=403, detail="Only SELECT queries can be explained")
    
    # Add EXPLAIN to the query
    explain_query = f"EXPLAIN {query_request.query}"
    
    # Execute the EXPLAIN query
    try:
        results = execute_query(explain_query, db)
        logger.info(f"Query explain completed successfully")
        return results
    except Exception as e:
        logger.error(f"Query explain failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Query explain failed: {str(e)}")

@router.post("/query/validate", response_model=Dict[str, Any])
def validate_query(query_request: QueryRequest):
    """Validate SQL query syntax without executing it"""
    logger.info(f"Validating query: {query_request.query}")
    
    # Basic validation: check if query starts with SELECT
    is_select = query_request.query.strip().lower().startswith("select")
    
    # Simple syntax checks
    has_from = "from" in query_request.query.lower()
    has_semicolon = ";" in query_request.query
    
    validation_result = {
        "is_valid": is_select and has_from and not has_semicolon,
        "is_select": is_select,
        "has_from": has_from,
        "has_semicolon": has_semicolon,
        "suggestions": []
    }
    
    # Add suggestions based on validation
    if not is_select:
        validation_result["suggestions"].append("Only SELECT queries are allowed")
    if not has_from:
        validation_result["suggestions"].append("Query should include a FROM clause")
    if has_semicolon:
        validation_result["suggestions"].append("Remove semicolons from the query")
    
    return validation_result