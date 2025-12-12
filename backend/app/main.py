from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import db_instance
from app.routers import auth

# Initialize FastAPI
app = FastAPI(title="EdifyMinds Junior Modular API")

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Connection Events
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from app.core.config import settings
from app.core.database import db_instance
from app.routers import auth, classes, admin, tests, resources, files

# Initialize FastAPI
app = FastAPI(title="EdifyMinds Junior Modular API")

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Configuration
@app.on_event("startup")
async def startup_db_client():
    db_instance.connect()
    
    # Mount Static Files for Uploads
    UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
    
    # Create database indexes
    db = db_instance.db
    logging.info("Creating database indexes...")
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
        
        # Other indexes
        await db.homework.create_index("class_id")
        await db.notices.create_index("class_id")
        await db.resources.create_index("class_id")
        await db.tests.create_index("class_id")
        await db.test_submissions.create_index([("test_id", 1), ("student_id", 1)])
        
        logging.info("Database indexes created successfully")
    except Exception as e:
        logging.error(f"Error creating indexes: {e}")

    # Seed Default Users
    from app.models.schemas import User
    from app.core.security import get_password_hash
    from starlette.concurrency import run_in_threadpool

    # Initialize default teacher if doesn't exist
    existing_teacher = await db.users.find_one({"email": "edify@gmail.com"}, {"_id": 0})
    if not existing_teacher:
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
        logging.info("Default teacher account created: edify@gmail.com")

    # Initialize default admin if doesn't exist
    existing_admin = await db.users.find_one({"email": "admin@edify.com"}, {"_id": 0})
    if not existing_admin:
        password_hash = await run_in_threadpool(get_password_hash, "admin123")
        admin = User(
            email="admin@edify.com",
            password_hash=password_hash,
            name="System Admin",
            role="admin"
        )
        doc = admin.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logging.info("Default admin account created: admin@edify.com")

@app.on_event("shutdown")
async def shutdown_db_client():
    db_instance.close()

# Include Routers
app.include_router(auth.router, prefix="/api")
app.include_router(classes.router, prefix="/api")
app.include_router(admin.router, prefix="/api") # Note: admin module sets its own /admin prefix? No, it sets /admin, so /api/admin
app.include_router(tests.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(files.router, prefix="/api")

# Root Endpoint
@app.get("/")
async def root():
    return {"message": "EdifyMinds Junior API (Modular Edition)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
