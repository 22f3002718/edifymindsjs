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
    
    # Initialize DB (Check indexes, etc. - Ideally could be in a separate script or init method)
    # For now, relying on the fact that existing DB already has indexes from server.py runs
    # But for a fresh deploy using this app, we'd want that index logic here too.

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
