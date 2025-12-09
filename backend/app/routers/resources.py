from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.security_utils import sanitize_string, sanitize_url, validate_object_id
from app.core.config import settings
from app.models.schemas import (
    Homework, HomeworkCreate,
    Notice, NoticeCreate,
    Resource, ResourceCreate
)
from app.core.file_security import log_security_event
import logging
from pathlib import Path

# Setup Logger and Upload Dir
logger = logging.getLogger(__name__)
# UPLOAD_DIR depends on where we run. In modular app, we might need to define it in config
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" 

router = APIRouter(tags=["Resources"])
limiter = Limiter(key_func=get_remote_address)

# ==== HOMEWORK ROUTES ====

@router.post("/homework", response_model=Homework)
@limiter.limit("30/minute")
async def create_homework(request: Request, homework_input: HomeworkCreate, current_user: dict = Depends(get_current_user)):
    """Create homework with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create homework")
    
    db = get_db()
    
    # Sanitize inputs
    sanitized_data = homework_input.model_dump()
    sanitized_data['title'] = sanitize_string(sanitized_data['title'], max_length=200)
    sanitized_data['description'] = sanitize_string(sanitized_data['description'], max_length=2000)
    sanitized_data['due_date'] = sanitize_string(sanitized_data['due_date'], max_length=50)
    if sanitized_data.get('attachment_link'):
        sanitized_data['attachment_link'] = sanitize_url(sanitized_data['attachment_link'])
    
    try:
        validate_object_id(sanitized_data['class_id'], "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    homework = Homework(**sanitized_data)
    doc = homework.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.homework.insert_one(doc)
    
    return homework

@router.get("/classes/{class_id}/homework", response_model=List[Homework])
async def get_class_homework(class_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    homework_list = await db.homework.find({"class_id": class_id}, {"_id": 0}).to_list(1000)
    
    for hw in homework_list:
        if isinstance(hw.get('created_at'), str):
            hw['created_at'] = datetime.fromisoformat(hw['created_at'])
    
    return homework_list

@router.delete("/homework/{homework_id}")
async def delete_homework(homework_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete homework")
    
    db = get_db()
    homework = await db.homework.find_one({"id": homework_id}, {"_id": 0})
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    await db.homework.delete_one({"id": homework_id})
    
    # Delete physical file if uploaded
    if homework.get('attachment_link', '').startswith('/uploads/'):
        filename = homework['attachment_link'].replace('/uploads/', '')
        file_path = UPLOAD_DIR / filename
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted uploaded file: {filename}")
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {str(e)}")
    
    return {"message": "Homework deleted successfully"}

# ==== NOTICE ROUTES ====

@router.post("/notices", response_model=Notice)
@limiter.limit("30/minute")
async def create_notice(request: Request, notice_input: NoticeCreate, current_user: dict = Depends(get_current_user)):
    """Create notice with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create notices")
    
    db = get_db()
    sanitized_data = notice_input.model_dump()
    sanitized_data['title'] = sanitize_string(sanitized_data['title'], max_length=200)
    sanitized_data['message'] = sanitize_string(sanitized_data['message'], max_length=2000)
    
    try:
        validate_object_id(sanitized_data['class_id'], "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    notice = Notice(**sanitized_data, created_by=current_user["id"])
    doc = notice.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.notices.insert_one(doc)
    
    return notice

@router.get("/classes/{class_id}/notices", response_model=List[Notice])
async def get_class_notices(class_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    notices = await db.notices.find({"class_id": class_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for notice in notices:
        if isinstance(notice.get('created_at'), str):
            notice['created_at'] = datetime.fromisoformat(notice['created_at'])
    
    return notices

@router.delete("/notices/{notice_id}")
async def delete_notice(notice_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete notices")
    
    db = get_db()
    result = await db.notices.delete_one({"id": notice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    return {"message": "Notice deleted successfully"}

# ==== RESOURCE ROUTES ====

@router.post("/resources", response_model=Resource)
@limiter.limit("30/minute")
async def create_resource(request: Request, resource_input: ResourceCreate, current_user: dict = Depends(get_current_user)):
    """Create resource with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add resources")
    
    db = get_db()
    sanitized_data = resource_input.model_dump()
    sanitized_data['name'] = sanitize_string(sanitized_data['name'], max_length=200)
    sanitized_data['type'] = sanitize_string(sanitized_data['type'], max_length=50)
    sanitized_data['drive_link'] = sanitize_url(sanitized_data['drive_link'])
    
    try:
        validate_object_id(sanitized_data['class_id'], "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    resource = Resource(**sanitized_data)
    doc = resource.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.resources.insert_one(doc)
    
    return resource

@router.get("/classes/{class_id}/resources", response_model=List[Resource])
async def get_class_resources(class_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    resources = await db.resources.find({"class_id": class_id}, {"_id": 0}).to_list(1000)
    
    for resource in resources:
        if isinstance(resource.get('created_at'), str):
            resource['created_at'] = datetime.fromisoformat(resource['created_at'])
    
    return resources

@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete resources")
    
    db = get_db()
    resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    await db.resources.delete_one({"id": resource_id})
    
    if resource.get('drive_link', '').startswith('/uploads/'):
        filename = resource['drive_link'].replace('/uploads/', '')
        file_path = UPLOAD_DIR / filename
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted uploaded file: {filename}")
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {str(e)}")
    
    return {"message": "Resource deleted successfully"}
