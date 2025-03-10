from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from api.middleware.database import get_db, execute_query
import logging

logger = logging.getLogger(__name__)

# Pydantic model for subject data
class Subject(BaseModel):
    subject_code: str
    subject_name: str
    subject_type: str
    credits: Optional[int] = None
    department: Optional[str] = None
    semester: Optional[int] = None

# Create router
router = APIRouter(tags=["Subjects"])

@router.get("/subjects", response_model=List[Dict[str, Any]])
def get_subjects(
    db=Depends(get_db),
    subject_type: Optional[str] = Query(None, description="Filter by subject type"),
    semester: Optional[int] = Query(None, description="Filter by semester")
):
    """Get all subjects with optional filtering"""
    logger.info(f"Getting subjects with filters: subject_type={subject_type}, semester={semester}")
    
    query = "SELECT * FROM subjects WHERE 1=1"
    
    if subject_type:
        query += f" AND subject_type = '{subject_type}'"
    if semester:
        query += f" AND semester = {semester}"
    
    return execute_query(query, db)

@router.get("/subjects/{subject_code}", response_model=Dict[str, Any])
def get_subject(subject_code: str = Path(..., description="Subject code"), db=Depends(get_db)):
    """Get details of a specific subject by code"""
    logger.info(f"Getting subject with code: {subject_code}")
    
    query = f"SELECT * FROM subjects WHERE subject_code = '{subject_code}'"
    results = execute_query(query, db)
    
    if isinstance(results, dict) and "message" in results:
        logger.warning(f"Subject with code {subject_code} not found")
        raise HTTPException(status_code=404, detail=f"Subject with code {subject_code} not found")
    
    if not results:
        logger.warning(f"Subject with code {subject_code} not found")
        raise HTTPException(status_code=404, detail=f"Subject with code {subject_code} not found")
    
    return results[0]

@router.post("/subjects", response_model=Dict[str, Any])
def create_subject(subject: Subject, db=Depends(get_db)):
    """Create a new subject"""
    logger.info(f"Creating new subject with code: {subject.subject_code}")
    
    # Check if subject already exists
    check_query = f"SELECT COUNT(*) as count FROM subjects WHERE subject_code = '{subject.subject_code}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] > 0:
        logger.warning(f"Subject with code {subject.subject_code} already exists")
        raise HTTPException(status_code=409, detail=f"Subject with code {subject.subject_code} already exists")
    
    # Create subject
    query = f"""
    INSERT INTO subjects (subject_code, subject_name, subject_type, credits, department, semester)
    VALUES (
        '{subject.subject_code}',
        '{subject.subject_name}',
        '{subject.subject_type}',
        {subject.credits or "NULL"},
        '{subject.department or ""}',
        {subject.semester or "NULL"}
    )
    """
    
    response = execute_query(query, db)
    logger.info(f"Subject created: {response}")
    return response

@router.put("/subjects/{subject_code}", response_model=Dict[str, Any])
def update_subject(subject_code: str, subject: Subject, db=Depends(get_db)):
    """Update an existing subject"""
    logger.info(f"Updating subject with code: {subject_code}")
    
    # Check if subject exists
    check_query = f"SELECT COUNT(*) as count FROM subjects WHERE subject_code = '{subject_code}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"Subject with code {subject_code} not found for update")
        raise HTTPException(status_code=404, detail=f"Subject with code {subject_code} not found")
    
    # Update subject
    query = f"""
    UPDATE subjects SET
        subject_name = '{subject.subject_name}',
        subject_type = '{subject.subject_type}',
        credits = {subject.credits or "NULL"},
        department = '{subject.department or ""}',
        semester = {subject.semester or "NULL"}
    WHERE subject_code = '{subject_code}'
    """
    
    response = execute_query(query, db)
    logger.info(f"Subject updated: {response}")
    return response

@router.delete("/subjects/{subject_code}", response_model=Dict[str, Any])
def delete_subject(subject_code: str, db=Depends(get_db)):
    """Delete a subject"""
    logger.info(f"Deleting subject with code: {subject_code}")
    
    # Check if subject exists
    check_query = f"SELECT COUNT(*) as count FROM subjects WHERE subject_code = '{subject_code}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"Subject with code {subject_code} not found for deletion")
        raise HTTPException(status_code=404, detail=f"Subject with code {subject_code} not found")
    
    # Check if subject is enrolled by any students
    enroll_check = f"SELECT COUNT(*) as count FROM enrollments WHERE subject_code = '{subject_code}'"
    enroll_result = execute_query(enroll_check, db)
    
    if enroll_result[0]["count"] > 0:
        logger.warning(f"Cannot delete subject {subject_code} - it has active enrollments")
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete subject {subject_code} - it has {enroll_result[0]['count']} active enrollments"
        )
    
    # Delete subject
    query = f"DELETE FROM subjects WHERE subject_code = '{subject_code}'"
    response = execute_query(query, db)
    
    logger.info(f"Subject deleted: {response}")
    return response

@router.get("/subjects/{subject_code}/enrollments", response_model=List[Dict[str, Any]])
def get_subject_enrollments(subject_code: str, db=Depends(get_db)):
    """Get all students enrolled in a specific subject"""
    logger.info(f"Getting enrollments for subject with code: {subject_code}")
    
    # Check if subject exists
    check_query = f"SELECT COUNT(*) as count FROM subjects WHERE subject_code = '{subject_code}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"Subject with code {subject_code} not found")
        raise HTTPException(status_code=404, detail=f"Subject with code {subject_code} not found")
    
    # Get enrollments
    query = f"""
    SELECT 
        s.usn, 
        s.name_of_the_student,
        s.division,
        s.batch,
        e.academic_year,
        e.semester
    FROM 
        enrollments e
    JOIN 
        students s ON e.usn = s.usn
    WHERE 
        e.subject_code = '{subject_code}'
    """
    
    return execute_query(query, db)