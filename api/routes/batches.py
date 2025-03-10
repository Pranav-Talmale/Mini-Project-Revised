from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from api.middleware.database import get_db, execute_query
import logging

logger = logging.getLogger(__name__)

# Pydantic models for batch operations
class BatchAssignment(BaseModel):
    usn: str
    batch: str

class BatchFormation(BaseModel):
    division: str
    num_batches: int = 3
    batch_prefix: Optional[str] = None

# Create router
router = APIRouter(tags=["Batches"])

@router.get("/batches", response_model=List[Dict[str, Any]])
def get_batches(
    db=Depends(get_db),
    division: Optional[str] = Query(None, description="Filter by division")
):
    """Get batch distribution summary"""
    logger.info(f"Getting batch distribution with filter: division={division}")
    
    query = "SELECT batch, COUNT(*) as student_count FROM students WHERE batch IS NOT NULL"
    
    if division:
        query += f" AND division = '{division}'"
    
    query += " GROUP BY batch ORDER BY batch"
    
    return execute_query(query, db)

@router.get("/batches/{batch}", response_model=List[Dict[str, Any]])
def get_batch_students(batch: str = Path(..., description="Batch identifier"), db=Depends(get_db)):
    """Get all students in a specific batch"""
    logger.info(f"Getting students in batch: {batch}")
    
    query = f"""
    SELECT s.usn, s.name_of_the_student, s.email_address, s.division, s.batch
    FROM students s
    WHERE s.batch = '{batch}'
    """
    
    results = execute_query(query, db)
    
    if not results:
        logger.warning(f"No students found in batch {batch}")
    
    return results

@router.post("/batches/assign", response_model=Dict[str, Any])
def assign_batch(assignments: List[BatchAssignment], db=Depends(get_db)):
    """Assign multiple students to batches"""
    logger.info(f"Assigning {len(assignments)} students to batches")
    
    success_count = 0
    failed_usns = []
    
    for assignment in assignments:
        # Check if student exists
        check_query = f"SELECT COUNT(*) as count FROM students WHERE usn = '{assignment.usn}'"
        result = execute_query(check_query, db)
        
        if result[0]["count"] == 0:
            logger.warning(f"Student with USN {assignment.usn} not found")
            failed_usns.append(assignment.usn)
            continue
        
        # Update student batch
        query = f"UPDATE students SET batch = '{assignment.batch}' WHERE usn = '{assignment.usn}'"
        result = execute_query(query, db)
        
        if "message" in result and "successfully" in result["message"]:
            success_count += 1
        else:
            failed_usns.append(assignment.usn)
    
    response = {
        "message": f"Assigned {success_count} students to batches",
        "success_count": success_count,
        "failed_usns": failed_usns
    }
    
    logger.info(f"Batch assignment completed: {response}")
    return response

@router.post("/batches/form", response_model=Dict[str, Any])
def form_batches(formation: BatchFormation, db=Depends(get_db)):
    """Form batches automatically based on DLO subject combinations"""
    logger.info(f"Forming {formation.num_batches} batches for division {formation.division}")
    
    # Check if division exists
    check_query = f"SELECT COUNT(*) as count FROM students WHERE division = '{formation.division}'"
    result = execute_query(check_query, db)
    
    if result[0]["count"] == 0:
        logger.warning(f"No students found in division {formation.division}")
        raise HTTPException(status_code=404, detail=f"No students found in division {formation.division}")
    
    # Get all students in the division with their DLO subjects
    query = f"""
    SELECT 
        s.usn,
        GROUP_CONCAT(DISTINCT CASE WHEN sub.subject_type = 'DLO' THEN sub.subject_code ELSE NULL END) as dlo_subjects
    FROM 
        students s
    LEFT JOIN 
        enrollments e ON s.usn = e.usn
    LEFT JOIN 
        subjects sub ON e.subject_code = sub.subject_code
    WHERE 
        s.division = '{formation.division}'
    GROUP BY 
        s.usn
    """
    
    students = execute_query(query, db)
    
    if not students:
        logger.warning(f"No students with subjects found in division {formation.division}")
        raise HTTPException(status_code=404, detail=f"No students with subjects found in division {formation.division}")
    
    # Group students by DLO subject combinations
    combinations = {}
    for student in students:
        dlo_subjects = student.get('dlo_subjects', '')
        if dlo_subjects not in combinations:
            combinations[dlo_subjects] = []
        combinations[dlo_subjects].append(student['usn'])
    
    # Sort combinations by size (largest first)
    sorted_combinations = sorted(combinations.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Initialize batches
    batch_prefix = formation.batch_prefix or formation.division
    batches = {f"{batch_prefix}{i+1}": [] for i in range(formation.num_batches)}
    batch_names = list(batches.keys())
    
    # Distribute students from each combination group across batches
    batch_idx = 0
    for _, student_usns in sorted_combinations:
        for usn in student_usns:
            # Assign to the next batch in rotation
            target_batch = batch_names[batch_idx % formation.num_batches]
            batches[target_batch].append(usn)
            batch_idx += 1
    
    # Update student records with batch assignments
    total_assigned = 0
    for batch, usns in batches.items():
        if not usns:
            continue
            
        usn_list = "', '".join(usns)
        query = f"""
        UPDATE students 
        SET batch = '{batch}' 
        WHERE usn IN ('{usn_list}')
        """
        
        result = execute_query(query, db)
        if "message" in result and "successfully" in result["message"]:
            total_assigned += len(usns)
    
    response = {
        "message": f"Successfully formed {len(batches)} batches with {total_assigned} students",
        "batch_distribution": {batch: len(usns) for batch, usns in batches.items()}
    }
    
    logger.info(f"Batch formation completed: {response}")
    return response

@router.delete("/batches/{batch}", response_model=Dict[str, Any])
def clear_batch(batch: str = Path(..., description="Batch identifier"), db=Depends(get_db)):
    """Clear all students from a specific batch"""
    logger.info(f"Clearing all students from batch: {batch}")
    
    query = f"UPDATE students SET batch = NULL WHERE batch = '{batch}'"
    return execute_query(query, db)