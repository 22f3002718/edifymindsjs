from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db
from app.core.security import get_admin_user, get_password_hash
from app.core.security_utils import sanitize_string, sanitize_email, sanitize_name, validate_object_id
from app.core.file_security import log_security_event
from app.models.schemas import PasswordResetRequest

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users")
async def get_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Get all users with optional filtering by role and search (admin only)"""
    db = get_db()
    query = {}
    
    # Filter by role if provided
    if role:
        if role not in ['teacher', 'student', 'admin']:
            raise HTTPException(status_code=400, detail="Invalid role filter")
        query['role'] = role
    
    # Search by name or email if provided
    if search:
        sanitized_search = sanitize_string(search, max_length=100)
        query['$or'] = [
            {'name': {'$regex': sanitized_search, '$options': 'i'}},
            {'email': {'$regex': sanitized_search, '$options': 'i'}}
        ]
    
    # Fetch users, exclude password_hash
    users = await db.users.find(query, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    return users

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    current_user: dict = Depends(get_admin_user)
):
    """Update user details (admin only)"""
    db = get_db()
    # Validate user_id
    try:
        validate_object_id(user_id, "user_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build update data
    update_data = {}
    
    if name is not None:
        update_data['name'] = sanitize_name(name)
    
    if email is not None:
        sanitized_email = sanitize_email(email)
        # Check if email already exists for another user
        existing_user = await db.users.find_one(
            {"email": sanitized_email, "id": {"$ne": user_id}},
            {"_id": 0}
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use by another user")
        update_data['email'] = sanitized_email
    
    if role is not None:
        if role not in ['teacher', 'student', 'admin']:
            raise HTTPException(status_code=400, detail="Invalid role")
        update_data['role'] = role
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Update user
    await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    # Log security event
    log_security_event('admin_user_update', {
        'admin_id': current_user['id'],
        'target_user_id': user_id,
        'updated_fields': list(update_data.keys())
    })
    
    # Get updated user
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
    return updated_user

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request_body: PasswordResetRequest,
    current_user: dict = Depends(get_admin_user)
):
    """Reset a user's password (admin only)"""
    db = get_db()
    # Validate user_id
    try:
        validate_object_id(user_id, "user_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate password length
    if len(request_body.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    # Hash the new password using threadpool
    password_hash = await run_in_threadpool(get_password_hash, request_body.new_password)
    
    # Update password
    await db.users.update_one({"id": user_id}, {"$set": {"password_hash": password_hash}})
    
    # Log security event
    log_security_event('admin_password_reset', {
        'admin_id': current_user['id'],
        'target_user_id': user_id,
        'target_user_email': user['email']
    })
    
    return {"message": "Password reset successfully"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_admin_user)
):
    """Delete a user (admin only)"""
    db = get_db()
    # Validate user_id
    try:
        validate_object_id(user_id, "user_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user_id == current_user['id']:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # If user is a teacher, optionally delete their classes and related data
    if user.get('role') == 'teacher':
        # Get all classes by this teacher
        teacher_classes = await db.classes.find({"teacher_id": user_id}, {"_id": 0}).to_list(1000)
        class_ids = [cls['id'] for cls in teacher_classes]
        
        # Delete classes and related data
        await db.classes.delete_many({"teacher_id": user_id})
        await db.enrollments.delete_many({"class_id": {"$in": class_ids}})
        await db.homework.delete_many({"class_id": {"$in": class_ids}})
        await db.notices.delete_many({"class_id": {"$in": class_ids}})
        await db.resources.delete_many({"class_id": {"$in": class_ids}})
        await db.tests.delete_many({"class_id": {"$in": class_ids}})
        await db.test_submissions.delete_many({"class_id": {"$in": class_ids}})
    
    # If user is a student, delete their enrollments and test submissions
    if user.get('role') == 'student':
        await db.enrollments.delete_many({"student_id": user_id})
        await db.test_submissions.delete_many({"student_id": user_id})
    
    # Delete the user
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log security event
    log_security_event('admin_user_delete', {
        'admin_id': current_user['id'],
        'target_user_id': user_id,
        'target_user_email': user['email'],
        'target_user_role': user['role']
    })
    
    return {"message": "User deleted successfully"}
