# Security Features Documentation

## Overview

This document describes the comprehensive security enhancements implemented in the EdifyMinds Junior platform to protect against common web vulnerabilities and attacks.

## Implemented Security Features

### 1. Rate Limiting

Rate limiting prevents API abuse and brute-force attacks by limiting the number of requests per time period.

#### Configuration

- **Authentication Endpoints**: 5 requests/minute
  - `/api/auth/register`
  - `/api/auth/login`
- **File Upload Endpoint**: 10 requests/minute
  - `/api/upload`
- **General Content Creation**: 30 requests/minute
  - `/api/classes`
  - `/api/homework`
  - `/api/notices`
  - `/api/resources`
  - `/api/tests`
  - `/api/tests/submit`

#### Implementation

Uses `slowapi` library with IP-based rate limiting. When limits are exceeded, the API returns a `429 Too Many Requests` status code.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@api_router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # Login logic
```

#### Benefits

- Prevents brute-force password attacks
- Protects against credential stuffing
- Prevents API abuse and DoS attacks
- Reduces spam and automated attacks

---

### 2. Input Sanitization & NoSQL Injection Protection

All user inputs are sanitized to prevent XSS attacks, SQL/NoSQL injection, and malicious content.

#### Features

**String Sanitization:**
- Removes all HTML tags using `bleach` library
- Limits string length to prevent buffer overflow
- Strips dangerous characters
- Preserves safe content

**Email Sanitization:**
- Validates email format with regex
- Converts to lowercase
- Strips whitespace
- Prevents email injection attacks

**Name Sanitization:**
- Allows only letters, spaces, hyphens, apostrophes, dots
- Removes dangerous characters
- Prevents XSS in name fields

**URL Sanitization:**
- Validates URL format
- Ensures proper protocol (http/https)
- Limits URL length
- Prevents javascript: and data: URL attacks

**NoSQL Injection Protection:**
- Sanitizes MongoDB query operators
- Prevents $where, $regex, and other operator injection
- Validates all ID fields (UUID format)
- Logs suspicious query attempts

#### Implementation

```python
from security_utils import (
    sanitize_string, 
    sanitize_email, 
    sanitize_name,
    sanitize_mongo_query,
    validate_object_id
)

# Sanitize user input
sanitized_email = sanitize_email(user_input.email)
sanitized_name = sanitize_name(user_input.name)

# Protect MongoDB queries
user = await db.users.find_one(
    sanitize_mongo_query({"email": sanitized_email})
)
```

#### Protected Endpoints

All endpoints that accept user input are protected:
- User registration and profile updates
- Class creation and updates
- Homework, notices, and resource creation
- Test creation with question parsing
- File uploads

#### Benefits

- Prevents XSS (Cross-Site Scripting) attacks
- Blocks NoSQL injection attempts
- Protects against HTML/JavaScript injection
- Prevents data corruption from malformed input
- Maintains data integrity

---

### 3. File Upload Security Enhancement

Comprehensive file validation beyond simple extension checks.

#### MIME Type Validation

**Technology:** Uses `python-magic` library to detect actual file content, not just extension.

**Process:**
1. File is saved temporarily
2. Magic bytes are read to determine true file type
3. MIME type is validated against whitelist
4. MIME type is cross-verified with file extension
5. Dangerous MIME types are blocked

**Allowed MIME Types:**
- **Documents**: PDF, DOC, DOCX, TXT, PPT, PPTX, XLS, XLSX
- **Images**: JPEG, PNG, GIF, WebP
- **Archives**: ZIP

**Blocked MIME Types:**
- Executables (application/x-executable)
- Shell scripts (text/x-shellscript)
- Python scripts (text/x-python)
- Batch files, JAR files, etc.

```python
from file_security import validate_uploaded_file

# Comprehensive validation
validation_results = await validate_uploaded_file(
    file=file,
    temp_path=file_path,
    allowed_extensions=ALLOWED_EXTENSIONS,
    max_size=MAX_FILE_SIZE
)
```

#### Virus Scanning with ClamAV

**Technology:** Integrates with ClamAV antivirus daemon for real-time scanning.

**Process:**
1. Check if ClamAV daemon is available
2. If available, scan the uploaded file
3. If virus detected, delete file immediately and reject upload
4. If ClamAV unavailable, gracefully continue (logged)
5. Log all scan results

**Features:**
- Real-time virus detection
- Automatic infected file deletion
- Graceful fallback if ClamAV unavailable
- Comprehensive logging of security events

```python
from file_security import scan_file_for_viruses

is_clean, virus_name = scan_file_for_viruses(file_path)
if not is_clean:
    file_path.unlink()  # Delete infected file
    raise HTTPException(400, f"Virus detected: {virus_name}")
```

#### File Upload Validation Pipeline

1. **Extension Validation** - Check file extension against whitelist
2. **Size Validation** - Ensure file doesn't exceed 5MB limit
3. **MIME Type Validation** - Verify actual file type matches extension
4. **Virus Scanning** - Scan for malware with ClamAV
5. **Unique Naming** - Generate UUID-based filename
6. **Security Logging** - Log all upload attempts and results

#### Benefits

- Prevents upload of malicious executables disguised as documents
- Detects malware and viruses in uploaded files
- Protects against file type confusion attacks
- Prevents double-extension exploits (e.g., file.pdf.exe)
- Comprehensive audit trail of all file operations

---

## Security Logging

All security-relevant events are logged for audit and monitoring:

### Logged Events

- User registration and login attempts
- Failed login attempts (with IP address)
- Successful authentication
- File upload attempts with validation results
- Dangerous file upload attempts (blocked)
- Virus detection events
- NoSQL injection attempts
- Rate limit violations

### Log Format

```python
log_security_event('event_type', {
    'user_id': '...',
    'details': '...',
    'ip': '...'
})
```

### Log Location

Security logs are written to the application logs:
- `/var/log/supervisor/backend.err.log` - Errors and warnings
- Application logger - All security events

---

## Installation & Setup

### Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Required packages:**
- `slowapi==0.1.9` - Rate limiting
- `bleach==6.2.0` - HTML sanitization
- `python-magic==0.4.27` - MIME type detection
- `pyclamd==0.4.0` - ClamAV integration

### System Dependencies

```bash
# Install libmagic for MIME type detection
apt-get install -y libmagic1 file

# Install ClamAV for virus scanning (optional but recommended)
apt-get install -y clamav clamav-daemon

# Start ClamAV daemon (optional)
systemctl start clamav-daemon
systemctl enable clamav-daemon

# Update virus definitions (if using ClamAV)
freshclam
```

### Configuration

No additional configuration needed. Security features are enabled by default.

**ClamAV Note:** If ClamAV is not installed or not running, the system will gracefully skip virus scanning and log a warning. All other security features will continue to work.

---

## Testing Security Features

### Test Rate Limiting

```bash
# Try login multiple times rapidly (should get 429 after 5 attempts)
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}';
done
```

### Test Input Sanitization

```bash
# Try XSS attack in name field
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"malicious@example.com",
    "password":"test123",
    "name":"<script>alert(\"XSS\")</script>",
    "role":"student"
  }'

# Name should be sanitized, no script tags in response
```

### Test MIME Type Validation

```bash
# Try uploading executable with .pdf extension
# 1. Create a fake PDF (actually an executable)
echo "#!/bin/bash\necho 'malicious'" > fake.pdf

# 2. Try to upload it
curl -X POST http://localhost:8001/api/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@fake.pdf"

# Should be rejected due to MIME type mismatch
```

### Test NoSQL Injection

```bash
# Try NoSQL injection in login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":{"$ne":""},"password":{"$ne":""}}'

# Should be rejected or sanitized
```

---

## Security Best Practices

### For Deployment

1. **Enable HTTPS** - Always use SSL/TLS in production
2. **Configure CORS** - Restrict allowed origins
3. **Enable ClamAV** - Install and run ClamAV daemon for virus scanning
4. **Monitor Logs** - Regularly review security logs
5. **Update Dependencies** - Keep all libraries up to date
6. **Set Strong Secrets** - Use strong JWT_SECRET_KEY
7. **Limit File Sizes** - Current 5MB limit is reasonable
8. **Regular Backups** - Backup database and uploaded files

### For Developers

1. **Never Disable Security** - Don't bypass sanitization
2. **Validate All Input** - Use sanitization functions for all user input
3. **Test Security** - Include security tests in test suite
4. **Log Suspicious Activity** - Use log_security_event for security events
5. **Review Code** - Look for potential injection points
6. **Keep It Updated** - Regularly update security libraries

---

## Security Considerations

### ClamAV Performance

- Virus scanning adds ~100-500ms latency per file
- Consider for production based on file upload volume
- Graceful degradation if ClamAV unavailable

### Rate Limiting

- IP-based limiting may affect users behind NAT
- Consider token-based limiting for authenticated users
- Adjust limits based on usage patterns

### Input Sanitization

- May remove legitimate special characters
- Test with real-world data
- Balance security with usability

---

## Vulnerability Disclosure

If you discover a security vulnerability, please report it responsibly:

1. **Do not** post publicly
2. Email security details to the development team
3. Allow time for patches before disclosure
4. We appreciate responsible disclosure

---

## Compliance

These security features help comply with:

- **OWASP Top 10** - Protection against most common web vulnerabilities
- **GDPR** - Data protection and privacy requirements
- **PCI DSS** - If handling payment data (additional measures needed)

---

## Security Checklist

- [x] Rate limiting on authentication endpoints
- [x] Rate limiting on file uploads
- [x] Input sanitization for all user inputs
- [x] NoSQL injection protection
- [x] MIME type validation
- [x] Virus scanning integration
- [x] Security event logging
- [x] UUID-based file naming
- [x] File size validation
- [x] Extension whitelist/blacklist
- [ ] HTTPS/TLS (deployment configuration)
- [ ] CORS configuration (deployment configuration)
- [ ] Content Security Policy headers (deployment configuration)

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NoSQL Injection](https://owasp.org/www-community/attacks/NoSQL_Injection)
- [File Upload Vulnerabilities](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [ClamAV Documentation](https://docs.clamav.net/)
- [slowapi Documentation](https://github.com/laurents/slowapi)
- [bleach Documentation](https://bleach.readthedocs.io/)

---

## Version

- **Document Version**: 1.0
- **Last Updated**: December 2025
- **Security Features Version**: 1.0
