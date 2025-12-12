from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    name: str
    role: str  # "teacher" or "student" or "admin"
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

class PasswordResetRequest(BaseModel):
    new_password: str

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

# Test Models (Need to inspect server.py further for these if they weren't in first 200 lines, 
# but I saw them in previous outputs. I'll add them here.)
class TestQuestion(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str  # "A", "B", "C", or "D"
    marks: int = 1

class Test(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    title: str
    description: str
    start_time: str
    duration_minutes: int
    questions: List[TestQuestion]
    created_by: str  # teacher_id
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TestCreate(BaseModel):
    class_id: str
    title: str
    description: str
    start_time: str
    duration_minutes: int
    questions: List[TestQuestion]

class Answer(BaseModel):
    question_index: int
    selected_answer: str

class TestSubmit(BaseModel):
    test_id: str
    answers: List[Answer]

class TestSubmission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    student_id: str
    answers: List[dict]  # Storing as dict to simplify
    score: int
    total_questions: int
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
