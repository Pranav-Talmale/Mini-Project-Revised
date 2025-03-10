from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from api.middleware.database import get_db, execute_query
import logging

logger = logging.getLogger(__name__)

# Pydantic model for enrollment data
class Enrollment(BaseModel):
    usn: str
    subject_code: str
    academic_year: Optional[str] = None
    semester: Optional[int] = None

# Create router
router = APIRouter(tags=["Enrollments"])

@router.get("/enrollments", response_model=List[Dict[str, Any]])
def get_enrollments(
    db=Depends(get_db),
    usn: Optional[str] = Query(None, description="Filter by student USN"),
    subject_code: Optional[str] = Query(None, description="Filter by subject code")
):
    """Get all enrollments with optional filtering"""
    logger.info(f"Getting enrollments with filters: usn={usn}, subject_code={subject_code}")
    
    query = "SELECT e.*, s.name_of_the_student, sub.subject_name FROM enrollments e"
    query += " JOIN students s ON e.usn = s.usn"
    query += " JOIN subjects sub ON e.subject_code = sub.subject_code"
    query += " WHERE 1=1"
    
    if usn:
        query += f" AND e.usn = '{usn}'"
    if subject_code:
        query += f" AND e.subject_code = '{subject_code}'"
    
    return execute_query(query, db)

@router.post("/enrollments", response_model=Dict[str, Any])
def create_enrollment(enrollment: Enrollment, db=Depends(get_db)):
    """Create a new enrollment record"""
    logger.info(f"Creating enrollment for student {enrollment.usn} in subject {enrollment.subject_code}")
    
    # Check if student exists
    student_check = f"SELECT COUNT(*) as count FROM students WHERE usn = '{enrollment.usn}'"
    student_result = execute_query(student_check, db)
    
    if student_result[0]["count"] == 0:
        logger.warning(f"Student with USN {enrollment.usn} not found")
        raise HTTPException(status_code=404, detail=f"Student with USN {enrollment.usn} not found")
    
    # Check if subject exists
    subject_check = f"SELECT COUNT(*) as count FROM subjects WHERE subject_code = '{enrollment.subject_code}'"
    subject_result = execute_query(subject_check, db)
    
    if subject_result[0]["count"] == 0:
        logger.warning(f"Subject with code {enrollment.subject_code} not found")
        raise HTTPException(status_code=404, detail=f"Subject with code {enrollment.subject_code} not found")
    
    # Check if enrollment already exists
    enroll_check = f"""
    SELECT COUNT(*) as count FROM enrollments 
    WHERE usn = '{enrollment.usn}' AND subject_code = '{enrollment.subject_code}'
    """
    enroll_result = execute_query(enroll_check, db)
    
    if enroll_result[0]["count"] > 0:
        logger.warning(f"Enrollment already exists for student {enrollment.usn} in subject {enrollment.subject_code}")
        raise HTTPException(
            status_code=409, 
            detail=f"Student {enrollment.usn} is already enrolled in subject {enrollment.subject_code}"
        )
    
    # Create enrollment
    query = f"""
    INSERT INTO enrollments (usn, subject_code, academic_year, semester)
    VALUES (
        '{enrollment.usn}',
        '{enrollment.subject_code}',
        '{enrollment.academic_year or ""}',
        {enrollment.semester or "NULL"}
    )
    """
    
    response = execute_query(query, db)
    logger.info(f"Enrollment created: {response}")
    return response

@router.delete("/enrollments", response_model=Dict[str, Any])
def delete_enrollment(
    usn: str = Query(..., description="Student USN"),
    subject_code: str = Query(..., description="Subject code"),
    db=Depends(get_db)
):
    """Delete an enrollment record"""
    logger.info(f"Deleting enrollment for student {usn} in subject {subject_code}")
    
    # Check if enrollment exists
    check_query = f"""
    SELECT COUNT(*) as count FROM enrollments 
    WHERE usn = '{usn}' AND subject_code = '{subject_code}'
    """
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"Enrollment not found for student {usn} in subject {subject_code}")
        raise HTTPException(
            status_code=404, 
            detail=f"Enrollment not found for student {usn} in subject {subject_code}"
        )
    
    # Delete enrollment
    query = f"DELETE FROM enrollments WHERE usn = '{usn}' AND subject_code = '{subject_code}'"
    response = execute_query(query, db)
    
    logger.info(f"Enrollment deleted: {response}")
    return response

@router.get("/enrollments/summary", response_model=Dict[str, Any])
def get_enrollment_summary(db=Depends(get_db)):
    """Get summary statistics for enrollments"""
    logger.info("Getting enrollment summary statistics")
    
    query = """
    SELECT 
        COUNT(DISTINCT usn) as total_students,
        COUNT(DISTINCT subject_code) as total_subjects,
        COUNT(*) as total_enrollments
    FROM 
        enrollments
    """
    
    results = execute_query(query, db)
    return results[0] if results else {}