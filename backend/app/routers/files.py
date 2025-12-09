from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address
from pathlib import Path
import uuid
import logging

from app.core.security import get_current_user
from app.core.security_utils import sanitize_string
from app.core.file_security import validate_uploaded_file, log_security_event

router = APIRouter(tags=["Files"])
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)

# Config
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.txt', '.ppt', '.pptx', '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.zip'
}
DANGEROUS_EXTENSIONS = {'.exe', '.sh', '.py', '.bat', '.cmd', '.ps1', '.jar', '.app'}

@router.post("/upload")
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
    
    # Ensure upload dir exists
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
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
