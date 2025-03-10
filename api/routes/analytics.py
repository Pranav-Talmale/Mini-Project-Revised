from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from api.middleware.database import get_db, execute_query
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Analytics"])

@router.get("/analytics/subjects", response_model=List[Dict[str, Any]])
def get_subject_analytics(db=Depends(get_db)):
    """Get subject enrollment statistics"""
    logger.info("Getting subject enrollment statistics")
    
    query = """
    SELECT 
        sub.subject_code,
        sub.subject_name,
        sub.subject_type,
        COUNT(e.id) as enrollment_count
    FROM 
        subjects sub
    LEFT JOIN 
        enrollments e ON sub.subject_code = e.subject_code
    GROUP BY 
        sub.subject_code
    ORDER BY 
        enrollment_count DESC
    """
    
    return execute_query(query, db)

@router.get("/analytics/combinations", response_model=List[Dict[str, Any]])
def get_subject_combinations(
    db=Depends(get_db),
    subject_type: str = Query("DLO", description="Subject type to analyze combinations for")
):
    """Get popular subject combinations"""
    logger.info(f"Getting popular {subject_type} subject combinations")
    
    query = f"""
    SELECT 
        s1.subject_name as subject1, 
        s2.subject_name as subject2, 
        COUNT(DISTINCT e1.usn) as student_count
    FROM 
        enrollments e1
    JOIN 
        enrollments e2 ON e1.usn = e2.usn AND e1.subject_code < e2.subject_code
    JOIN 
        subjects s1 ON e1.subject_code = s1.subject_code
    JOIN 
        subjects s2 ON e2.subject_code = s2.subject_code
    WHERE 
        s1.subject_type = '{subject_type}' AND s2.subject_type = '{subject_type}'
    GROUP BY 
        s1.subject_name, s2.subject_name
    ORDER BY 
        student_count DESC
    """
    
    return execute_query(query, db)

@router.get("/analytics/divisions", response_model=List[Dict[str, Any]])
def get_division_analytics(db=Depends(get_db)):
    """Get division statistics"""
    logger.info("Getting division statistics")
    
    query = """
    SELECT 
        division,
        COUNT(*) as student_count,
        COUNT(DISTINCT batch) as batch_count
    FROM 
        students
    WHERE
        division IS NOT NULL
    GROUP BY 
        division
    ORDER BY 
        student_count DESC
    """
    
    return execute_query(query, db)

@router.get("/analytics/student-performance", response_model=List[Dict[str, Any]])
def get_student_performance(
    db=Depends(get_db),
    division: Optional[str] = Query(None, description="Filter by division"),
    batch: Optional[str] = Query(None, description="Filter by batch")
):
    """Get student performance statistics by subject"""
    logger.info(f"Getting student performance with filters: division={division}, batch={batch}")
    
    query = """
    SELECT 
        sub.subject_type,
        sub.subject_name,
        COUNT(DISTINCT e.usn) as student_count,
        s.division,
        s.batch
    FROM 
        enrollments e
    JOIN 
        students s ON e.usn = s.usn
    JOIN 
        subjects sub ON e.subject_code = sub.subject_code
    WHERE 1=1
    """
    
    if division:
        query += f" AND s.division = '{division}'"
    if batch:
        query += f" AND s.batch = '{batch}'"
    
    query += """
    GROUP BY 
        sub.subject_name, s.division, s.batch
    ORDER BY 
        student_count DESC
    """
    
    return execute_query(query, db)

@router.get("/analytics/dashboard", response_model=Dict[str, Any])
def get_dashboard_analytics(db=Depends(get_db)):
    """Get dashboard summary statistics"""
    logger.info("Getting dashboard summary statistics")
    
    # Get total students count
    students_query = "SELECT COUNT(*) as total_students FROM students"
    students_result = execute_query(students_query, db)
    
    # Get total subjects count
    subjects_query = "SELECT COUNT(*) as total_subjects FROM subjects"
    subjects_result = execute_query(subjects_query, db)
    
    # Get total enrollments count
    enrollments_query = "SELECT COUNT(*) as total_enrollments FROM enrollments"
    enrollments_result = execute_query(enrollments_query, db)
    
    # Get division distribution
    divisions_query = """
    SELECT division, COUNT(*) as count 
    FROM students 
    WHERE division IS NOT NULL 
    GROUP BY division
    """
    divisions_result = execute_query(divisions_query, db)
    
    # Get batch distribution
    batches_query = """
    SELECT batch, COUNT(*) as count 
    FROM students 
    WHERE batch IS NOT NULL 
    GROUP BY batch
    """
    batches_result = execute_query(batches_query, db)
    
    # Get subject type distribution
    subject_types_query = """
    SELECT subject_type, COUNT(*) as count 
    FROM subjects 
    GROUP BY subject_type
    """
    subject_types_result = execute_query(subject_types_query, db)
    
    return {
        "total_students": students_result[0]["total_students"] if students_result else 0,
        "total_subjects": subjects_result[0]["total_subjects"] if subjects_result else 0,
        "total_enrollments": enrollments_result[0]["total_enrollments"] if enrollments_result else 0,
        "divisions": divisions_result,
        "batches": batches_result,
        "subject_types": subject_types_result
    }