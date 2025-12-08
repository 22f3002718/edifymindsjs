from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import shutil

# Import security utilities
from security_utils import (
    sanitize_string, sanitize_email, sanitize_name, sanitize_url,
    sanitize_mongo_query, validate_object_id, sanitize_test_questions
)
from file_security import (
    validate_uploaded_file, log_security_event
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection with connection pooling
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    minPoolSize=1,
    maxPoolSize=10,
    maxIdleTimeMS=30000,  # Close idle connections after 30 seconds
    serverSelectionTimeoutMS=5000
)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'edifyminds-junior-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# File Upload Configuration
UPLOAD_DIR = ROOT_DIR / "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.zip'
}
DANGEROUS_EXTENSIONS = {'.exe', '.sh', '.py', '.bat', '.cmd', '.ps1', '.jar', '.app'}

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ==== RATE LIMITING SETUP ====
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==== MODELS ====

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    name: str
    role: str  # "teacher" or "student"
    parent_contact: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str
    parent_contact: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class Class(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    grade_level: str
    days_of_week: List[str]  # ["Monday", "Wednesday", "Friday"]
    time: str  # "10:00 AM"
    start_date: str
    end_date: Optional[str] = None
    zoom_link: Optional[str] = None
    drive_folder_id: Optional[str] = None
    teacher_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClassCreate(BaseModel):
    name: str
    description: str
    grade_level: str
    days_of_week: List[str]
    time: str
    start_date: str
    end_date: Optional[str] = None
    zoom_link: Optional[str] = None
    drive_folder_id: Optional[str] = None

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    grade_level: Optional[str] = None
    days_of_week: Optional[List[str]] = None
    time: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    zoom_link: Optional[str] = None
    drive_folder_id: Optional[str] = None

class Enrollment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    class_id: str
    enrolled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EnrollmentCreate(BaseModel):
    student_id: str
    class_id: str

class Homework(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    title: str
    description: str
    due_date: str
    attachment_link: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HomeworkCreate(BaseModel):
    class_id: str
    title: str
    description: str
    due_date: str
    attachment_link: Optional[str] = None

class Notice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    title: str
    message: str
    is_important: bool = False
    created_by: str  # teacher_id
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NoticeCreate(BaseModel):
    class_id: str
    title: str
    message: str
    is_important: bool = False

class Resource(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    name: str
    type: str  # "folder" or "file"
    drive_link: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResourceCreate(BaseModel):
    class_id: str
    name: str
    type: str
    drive_link: str

# Test Models
class TestQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str  # e.g., "A", "B", "C"

class Test(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    title: str
    description: str
    duration_minutes: int
    questions: List[TestQuestion]
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TestCreate(BaseModel):
    class_id: str
    title: str
    description: str
    duration_minutes: int
    questions_text: str  # Raw text to be parsed

class StudentAnswer(BaseModel):
    question_index: int
    selected_answer: str

class TestSubmission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    student_id: str
    answers: List[StudentAnswer]
    score: int
    total_questions: int
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TestSubmit(BaseModel):
    test_id: str
    answers: List[StudentAnswer]

# ==== AUTHENTICATION UTILITIES ====

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Dependency to ensure the current user is an admin"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ==== AUTHENTICATION ROUTES ====

@api_router.post("/auth/register", response_model=Token)
@limiter.limit("5/minute")
async def register(request: Request, user_input: UserCreate):
    """Register a new user with rate limiting and input sanitization"""
    
    # Sanitize inputs
    try:
        sanitized_email = sanitize_email(user_input.email)
        sanitized_name = sanitize_name(user_input.name)
        
        # Validate role
        if user_input.role not in ['teacher', 'student', 'admin']:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'teacher', 'student', or 'admin'")
        
        # Sanitize optional parent contact
        parent_contact = sanitize_string(user_input.parent_contact) if user_input.parent_contact else None
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if user exists - using sanitized query
    existing_user = await db.users.find_one(
        sanitize_mongo_query({"email": sanitized_email}), 
        {"_id": 0}
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password in threadpool to avoid blocking the event loop
    password_hash = await run_in_threadpool(get_password_hash, user_input.password)
    
    # Create user with sanitized data
    user = User(
        email=sanitized_email,
        password_hash=password_hash,
        name=sanitized_name,
        role=user_input.role,
        parent_contact=parent_contact
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Log security event
    log_security_event('user_registration', {
        'user_id': user.id,
        'email': sanitized_email,
        'role': user_input.role
    })
    
    # Create token
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={"id": user.id, "email": user.email, "name": user.name, "role": user.role}
    )

@api_router.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user_input: UserLogin):
    """Login with rate limiting and input sanitization"""
    
    # Sanitize email input
    try:
        sanitized_email = sanitize_email(user_input.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Query with sanitized input
    user = await db.users.find_one(
        sanitize_mongo_query({"email": sanitized_email}), 
        {"_id": 0}
    )
    
    if not user:
        # Log failed login attempt
        log_security_event('failed_login', {
            'email': sanitized_email,
            'ip': get_remote_address(request)
        })
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password in threadpool to avoid blocking the event loop
    password_valid = await run_in_threadpool(verify_password, user_input.password, user["password_hash"])
    
    if not password_valid:
        # Log failed login attempt
        log_security_event('failed_login', {
            'email': sanitized_email,
            'ip': get_remote_address(request)
        })
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Log successful login
    log_security_event('successful_login', {
        'user_id': user["id"],
        'email': sanitized_email
    })
    
    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "email": current_user["email"], "name": current_user["name"], "role": current_user["role"]}

# ==== CLASS ROUTES ====

@api_router.post("/classes", response_model=Class)
@limiter.limit("30/minute")
async def create_class(request: Request, class_input: ClassCreate, current_user: dict = Depends(get_current_user)):
    """Create a class with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create classes")
    
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

@api_router.get("/classes", response_model=List[Class])
async def get_classes(current_user: dict = Depends(get_current_user)):
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

@api_router.get("/classes/{class_id}", response_model=Class)
async def get_class(class_id: str, current_user: dict = Depends(get_current_user)):
    class_obj = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    
    if isinstance(class_obj.get('created_at'), str):
        class_obj['created_at'] = datetime.fromisoformat(class_obj['created_at'])
    
    return class_obj

@api_router.put("/classes/{class_id}", response_model=Class)
async def update_class(class_id: str, class_update: ClassUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update classes")
    
    class_obj = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_obj or class_obj["teacher_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Class not found")
    
    update_data = {k: v for k, v in class_update.model_dump().items() if v is not None}
    await db.classes.update_one({"id": class_id}, {"$set": update_data})
    
    updated_class = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if isinstance(updated_class.get('created_at'), str):
        updated_class['created_at'] = datetime.fromisoformat(updated_class['created_at'])
    
    return updated_class

@api_router.delete("/classes/{class_id}")
async def delete_class(class_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete classes")
    
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

@api_router.post("/enrollments")
async def enroll_student(enrollment_input: EnrollmentCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can enroll students")
    
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

@api_router.get("/classes/{class_id}/students")
async def get_class_students(class_id: str, current_user: dict = Depends(get_current_user)):
    enrollments = await db.enrollments.find({"class_id": class_id}, {"_id": 0}).to_list(1000)
    student_ids = [e["student_id"] for e in enrollments]
    students = await db.users.find({"id": {"$in": student_ids}, "role": "student"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return students

@api_router.delete("/enrollments/{student_id}/{class_id}")
async def remove_student(student_id: str, class_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can remove students")
    
    result = await db.enrollments.delete_one({"student_id": student_id, "class_id": class_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    return {"message": "Student removed successfully"}

# ==== HOMEWORK ROUTES ====

@api_router.post("/homework", response_model=Homework)
@limiter.limit("30/minute")
async def create_homework(request: Request, homework_input: HomeworkCreate, current_user: dict = Depends(get_current_user)):
    """Create homework with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create homework")
    
    # Sanitize inputs
    sanitized_data = homework_input.model_dump()
    sanitized_data['title'] = sanitize_string(sanitized_data['title'], max_length=200)
    sanitized_data['description'] = sanitize_string(sanitized_data['description'], max_length=2000)
    sanitized_data['due_date'] = sanitize_string(sanitized_data['due_date'], max_length=50)
    if sanitized_data.get('attachment_link'):
        sanitized_data['attachment_link'] = sanitize_url(sanitized_data['attachment_link'])
    
    # Validate class_id
    try:
        validate_object_id(sanitized_data['class_id'], "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    homework = Homework(**sanitized_data)
    doc = homework.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.homework.insert_one(doc)
    
    return homework

@api_router.get("/classes/{class_id}/homework", response_model=List[Homework])
async def get_class_homework(class_id: str, current_user: dict = Depends(get_current_user)):
    homework_list = await db.homework.find({"class_id": class_id}, {"_id": 0}).to_list(1000)
    
    for hw in homework_list:
        if isinstance(hw.get('created_at'), str):
            hw['created_at'] = datetime.fromisoformat(hw['created_at'])
    
    return homework_list

@api_router.delete("/homework/{homework_id}")
async def delete_homework(homework_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete homework")
    
    # Get homework to check if it has an uploaded file
    homework = await db.homework.find_one({"id": homework_id}, {"_id": 0})
    if not homework:
        raise HTTPException(status_code=404, detail="Homework not found")
    
    # Delete from database
    await db.homework.delete_one({"id": homework_id})
    
    # If it's an uploaded file (starts with /uploads/), delete the physical file
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

@api_router.post("/notices", response_model=Notice)
@limiter.limit("30/minute")
async def create_notice(request: Request, notice_input: NoticeCreate, current_user: dict = Depends(get_current_user)):
    """Create notice with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create notices")
    
    # Sanitize inputs
    sanitized_data = notice_input.model_dump()
    sanitized_data['title'] = sanitize_string(sanitized_data['title'], max_length=200)
    sanitized_data['message'] = sanitize_string(sanitized_data['message'], max_length=2000)
    
    # Validate class_id
    try:
        validate_object_id(sanitized_data['class_id'], "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    notice = Notice(**sanitized_data, created_by=current_user["id"])
    doc = notice.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.notices.insert_one(doc)
    
    return notice

@api_router.get("/classes/{class_id}/notices", response_model=List[Notice])
async def get_class_notices(class_id: str, current_user: dict = Depends(get_current_user)):
    notices = await db.notices.find({"class_id": class_id}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for notice in notices:
        if isinstance(notice.get('created_at'), str):
            notice['created_at'] = datetime.fromisoformat(notice['created_at'])
    
    return notices

@api_router.delete("/notices/{notice_id}")
async def delete_notice(notice_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete notices")
    
    result = await db.notices.delete_one({"id": notice_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    return {"message": "Notice deleted successfully"}

# ==== RESOURCE ROUTES ====

@api_router.post("/resources", response_model=Resource)
@limiter.limit("30/minute")
async def create_resource(request: Request, resource_input: ResourceCreate, current_user: dict = Depends(get_current_user)):
    """Create resource with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add resources")
    
    # Sanitize inputs
    sanitized_data = resource_input.model_dump()
    sanitized_data['name'] = sanitize_string(sanitized_data['name'], max_length=200)
    sanitized_data['type'] = sanitize_string(sanitized_data['type'], max_length=50)
    sanitized_data['drive_link'] = sanitize_url(sanitized_data['drive_link'])
    
    # Validate class_id
    try:
        validate_object_id(sanitized_data['class_id'], "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    resource = Resource(**sanitized_data)
    doc = resource.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.resources.insert_one(doc)
    
    return resource

@api_router.get("/classes/{class_id}/resources", response_model=List[Resource])
async def get_class_resources(class_id: str, current_user: dict = Depends(get_current_user)):
    resources = await db.resources.find({"class_id": class_id}, {"_id": 0}).to_list(1000)
    
    for resource in resources:
        if isinstance(resource.get('created_at'), str):
            resource['created_at'] = datetime.fromisoformat(resource['created_at'])
    
    return resources

@api_router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete resources")
    
    # Get resource to check if it's an uploaded file
    resource = await db.resources.find_one({"id": resource_id}, {"_id": 0})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Delete from database
    await db.resources.delete_one({"id": resource_id})
    
    # If it's an uploaded file (starts with /uploads/), delete the physical file
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

# ==== STUDENT ROUTES ====

@api_router.get("/students")
async def get_all_students(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view all students")
    
    students = await db.users.find({"role": "student"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return students

# ==== TEST ROUTES ====

def parse_questions(text: str) -> List[TestQuestion]:
    """Parse questions from formatted text"""
    questions = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    current_question = None
    current_options = []
    current_answer = None
    
    for line in lines:
        if line.upper().startswith('Q'):
            # Save previous question if exists
            if current_question and current_options and current_answer:
                questions.append(TestQuestion(
                    question=current_question,
                    options=current_options,
                    correct_answer=current_answer
                ))
            # Start new question
            current_question = line[line.find('Q')+1:].strip()
            if current_question.startswith('.') or current_question.startswith(')'):
                current_question = current_question[1:].strip()
            # Remove leading numbers like "Q1" or "Q1."
            import re
            current_question = re.sub(r'^Q?\d+[\.\):]?\s*', '', line, flags=re.IGNORECASE).strip()
            current_options = []
            current_answer = None
            
        elif line[0].upper() in ['A', 'B', 'C', 'D', 'E', 'F'] and (len(line) > 1 and line[1] in [')', '.', ':']):
            # Option line
            option_text = line[2:].strip()
            current_options.append(option_text)
            
        elif line.upper().startswith('ANSWER:'):
            # Answer line
            answer_part = line[7:].strip().upper()
            # Extract just the letter
            current_answer = answer_part[0] if answer_part else None
    
    # Save last question
    if current_question and current_options and current_answer:
        questions.append(TestQuestion(
            question=current_question,
            options=current_options,
            correct_answer=current_answer
        ))
    
    return questions

@api_router.post("/tests", response_model=Test)
@limiter.limit("30/minute")
async def create_test(request: Request, test_input: TestCreate, current_user: dict = Depends(get_current_user)):
    """Create a test with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create tests")
    
    # Sanitize inputs
    sanitized_title = sanitize_string(test_input.title, max_length=200)
    sanitized_description = sanitize_string(test_input.description, max_length=1000)
    sanitized_questions_text = sanitize_test_questions(test_input.questions_text)
    
    # Validate class_id format
    try:
        validate_object_id(test_input.class_id, "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Parse questions from sanitized text
    try:
        questions = parse_questions(sanitized_questions_text)
        if not questions:
            raise HTTPException(status_code=400, detail="No valid questions found in the text")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing questions: {str(e)}")
    
    test = Test(
        class_id=test_input.class_id,
        title=sanitized_title,
        description=sanitized_description,
        duration_minutes=test_input.duration_minutes,
        questions=[q.model_dump() for q in questions],
        created_by=current_user["id"]
    )
    
    doc = test.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.tests.insert_one(doc)
    
    return test

@api_router.get("/classes/{class_id}/tests", response_model=List[Test])
async def get_class_tests(class_id: str, current_user: dict = Depends(get_current_user)):
    tests = await db.tests.find({"class_id": class_id}, {"_id": 0}).to_list(1000)
    
    for test in tests:
        if isinstance(test.get('created_at'), str):
            test['created_at'] = datetime.fromisoformat(test['created_at'])
    
    return tests

@api_router.get("/tests/{test_id}")
async def get_test(test_id: str, current_user: dict = Depends(get_current_user)):
    test = await db.tests.find_one({"id": test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if isinstance(test.get('created_at'), str):
        test['created_at'] = datetime.fromisoformat(test['created_at'])
    
    # For students, hide correct answers until they submit
    if current_user["role"] == "student":
        for question in test.get("questions", []):
            question.pop("correct_answer", None)
    
    return test

@api_router.post("/tests/submit", response_model=TestSubmission)
@limiter.limit("30/minute")
async def submit_test(request: Request, submission: TestSubmit, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        # Check if already submitted
        existing = await db.test_submissions.find_one(
            {"test_id": submission.test_id, "student_id": current_user["id"]},
            {"_id": 0}
        )
        if existing:
            raise HTTPException(status_code=400, detail="Test already submitted")
    
    # Get test details
    test = await db.tests.find_one({"id": submission.test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Calculate score
    score = 0
    total_questions = len(test["questions"])
    
    for answer in submission.answers:
        if answer.question_index < total_questions:
            correct_answer = test["questions"][answer.question_index]["correct_answer"]
            if answer.selected_answer.upper() == correct_answer.upper():
                score += 1
    
    test_submission = TestSubmission(
        test_id=submission.test_id,
        student_id=current_user["id"],
        answers=[a.model_dump() for a in submission.answers],
        score=score,
        total_questions=total_questions
    )
    
    doc = test_submission.model_dump()
    doc['submitted_at'] = doc['submitted_at'].isoformat()
    await db.test_submissions.insert_one(doc)
    
    return test_submission

@api_router.get("/tests/{test_id}/result")
async def get_test_result(test_id: str, current_user: dict = Depends(get_current_user)):
    submission = await db.test_submissions.find_one(
        {"test_id": test_id, "student_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not submission:
        raise HTTPException(status_code=404, detail="Test not submitted yet")
    
    # Get test details with correct answers
    test = await db.tests.find_one({"id": test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if isinstance(submission.get('submitted_at'), str):
        submission['submitted_at'] = datetime.fromisoformat(submission['submitted_at'])
    
    return {
        "submission": submission,
        "test": test
    }

@api_router.delete("/tests/{test_id}")
async def delete_test(test_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete tests")
    
    result = await db.tests.delete_one({"id": test_id, "created_by": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Also delete submissions
    await db.test_submissions.delete_many({"test_id": test_id})
    
    return {"message": "Test deleted successfully"}

@api_router.get("/tests/{test_id}/submissions")
async def get_test_submissions(test_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view submissions")
    
    submissions = await db.test_submissions.find({"test_id": test_id}, {"_id": 0}).to_list(1000)
    
    # Get student details for each submission
    for sub in submissions:
        student = await db.users.find_one({"id": sub["student_id"]}, {"_id": 0, "password_hash": 0})
        sub["student_name"] = student["name"] if student else "Unknown"
        if isinstance(sub.get('submitted_at'), str):
            sub['submitted_at'] = datetime.fromisoformat(sub['submitted_at'])
    
    return submissions

@api_router.get("/my-test-results")
async def get_my_test_results(current_user: dict = Depends(get_current_user)):
    """Get all test results for the current student"""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can view their test results")
    
    # Get all submissions for this student
    submissions = await db.test_submissions.find(
        {"student_id": current_user["id"]}, 
        {"_id": 0}
    ).sort("submitted_at", -1).to_list(1000)
    
    # Get test details for each submission
    results = []
    for sub in submissions:
        test = await db.tests.find_one({"id": sub["test_id"]}, {"_id": 0})
        if test:
            # Get class details
            class_obj = await db.classes.find_one({"id": test["class_id"]}, {"_id": 0})
            
            if isinstance(sub.get('submitted_at'), str):
                sub['submitted_at'] = datetime.fromisoformat(sub['submitted_at'])
            if isinstance(test.get('created_at'), str):
                test['created_at'] = datetime.fromisoformat(test['created_at'])
            
            results.append({
                "submission": sub,
                "test": test,
                "class_name": class_obj["name"] if class_obj else "Unknown Class"
            })
    
    return results

# ==== FILE UPLOAD ROUTE ====

@api_router.post("/upload")
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a file with comprehensive security validation:
    - Rate limiting (10 uploads per minute)
    - Extension validation
    - MIME type verification
    - Virus scanning (ClamAV)
    - Size validation (5MB max)
    """
    
    # Sanitize filename
    sanitized_filename = sanitize_string(file.filename, max_length=255)
    if not sanitized_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check file extension
    file_ext = Path(sanitized_filename).suffix.lower()
    
    # Security check - reject dangerous files
    if file_ext in DANGEROUS_EXTENSIONS:
        log_security_event('dangerous_file_upload_attempt', {
            'user_id': current_user['id'],
            'filename': sanitized_filename,
            'extension': file_ext
        })
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{file_ext}' is not allowed for security reasons"
        )
    
    # Check if extension is allowed
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size by reading in chunks
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    # Read file to check size
    temp_content = []
    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            file_size += len(chunk)
            temp_content.append(chunk)
            
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum allowed size of 5MB. Your file is {file_size / (1024*1024):.2f}MB"
                )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file temporarily for validation
    try:
        with open(file_path, "wb") as f:
            for chunk in temp_content:
                f.write(chunk)
        
        # Perform comprehensive security validation
        # This includes MIME type validation and virus scanning
        validation_results = await validate_uploaded_file(
            file=file,
            temp_path=file_path,
            allowed_extensions=ALLOWED_EXTENSIONS,
            max_size=MAX_FILE_SIZE
        )
        
        # Log successful upload
        log_security_event('file_upload_success', {
            'user_id': current_user['id'],
            'filename': sanitized_filename,
            'unique_filename': unique_filename,
            'size': file_size,
            'mime_type': validation_results.get('mime_type'),
            'virus_scan_clean': validation_results.get('virus_scan_clean')
        })
        
        logger.info(f"File uploaded: {unique_filename} by user {current_user['id']}")
        
        return {
            "url": f"/uploads/{unique_filename}",
            "filename": sanitized_filename,
            "size": file_size,
            "security_validated": True,
            "mime_type": validation_results.get('mime_type')
        }
        
    except HTTPException:
        # Clean up if validation fails
        if file_path.exists():
            file_path.unlink()
        raise
    except Exception as e:
        # Clean up if save fails
        if file_path.exists():
            file_path.unlink()
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

# ==== INIT ROUTE ====

@api_router.get("/")
async def root():
    return {"message": "EdifyMinds Junior API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_db():
    # Create uploads directory if it doesn't exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Uploads directory ready at: {UPLOAD_DIR}")
    
    # Create database indexes for performance optimization
    logger.info("Creating database indexes...")
    try:
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.users.create_index("role")
        await db.users.create_index("name")
        
        # Classes collection indexes
        await db.classes.create_index("id", unique=True)
        await db.classes.create_index("teacher_id")
        
        # Enrollments collection indexes
        await db.enrollments.create_index("id", unique=True)
        await db.enrollments.create_index("student_id")
        await db.enrollments.create_index("class_id")
        await db.enrollments.create_index([("student_id", 1), ("class_id", 1)])
        
        # Homework collection indexes
        await db.homework.create_index("id", unique=True)
        await db.homework.create_index("class_id")
        
        # Notices collection indexes
        await db.notices.create_index("id", unique=True)
        await db.notices.create_index("class_id")
        
        # Resources collection indexes
        await db.resources.create_index("id", unique=True)
        await db.resources.create_index("class_id")
        
        # Tests collection indexes
        await db.tests.create_index("id", unique=True)
        await db.tests.create_index("class_id")
        
        # Test submissions collection indexes
        await db.test_submissions.create_index("id", unique=True)
        await db.test_submissions.create_index("test_id")
        await db.test_submissions.create_index("student_id")
        await db.test_submissions.create_index([("test_id", 1), ("student_id", 1)])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
    
    # Initialize default teacher if doesn't exist
    existing_teacher = await db.users.find_one({"email": "edify@gmail.com"}, {"_id": 0})
    if not existing_teacher:
        # Use threadpool for password hashing to avoid blocking
        password_hash = await run_in_threadpool(get_password_hash, "edify123")
        teacher = User(
            email="edify@gmail.com",
            password_hash=password_hash,
            name="EdifyMinds Teacher",
            role="teacher"
        )
        doc = teacher.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logger.info("Default teacher account created: edify@gmail.com / edify123")

# Create uploads directory before mounting
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
