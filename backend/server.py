from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
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

# ==== AUTHENTICATION ROUTES ====

@api_router.post("/auth/register", response_model=Token)
async def register(user_input: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_input.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_input.email,
        password_hash=get_password_hash(user_input.password),
        name=user_input.name,
        role=user_input.role,
        parent_contact=user_input.parent_contact
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user={"id": user.id, "email": user.email, "name": user.name, "role": user.role}
    )

@api_router.post("/auth/login", response_model=Token)
async def login(user_input: UserLogin):
    user = await db.users.find_one({"email": user_input.email}, {"_id": 0})
    if not user or not verify_password(user_input.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
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
async def create_class(class_input: ClassCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create classes")
    
    class_obj = Class(**class_input.model_dump(), teacher_id=current_user["id"])
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
async def create_homework(homework_input: HomeworkCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create homework")
    
    homework = Homework(**homework_input.model_dump())
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
    result = await db.homework.delete_one({"id": homework_id})
    
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
async def create_notice(notice_input: NoticeCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create notices")
    
    notice = Notice(**notice_input.model_dump(), created_by=current_user["id"])
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
async def create_resource(resource_input: ResourceCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can add resources")
    
    resource = Resource(**resource_input.model_dump())
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
    result = await db.resources.delete_one({"id": resource_id})
    
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
async def create_test(test_input: TestCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create tests")
    
    # Parse questions from text
    try:
        questions = parse_questions(test_input.questions_text)
        if not questions:
            raise HTTPException(status_code=400, detail="No valid questions found in the text")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing questions: {str(e)}")
    
    test = Test(
        class_id=test_input.class_id,
        title=test_input.title,
        description=test_input.description,
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
async def submit_test(submission: TestSubmit, current_user: dict = Depends(get_current_user)):
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
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a file (max 5MB) for resources or homework"""
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    
    # Security check - reject dangerous files
    if file_ext in DANGEROUS_EXTENSIONS:
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
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            for chunk in temp_content:
                f.write(chunk)
        
        logger.info(f"File uploaded: {unique_filename} by user {current_user['id']}")
        
        return {
            "url": f"/uploads/{unique_filename}",
            "filename": file.filename,
            "size": file_size
        }
    except Exception as e:
        # Clean up if save fails
        if file_path.exists():
            file_path.unlink()
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
    
    # Initialize default teacher if doesn't exist
    existing_teacher = await db.users.find_one({"email": "edify@gmail.com"}, {"_id": 0})
    if not existing_teacher:
        teacher = User(
            email="edify@gmail.com",
            password_hash=get_password_hash("edify123"),
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
