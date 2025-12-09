"""
Security utilities for input sanitization, validation, and protection
"""
import re
import bleach
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# ==== INPUT SANITIZATION ====

# Allowed HTML tags and attributes (very restrictive for safety)
ALLOWED_TAGS = []  # No HTML tags allowed
ALLOWED_ATTRIBUTES = {}

def sanitize_string(text: Optional[str], max_length: int = 10000) -> Optional[str]:
    """
    Sanitize string input by removing HTML tags and limiting length.
    
    Args:
        text: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string or None if input was None
    """
    if text is None:
        return None
    
    if not isinstance(text, str):
        text = str(text)
    
    # Remove HTML tags
    sanitized = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    
    # Trim to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def sanitize_email(email: str) -> str:
    """
    Sanitize email address.
    
    Args:
        email: Email address to sanitize
        
    Returns:
        Sanitized email in lowercase
    """
    if not email:
        return ""
    
    # Convert to lowercase and strip whitespace
    email = email.lower().strip()
    
    # Basic email format validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    return email

def sanitize_name(name: str, max_length: int = 100) -> str:
    """
    Sanitize name field (allows letters, spaces, hyphens, apostrophes).
    
    Args:
        name: Name to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized name
    """
    if not name:
        return ""
    
    # Remove HTML and dangerous characters
    name = bleach.clean(name, tags=[], attributes={}, strip=True)
    
    # Allow only letters, spaces, hyphens, apostrophes, and dots
    name = re.sub(r"[^a-zA-Z\s\-'.()]", "", name)
    
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Limit length
    if len(name) > max_length:
        name = name[:max_length]
    
    return name

def sanitize_url(url: Optional[str]) -> Optional[str]:
    """
    Sanitize URL field.
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL or None
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Basic URL validation
    url_pattern = r'^https?://'
    if not re.match(url_pattern, url, re.IGNORECASE):
        # If no protocol, add https
        if not url.startswith(('http://', 'https://', '/uploads/')):
            url = 'https://' + url
    
    return url[:2000]  # Limit URL length

# ==== NoSQL INJECTION PROTECTION ====

def sanitize_mongo_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize MongoDB query to prevent NoSQL injection.
    
    Args:
        query: MongoDB query dictionary
        
    Returns:
        Sanitized query dictionary
    """
    if not isinstance(query, dict):
        return {}
    
    sanitized = {}
    for key, value in query.items():
        # Check for MongoDB operators
        if isinstance(key, str) and key.startswith('$'):
            logger.warning(f"Potentially dangerous MongoDB operator detected: {key}")
            continue
        
        # Recursively sanitize nested dictionaries
        if isinstance(value, dict):
            # Check for dangerous operators in values
            has_operator = any(k.startswith('$') for k in value.keys() if isinstance(k, str))
            if has_operator:
                logger.warning(f"Potentially dangerous MongoDB operator in value for key: {key}")
                # Only allow safe comparison operators
                safe_operators = {'$eq', '$ne', '$gt', '$gte', '$lt', '$lte', '$in', '$nin'}
                sanitized_value = {k: v for k, v in value.items() 
                                 if isinstance(k, str) and k in safe_operators}
                if sanitized_value:
                    sanitized[key] = sanitized_value
            else:
                sanitized[key] = sanitize_mongo_query(value)
        elif isinstance(value, list):
            # Sanitize list items
            sanitized[key] = [sanitize_mongo_query(item) if isinstance(item, dict) else item 
                            for item in value]
        else:
            sanitized[key] = value
    
    return sanitized

def validate_object_id(obj_id: str, field_name: str = "id") -> str:
    """
    Validate that an ID is in UUID format (not MongoDB ObjectId).
    
    Args:
        obj_id: ID to validate
        field_name: Name of the field (for error messages)
        
    Returns:
        Validated ID
        
    Raises:
        ValueError: If ID format is invalid
    """
    if not obj_id:
        raise ValueError(f"{field_name} is required")
    
    # UUID pattern (with or without hyphens)
    uuid_pattern = r'^[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}$'
    if not re.match(uuid_pattern, obj_id.lower()):
        raise ValueError(f"Invalid {field_name} format")
    
    return obj_id

# ==== DATA VALIDATION ====

def validate_and_sanitize_user_input(data: Dict[str, Any], schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Validate and sanitize user input based on a schema.
    
    Args:
        data: Input data dictionary
        schema: Schema defining field types (e.g., {'name': 'name', 'email': 'email', 'bio': 'string'})
        
    Returns:
        Sanitized data dictionary
    """
    sanitized = {}
    
    for field, field_type in schema.items():
        if field not in data:
            continue
        
        value = data[field]
        
        if field_type == 'email':
            sanitized[field] = sanitize_email(value)
        elif field_type == 'name':
            sanitized[field] = sanitize_name(value)
        elif field_type == 'string':
            sanitized[field] = sanitize_string(value)
        elif field_type == 'url':
            sanitized[field] = sanitize_url(value)
        elif field_type == 'id':
            sanitized[field] = validate_object_id(value, field)
        else:
            sanitized[field] = value
    
    return sanitized

def sanitize_test_questions(questions_text: str) -> str:
    """
    Sanitize test questions text while preserving formatting.
    
    Args:
        questions_text: Raw test questions text
        
    Returns:
        Sanitized questions text
    """
    if not questions_text:
        return ""
    
    # Remove dangerous HTML but preserve line breaks
    sanitized = bleach.clean(questions_text, tags=[], attributes={}, strip=True)
    
    # Limit total length
    max_length = 50000  # Allow longer for multiple questions
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

# ==== RATE LIMITING HELPERS ====

def get_rate_limit_key(request_type: str, identifier: str) -> str:
    """
    Generate a unique key for rate limiting.
    
    Args:
        request_type: Type of request (e.g., 'login', 'upload')
        identifier: User identifier (IP, user_id, etc.)
        
    Returns:
        Rate limit key
    """
    return f"rate_limit:{request_type}:{identifier}"
