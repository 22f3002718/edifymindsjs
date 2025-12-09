from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.concurrency import run_in_threadpool
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user
from app.core.security_utils import sanitize_email, sanitize_name, sanitize_string, sanitize_mongo_query
from app.models.schemas import User, UserCreate, UserLogin, Token
# Note: For logging, we assume a standard logging setup or import from file_security if it has generic logging
from app.core.file_security import log_security_event

router = APIRouter(prefix="/auth", tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)

@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
async def register(request: Request, user_input: UserCreate):
    """Register a new user with rate limiting and input sanitization"""
    db = get_db()
    
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

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user_input: UserLogin):
    """Login with rate limiting and input sanitization"""
    db = get_db()
    
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

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "email": current_user["email"], "name": current_user["name"], "role": current_user["role"]}
