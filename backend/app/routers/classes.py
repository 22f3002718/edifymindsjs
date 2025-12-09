from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.security_utils import sanitize_string, sanitize_url, validate_object_id
from app.models.schemas import (
    Class, ClassCreate, ClassUpdate,
    Enrollment, EnrollmentCreate
)

router = APIRouter(tags=["Classes"])
limiter = Limiter(key_func=get_remote_address)

# ==== CLASS ROUTES ====

@router.post("/classes", response_model=Class)
@limiter.limit("30/minute")
async def create_class(request: Request, class_input: ClassCreate, current_user: dict = Depends(get_current_user)):
    """Create a class with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create classes")
    
    db = get_db()
    
    # Sanitize inputs
    sanitized_data = class_input.model_dump()
    sanitized_data['name'] = sanitize_string(sanitized_data['name'], max_length=200)
    sanitized_data['description'] = sanitize_string(sanitized_data['description'], max_length=1000)
    sanitized_data['grade_level'] = sanitize_string(sanitized_data['grade_level'], max_length=50)
    sanitized_data['time'] = sanitize_string(sanitized_data['time'], max_length=50)
    sanitized_data['start_date'] = sanitize_string(sanitized_data['start_date'], max_length=50)
    if sanitized_data.get('end_date'):
        sanitized_data['end_date'] = sanitize_string(sanitized_data['end_date'], max_length=50)
    if sanitized_data.get('zoom_link'):
        sanitized_data['zoom_link'] = sanitize_url(sanitized_data['zoom_link'])
    if sanitized_data.get('drive_folder_id'):
        sanitized_data['drive_folder_id'] = sanitize_string(sanitized_data['drive_folder_id'], max_length=200)
    
    class_obj = Class(**sanitized_data, teacher_id=current_user["id"])
    doc = class_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.classes.insert_one(doc)
    
    return class_obj

@router.get("/classes", response_model=List[Class])
async def get_classes(current_user: dict = Depends(get_current_user)):
    db = get_db()
    if current_user["role"] == "teacher":
        classes = await db.classes.find({"teacher_id": current_user["id"]}, {"_id": 0}).to_list(1000)
    else:
        # Get enrolled classes for students
        enrollments = await db.enrollments.find({"student_id": current_user["id"]}, {"_id": 0}).to_list(1000)
        class_ids = [e["class_id"] for e in enrollments]
        classes = await db.classes.find({"id": {"$in": class_ids}}, {"_id": 0}).to_list(1000)
    
    for cls in classes:
        if isinstance(cls.get('created_at'), str):
            cls['created_at'] = datetime.fromisoformat(cls['created_at'])
    
    return classes

@router.get("/classes/{class_id}", response_model=Class)
async def get_class(class_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    class_obj = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    if isinstance(class_obj.get('created_at'), str):
        class_obj['created_at'] = datetime.fromisoformat(class_obj['created_at'])
    
    return class_obj

@router.put("/classes/{class_id}", response_model=Class)
async def update_class(class_id: str, class_update: ClassUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update classes")
    
    db = get_db()
    class_obj = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_obj or class_obj["teacher_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Class not found")
    
    update_data = {k: v for k, v in class_update.model_dump().items() if v is not None}
    await db.classes.update_one({"id": class_id}, {"$set": update_data})
    
    updated_class = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if isinstance(updated_class.get('created_at'), str):
        updated_class['created_at'] = datetime.fromisoformat(updated_class['created_at'])
    
    return updated_class

@router.delete("/classes/{class_id}")
async def delete_class(class_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete classes")
    
    db = get_db()
    result = await db.classes.delete_one({"id": class_id, "teacher_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Also delete related data
    await db.enrollments.delete_many({"class_id": class_id})
    await db.homework.delete_many({"class_id": class_id})
    await db.notices.delete_many({"class_id": class_id})
    await db.resources.delete_many({"class_id": class_id})
    
    return {"message": "Class deleted successfully"}

# ==== ENROLLMENT ROUTES ====

@router.post("/enrollments")
async def enroll_student(enrollment_input: EnrollmentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can enroll students")
    
    db = get_db()
    # Check if already enrolled
    existing = await db.enrollments.find_one(
        {"student_id": enrollment_input.student_id, "class_id": enrollment_input.class_id},
        {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled in this class")
    
    enrollment = Enrollment(**enrollment_input.model_dump())
    doc = enrollment.model_dump()
    doc['enrolled_at'] = doc['enrolled_at'].isoformat()
    await db.enrollments.insert_one(doc)
    
    return {"message": "Student enrolled successfully"}

@router.get("/classes/{class_id}/students")
async def get_class_students(class_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    enrollments = await db.enrollments.find({"class_id": class_id}, {"_id": 0}).to_list(1000)
    student_ids = [e["student_id"] for e in enrollments]
    students = await db.users.find({"id": {"$in": student_ids}, "role": "student"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return students

@router.delete("/enrollments/{student_id}/{class_id}")
async def remove_student(student_id: str, class_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can remove students")
    
    db = get_db()
    result = await db.enrollments.delete_one({"student_id": student_id, "class_id": class_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    return {"message": "Student removed successfully"}
