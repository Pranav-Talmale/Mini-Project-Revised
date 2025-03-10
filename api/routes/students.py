from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from api.middleware.database import get_db, execute_query
import logging

logger = logging.getLogger(__name__)

# Pydantic model for student data
class Student(BaseModel):
    usn: str
    name_of_the_student: str
    email_address: str
    phone_number: Optional[str] = None
    division: Optional[str] = None
    batch: Optional[str] = None
    semester: Optional[int] = None
    program: Optional[str] = None
    department: Optional[str] = None

# Create router
router = APIRouter(tags=["Students"])

@router.get("/students", response_model=List[Dict[str, Any]])
def get_students(
    db=Depends(get_db), 
    division: Optional[str] = Query(None, description="Filter by division"),
    batch: Optional[str] = Query(None, description="Filter by batch"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """Get all students with optional filtering"""
    logger.info(f"Getting students with filters: division={division}, batch={batch}, limit={limit}")
    
    query = "SELECT * FROM students WHERE 1=1"
    
    if division:
        query += f" AND division = '{division}'"
    if batch:
        query += f" AND batch = '{batch}'"
    
    query += f" LIMIT {limit}"
    
    return execute_query(query, db)

@router.get("/students/{usn}", response_model=Dict[str, Any])
def get_student(usn: str = Path(..., description="Student USN"), db=Depends(get_db)):
    """Get details of a specific student by USN"""
    logger.info(f"Getting student with USN: {usn}")
    
    query = f"SELECT * FROM students WHERE usn = '{usn}'"
    results = execute_query(query, db)
    
    if isinstance(results, dict) and "message" in results:
        logger.warning(f"Student with USN {usn} not found")
        raise HTTPException(status_code=404, detail=f"Student with USN {usn} not found")
    
    if not results:
        logger.warning(f"Student with USN {usn} not found")
        raise HTTPException(status_code=404, detail=f"Student with USN {usn} not found")
    
    return results[0]

@router.post("/students", response_model=Dict[str, Any])
def create_student(student: Student, db=Depends(get_db)):
    """Create a new student record"""
    logger.info(f"Creating new student with USN: {student.usn}")
    
    # Check if student already exists
    check_query = f"SELECT COUNT(*) as count FROM students WHERE usn = '{student.usn}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] > 0:
        logger.warning(f"Student with USN {student.usn} already exists")
        raise HTTPException(status_code=409, detail=f"Student with USN {student.usn} already exists")
    
    # Create student
    query = f"""
    INSERT INTO students (usn, name_of_the_student, email_address, phone_number, division, batch, semester, program, department)
    VALUES (
        '{student.usn}',
        '{student.name_of_the_student}',
        '{student.email_address}',
        '{student.phone_number or ""}',
        '{student.division or ""}',
        '{student.batch or ""}',
        {student.semester or "NULL"},
        '{student.program or ""}',
        '{student.department or ""}'
    )
    """
    
    response = execute_query(query, db)
    logger.info(f"Student created: {response}")
    return response

@router.put("/students/{usn}", response_model=Dict[str, Any])
def update_student(usn: str, student: Student, db=Depends(get_db)):
    """Update an existing student record"""
    logger.info(f"Updating student with USN: {usn}")
    
    # Check if student exists
    check_query = f"SELECT COUNT(*) as count FROM students WHERE usn = '{usn}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"Student with USN {usn} not found for update")
        raise HTTPException(status_code=404, detail=f"Student with USN {usn} not found")
    
    # Update student
    query = f"""
    UPDATE students SET
        name_of_the_student = '{student.name_of_the_student}',
        email_address = '{student.email_address}',
        phone_number = '{student.phone_number or ""}',
        division = '{student.division or ""}',
        batch = '{student.batch or ""}',
        semester = {student.semester or "NULL"},
        program = '{student.program or ""}',
        department = '{student.department or ""}'
    WHERE usn = '{usn}'
    """
    
    response = execute_query(query, db)
    logger.info(f"Student updated: {response}")
    return response

@router.delete("/students/{usn}", response_model=Dict[str, Any])
def delete_student(usn: str, db=Depends(get_db)):
    """Delete a student record"""
    logger.info(f"Deleting student with USN: {usn}")
    
    # Check if student exists
    check_query = f"SELECT COUNT(*) as count FROM students WHERE usn = '{usn}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"Student with USN {usn} not found for deletion")
        raise HTTPException(status_code=404, detail=f"Student with USN {usn} not found")
    
    # First delete associated enrollments
    delete_enrollments_query = f"DELETE FROM enrollments WHERE usn = '{usn}'"
    execute_query(delete_enrollments_query, db)
    
    # Then delete student
    query = f"DELETE FROM students WHERE usn = '{usn}'"
    response = execute_query(query, db)
    
    logger.info(f"Student deleted: {response}")
    return response

@router.get("/students/{usn}/enrollments", response_model=List[Dict[str, Any]])
def get_student_enrollments(usn: str, db=Depends(get_db)):
    """Get all subjects enrolled by a specific student"""
    logger.info(f"Getting enrollments for student with USN: {usn}")
    
    # Check if student exists
    check_query = f"SELECT COUNT(*) as count FROM students WHERE usn = '{usn}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"Student with USN {usn} not found")
        raise HTTPException(status_code=404, detail=f"Student with USN {usn} not found")
    
    # Get enrollments
    query = f"""
    SELECT 
        e.subject_code, 
        s.subject_name,
        s.subject_type,
        s.credits,
        e.academic_year,
        e.semester
    FROM 
        enrollments e
    JOIN 
        subjects s ON e.subject_code = s.subject_code
    WHERE 
        e.usn = '{usn}'
    """
    
    return execute_query(query, db)