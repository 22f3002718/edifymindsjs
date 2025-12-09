"""
File security utilities for MIME type validation and virus scanning
"""
import magic
import os
import logging
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

# ==== FILE TYPE VALIDATION ====

# Mapping of allowed MIME types to file extensions
ALLOWED_MIME_TYPES = {
    # Documents
    'application/pdf': ['.pdf'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/plain': ['.txt'],
    'application/vnd.ms-powerpoint': ['.ppt'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    
    # Images
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp'],
    
    # Archives
    'application/zip': ['.zip'],
    'application/x-zip-compressed': ['.zip'],
}

# Dangerous MIME types that should never be allowed
DANGEROUS_MIME_TYPES = {
    'application/x-executable',
    'application/x-dosexec',
    'application/x-msdownload',
    'application/x-sh',
    'application/x-python',
    'application/x-bat',
    'application/x-java-archive',
    'text/x-python',
    'text/x-shellscript',
}

def get_file_mime_type(file_path: Path) -> str:
    """
    Get the MIME type of a file using python-magic.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string
    """
    try:
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))
        logger.info(f"Detected MIME type for {file_path.name}: {mime_type}")
        return mime_type
    except Exception as e:
        logger.error(f"Error detecting MIME type: {e}")
        raise HTTPException(status_code=500, detail="Could not determine file type")

def validate_file_extension(filename: str, allowed_extensions: set) -> str:
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions (e.g., {'.pdf', '.jpg'})
        
    Returns:
        The file extension in lowercase
        
    Raises:
        HTTPException: If extension is not allowed
    """
    ext = Path(filename).suffix.lower()
    
    if not ext:
        raise HTTPException(status_code=400, detail="File must have an extension")
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed types: {', '.join(sorted(allowed_extensions))}"
        )
    
    return ext

def validate_mime_type(mime_type: str, file_extension: str) -> bool:
    """
    Validate that MIME type matches the file extension and is allowed.
    
    Args:
        mime_type: Detected MIME type
        file_extension: File extension (with dot, e.g., '.pdf')
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If MIME type is invalid or doesn't match extension
    """
    # Check for dangerous MIME types
    if mime_type in DANGEROUS_MIME_TYPES:
        logger.warning(f"Blocked dangerous MIME type: {mime_type}")
        raise HTTPException(
            status_code=400,
            detail="This file type is not allowed for security reasons"
        )
    
    # Check if MIME type is in allowed list
    if mime_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Blocked unallowed MIME type: {mime_type}")
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Detected type: {mime_type}"
        )
    
    # Verify MIME type matches extension
    expected_extensions = ALLOWED_MIME_TYPES[mime_type]
    if file_extension not in expected_extensions:
        logger.warning(f"MIME type {mime_type} doesn't match extension {file_extension}")
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_extension} doesn't match actual file type"
        )
    
    return True

# ==== VIRUS SCANNING ====

def check_clamav_available() -> bool:
    """
    Check if ClamAV daemon is available.
    
    Returns:
        True if ClamAV is available, False otherwise
    """
    try:
        import pyclamd
        cd = pyclamd.ClamdUnixSocket()
        # Try to ping the daemon
        if cd.ping():
            logger.info("ClamAV daemon is available")
            return True
    except Exception as e:
        logger.info(f"ClamAV not available: {e}")
    
    return False

def scan_file_for_viruses(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Scan a file for viruses using ClamAV.
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        Tuple of (is_clean, virus_name)
        - is_clean: True if file is clean or ClamAV unavailable, False if virus detected
        - virus_name: Name of virus if detected, None otherwise
    """
    try:
        import pyclamd
        
        # Connect to ClamAV daemon
        cd = pyclamd.ClamdUnixSocket()
        
        if not cd.ping():
            logger.warning("ClamAV daemon not responding, skipping virus scan")
            return True, None
        
        # Scan the file
        result = cd.scan_file(str(file_path))
        
        if result is None:
            # File is clean
            logger.info(f"File {file_path.name} passed virus scan")
            return True, None
        else:
            # Virus detected
            virus_info = result[str(file_path)]
            virus_name = virus_info[1] if virus_info else "Unknown"
            logger.error(f"VIRUS DETECTED in {file_path.name}: {virus_name}")
            return False, virus_name
            
    except ImportError:
        logger.warning("pyclamd not installed, skipping virus scan")
        return True, None
    except Exception as e:
        logger.warning(f"Error during virus scan: {e}, allowing file")
        return True, None

# ==== COMPREHENSIVE FILE VALIDATION ====

async def validate_uploaded_file(
    file: UploadFile,
    temp_path: Path,
    allowed_extensions: set,
    max_size: int
) -> dict:
    """
    Perform comprehensive validation on an uploaded file.
    
    Args:
        file: FastAPI UploadFile object
        temp_path: Path where file is temporarily saved
        allowed_extensions: Set of allowed extensions
        max_size: Maximum file size in bytes
        
    Returns:
        Dict with validation results
        
    Raises:
        HTTPException: If any validation fails
    """
    validation_results = {
        'filename': file.filename,
        'extension_valid': False,
        'mime_type_valid': False,
        'virus_scan_clean': False,
        'size_valid': False,
        'mime_type': None,
    }
    
    try:
        # 1. Validate extension
        file_extension = validate_file_extension(file.filename, allowed_extensions)
        validation_results['extension_valid'] = True
        validation_results['extension'] = file_extension
        
        # 2. Validate file size
        file_size = temp_path.stat().st_size
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB"
            )
        validation_results['size_valid'] = True
        validation_results['size'] = file_size
        
        # 3. Validate MIME type
        mime_type = get_file_mime_type(temp_path)
        validation_results['mime_type'] = mime_type
        validate_mime_type(mime_type, file_extension)
        validation_results['mime_type_valid'] = True
        
        # 4. Scan for viruses
        is_clean, virus_name = scan_file_for_viruses(temp_path)
        if not is_clean:
            # Delete the infected file immediately
            temp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=f"File rejected: virus detected ({virus_name})"
            )
        validation_results['virus_scan_clean'] = True
        
        logger.info(f"File validation successful: {file.filename}")
        return validation_results
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"File validation error: {e}")
        raise HTTPException(status_code=500, detail="File validation failed")

def log_security_event(event_type: str, details: dict):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event (e.g., 'file_upload', 'virus_detected')
        details: Dictionary with event details
    """
    logger.warning(f"SECURITY EVENT [{event_type}]: {details}")
