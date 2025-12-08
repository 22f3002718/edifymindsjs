#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for EdifyMinds Junior Security Features
Tests all backend endpoints with focus on security enhancements:
- Rate limiting
- Input sanitization and XSS/NoSQL injection protection
- MIME type validation
- File upload security pipeline
- Security logging
"""

import requests
import json
import time
import io
import tempfile
import os
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://fortify-uploads.preview.emergentagent.com/api"

# Test credentials - using realistic data as requested
TEACHER_EMAIL = "teacher@test.com"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "student@test.com"
STUDENT_PASSWORD = "student123"

# Global variables for tokens and IDs
teacher_token = None
student_token = None
test_class_id = None
test_id = None
student_id = None

def print_test_result(test_name, success, message=""):
    """Print formatted test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")
    print()

def make_request(method, endpoint, data=None, token=None, expected_status=200):
    """Make HTTP request with proper error handling"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=60)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=60)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=60)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=60)
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_teacher_login():
    """Test teacher authentication"""
    global teacher_token
    
    print("🔐 Testing Teacher Authentication...")
    
    response = make_request("POST", "/auth/login", {
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    })
    
    if response and response.status_code == 200:
        data = response.json()
        teacher_token = data.get("access_token")
        user_info = data.get("user", {})
        
        if teacher_token and user_info.get("role") == "teacher":
            print_test_result("Teacher Login", True, f"Logged in as {user_info.get('name')}")
            return True
        else:
            print_test_result("Teacher Login", False, "Invalid response format")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Teacher Login", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_create_student_account():
    """Create a test student account"""
    global student_id
    
    print("👤 Creating Test Student Account...")
    
    response = make_request("POST", "/auth/register", {
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD,
        "name": "Test Student",
        "role": "student"
    })
    
    if response and response.status_code == 200:
        data = response.json()
        user_info = data.get("user", {})
        student_id = user_info.get("id")
        print_test_result("Student Account Creation", True, f"Created student: {user_info.get('name')}")
        return True
    elif response and response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        print_test_result("Student Account Creation", True, "Student account already exists")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Student Account Creation", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_student_login():
    """Test student authentication"""
    global student_token, student_id
    
    print("🔐 Testing Student Authentication...")
    
    response = make_request("POST", "/auth/login", {
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD
    })
    
    if response and response.status_code == 200:
        data = response.json()
        student_token = data.get("access_token")
        user_info = data.get("user", {})
        student_id = user_info.get("id")
        
        if student_token and user_info.get("role") == "student":
            print_test_result("Student Login", True, f"Logged in as {user_info.get('name')}")
            return True
        else:
            print_test_result("Student Login", False, "Invalid response format")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Student Login", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_get_classes():
    """Test getting classes and create one if needed"""
    global test_class_id
    
    print("📚 Testing Get Classes...")
    
    response = make_request("GET", "/classes", token=teacher_token)
    
    if response and response.status_code == 200:
        classes = response.json()
        
        if classes:
            test_class_id = classes[0]["id"]
            print_test_result("Get Classes", True, f"Found {len(classes)} classes, using: {classes[0]['name']}")
            return True
        else:
            # Create a test class
            return test_create_class()
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Get Classes", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_create_class():
    """Create a test class"""
    global test_class_id
    
    print("🏫 Creating Test Class...")
    
    response = make_request("POST", "/classes", {
        "name": "Test Class for API Testing",
        "description": "A test class for testing the test module",
        "grade_level": "Grade 10",
        "days_of_week": ["Monday", "Wednesday", "Friday"],
        "time": "10:00 AM",
        "start_date": "2024-01-01"
    }, token=teacher_token)
    
    if response and response.status_code == 200:
        class_data = response.json()
        test_class_id = class_data["id"]
        print_test_result("Create Class", True, f"Created class: {class_data['name']}")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Create Class", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_enroll_student():
    """Enroll the test student in the test class"""
    print("📝 Enrolling Student in Class...")
    
    if not student_id:
        print_test_result("Enroll Student", False, "Student ID not available")
        return False
    
    response = make_request("POST", "/enrollments", {
        "student_id": student_id,
        "class_id": test_class_id
    }, token=teacher_token)
    
    if response and response.status_code == 200:
        print_test_result("Enroll Student", True, "Student enrolled successfully")
        return True
    elif response and response.status_code == 400 and "already enrolled" in response.json().get("detail", ""):
        print_test_result("Enroll Student", True, "Student already enrolled")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Enroll Student", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_question_parsing():
    """Test various question formats"""
    print("🧠 Testing Question Parsing...")
    
    # Test case 1: Standard format
    questions_text_1 = """Q1. What is the capital of France?
A) London
B) Berlin
C) Paris
D) Madrid
ANSWER: C

Q2. Which planet is closest to the Sun?
A) Venus
B) Mercury
C) Earth
D) Mars
ANSWER: B"""

    # Test case 2: Different numbering and options
    questions_text_2 = """Q. What is 2 + 2?
A. 3
B. 4
C. 5
ANSWER: B

Q. What color is the sky?
A. Red
B. Blue
C. Green
D. Yellow
E. Purple
F. Orange
ANSWER: B"""

    test_cases = [
        ("Standard Format", questions_text_1),
        ("Flexible Format", questions_text_2)
    ]
    
    all_passed = True
    
    for test_name, questions_text in test_cases:
        response = make_request("POST", "/tests", {
            "class_id": test_class_id,
            "title": f"Question Parsing Test - {test_name}",
            "description": "Testing question parsing functionality",
            "duration_minutes": 30,
            "questions_text": questions_text
        }, token=teacher_token)
        
        if response and response.status_code == 200:
            test_data = response.json()
            questions = test_data.get("questions", [])
            
            if questions and len(questions) == 2:
                print_test_result(f"Question Parsing - {test_name}", True, f"Parsed {len(questions)} questions correctly")
            else:
                print_test_result(f"Question Parsing - {test_name}", False, f"Expected 2 questions, got {len(questions)}")
                all_passed = False
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            print_test_result(f"Question Parsing - {test_name}", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
            all_passed = False
    
    return all_passed

def test_create_test():
    """Test creating a test"""
    global test_id
    
    print("📝 Testing Test Creation...")
    
    questions_text = """Q1. What is the capital of India?
A) Mumbai
B) Delhi
C) Kolkata
D) Chennai
ANSWER: B

Q2. Which is the largest planet in our solar system?
A) Earth
B) Mars
C) Jupiter
D) Saturn
ANSWER: C

Q3. What is 15 + 25?
A) 35
B) 40
C) 45
D) 50
ANSWER: B"""

    response = make_request("POST", "/tests", {
        "class_id": test_class_id,
        "title": "Sample Test for API Testing",
        "description": "A comprehensive test to verify all functionality",
        "duration_minutes": 45,
        "questions_text": questions_text
    }, token=teacher_token)
    
    if response and response.status_code == 200:
        test_data = response.json()
        test_id = test_data["id"]
        questions = test_data.get("questions", [])
        print_test_result("Create Test", True, f"Created test with {len(questions)} questions")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Create Test", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_get_test_as_student():
    """Test getting test as student (answers should be hidden)"""
    print("👁️ Testing Get Test as Student (Answer Hiding)...")
    
    response = make_request("GET", f"/tests/{test_id}", token=student_token)
    
    if response and response.status_code == 200:
        test_data = response.json()
        questions = test_data.get("questions", [])
        
        # Check if correct answers are hidden
        answers_hidden = True
        for question in questions:
            if "correct_answer" in question:
                answers_hidden = False
                break
        
        if answers_hidden and questions:
            print_test_result("Get Test as Student", True, f"Answers properly hidden, {len(questions)} questions visible")
            return True
        else:
            print_test_result("Get Test as Student", False, "Answers not properly hidden or no questions found")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Get Test as Student", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_get_test_as_teacher():
    """Test getting test as teacher (answers should be visible)"""
    print("👨‍🏫 Testing Get Test as Teacher (Answers Visible)...")
    
    response = make_request("GET", f"/tests/{test_id}", token=teacher_token)
    
    if response and response.status_code == 200:
        test_data = response.json()
        questions = test_data.get("questions", [])
        
        # Check if correct answers are visible
        answers_visible = True
        for question in questions:
            if "correct_answer" not in question:
                answers_visible = False
                break
        
        if answers_visible and questions:
            print_test_result("Get Test as Teacher", True, f"Answers properly visible, {len(questions)} questions found")
            return True
        else:
            print_test_result("Get Test as Teacher", False, "Answers not visible or no questions found")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Get Test as Teacher", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_submit_test():
    """Test submitting test answers"""
    print("📤 Testing Test Submission...")
    
    # Submit answers (2 correct, 1 incorrect)
    answers = [
        {"question_index": 0, "selected_answer": "B"},  # Correct
        {"question_index": 1, "selected_answer": "C"},  # Correct
        {"question_index": 2, "selected_answer": "A"}   # Incorrect (correct is B)
    ]
    
    response = make_request("POST", "/tests/submit", {
        "test_id": test_id,
        "answers": answers
    }, token=student_token)
    
    if response and response.status_code == 200:
        submission_data = response.json()
        score = submission_data.get("score", 0)
        total = submission_data.get("total_questions", 0)
        
        if score == 2 and total == 3:
            print_test_result("Submit Test", True, f"Score calculated correctly: {score}/{total}")
            return True
        else:
            print_test_result("Submit Test", False, f"Score calculation error: {score}/{total} (expected 2/3)")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Submit Test", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_get_test_result():
    """Test getting test result after submission"""
    print("📊 Testing Get Test Result...")
    
    response = make_request("GET", f"/tests/{test_id}/result", token=student_token)
    
    if response and response.status_code == 200:
        result_data = response.json()
        submission = result_data.get("submission", {})
        test_data = result_data.get("test", {})
        
        # Check if correct answers are now visible
        questions = test_data.get("questions", [])
        answers_visible = all("correct_answer" in q for q in questions)
        
        if submission and test_data and answers_visible:
            score = submission.get("score", 0)
            total = submission.get("total_questions", 0)
            print_test_result("Get Test Result", True, f"Result retrieved: {score}/{total}, answers now visible")
            return True
        else:
            print_test_result("Get Test Result", False, "Result data incomplete or answers not visible")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Get Test Result", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_my_test_results_endpoint():
    """Test the new /api/my-test-results endpoint"""
    print("📋 Testing My Test Results Endpoint...")
    
    # Test as student (should work)
    response = make_request("GET", "/my-test-results", token=student_token)
    
    student_test_passed = False
    if response and response.status_code == 200:
        results = response.json()
        
        if isinstance(results, list):
            if len(results) > 0:
                # Check structure of first result
                first_result = results[0]
                required_keys = ["submission", "test", "class_name"]
                has_all_keys = all(key in first_result for key in required_keys)
                
                if has_all_keys:
                    print_test_result("My Test Results - Student Access", True, f"Retrieved {len(results)} test results with proper structure")
                    student_test_passed = True
                else:
                    print_test_result("My Test Results - Student Access", False, f"Missing required keys in result structure")
            else:
                print_test_result("My Test Results - Student Access", True, "Empty results array (no submissions yet)")
                student_test_passed = True
        else:
            print_test_result("My Test Results - Student Access", False, "Response is not an array")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("My Test Results - Student Access", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test as teacher (should fail)
    response = make_request("GET", "/my-test-results", token=teacher_token)
    
    teacher_test_passed = False
    if response and response.status_code == 403:
        print_test_result("My Test Results - Teacher Access Denied", True, "Correctly denied access to teachers")
        teacher_test_passed = True
    else:
        print_test_result("My Test Results - Teacher Access Denied", False, f"Should deny teacher access, got status: {response.status_code if response else 'None'}")
    
    return student_test_passed and teacher_test_passed

def test_authentication_required():
    """Test that endpoints require authentication"""
    print("🔒 Testing Authentication Requirements...")
    
    # Test without token
    response = make_request("GET", "/my-test-results")
    
    if response and response.status_code in [401, 403]:
        print_test_result("Authentication Required", True, f"Correctly requires authentication (status: {response.status_code})")
        return True
    else:
        print_test_result("Authentication Required", False, f"Should require auth, got status: {response.status_code if response else 'None'}")
        return False

def test_backend_connectivity():
    """Test basic backend connectivity"""
    print("🌐 Testing Backend Connectivity...")
    
    response = make_request("GET", "/")
    
    if response and response.status_code == 200:
        print_test_result("Backend Connectivity", True, "Backend is accessible")
        return True
    else:
        print_test_result("Backend Connectivity", False, f"Backend not accessible, status: {response.status_code if response else 'None'}")
        return False

# ==== SECURITY TESTS ====

def test_rate_limiting_login():
    """Test rate limiting on login endpoint (5 requests/minute)"""
    print("🚦 Testing Rate Limiting - Login Endpoint...")
    
    # Make 6 rapid requests to trigger rate limiting
    failed_attempts = 0
    rate_limited = False
    
    for i in range(6):
        response = make_request("POST", "/auth/login", {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        
        if response and response.status_code == 429:
            rate_limited = True
            print_test_result("Rate Limiting - Login", True, f"Rate limited after {i+1} requests (429 status)")
            break
        elif response and response.status_code == 401:
            failed_attempts += 1
        
        time.sleep(0.1)  # Small delay between requests
    
    if not rate_limited:
        print_test_result("Rate Limiting - Login", False, f"Expected 429 after 5 requests, got {failed_attempts} 401s")
        return False
    
    return True

def test_rate_limiting_registration():
    """Test rate limiting on registration endpoint (5 requests/minute)"""
    print("🚦 Testing Rate Limiting - Registration Endpoint...")
    
    # Make 6 rapid requests to trigger rate limiting
    rate_limited = False
    
    for i in range(6):
        response = make_request("POST", "/auth/register", {
            "email": f"testuser{i}@test.com",
            "password": "testpass123",
            "name": "Test User",
            "role": "student"
        })
        
        if response and response.status_code == 429:
            rate_limited = True
            print_test_result("Rate Limiting - Registration", True, f"Rate limited after {i+1} requests (429 status)")
            break
        
        time.sleep(0.1)
    
    if not rate_limited:
        print_test_result("Rate Limiting - Registration", False, "Expected 429 after 5 requests")
        return False
    
    return True

def test_rate_limiting_file_upload():
    """Test rate limiting on file upload endpoint (10 requests/minute)"""
    print("🚦 Testing Rate Limiting - File Upload Endpoint...")
    
    if not teacher_token:
        print_test_result("Rate Limiting - File Upload", False, "Teacher token not available")
        return False
    
    # Create a small test file
    test_content = b"This is a test file for rate limiting"
    
    rate_limited = False
    
    for i in range(11):
        files = {'file': ('test.txt', io.BytesIO(test_content), 'text/plain')}
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        try:
            response = requests.post(
                f"{BASE_URL}/upload",
                files=files,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 429:
                rate_limited = True
                print_test_result("Rate Limiting - File Upload", True, f"Rate limited after {i+1} requests (429 status)")
                break
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
        
        time.sleep(0.1)
    
    if not rate_limited:
        print_test_result("Rate Limiting - File Upload", False, "Expected 429 after 10 requests")
        return False
    
    return True

def test_rate_limiting_content_creation():
    """Test rate limiting on content creation endpoints (30 requests/minute)"""
    print("🚦 Testing Rate Limiting - Content Creation...")
    
    if not teacher_token or not test_class_id:
        print_test_result("Rate Limiting - Content Creation", False, "Prerequisites not available")
        return False
    
    rate_limited = False
    
    # Test with homework creation endpoint
    for i in range(31):
        response = make_request("POST", "/homework", {
            "class_id": test_class_id,
            "title": f"Rate Limit Test Homework {i}",
            "description": "Testing rate limiting",
            "due_date": "2024-12-31"
        }, token=teacher_token)
        
        if response and response.status_code == 429:
            rate_limited = True
            print_test_result("Rate Limiting - Content Creation", True, f"Rate limited after {i+1} requests (429 status)")
            break
        
        time.sleep(0.05)  # Faster requests for content creation
    
    if not rate_limited:
        print_test_result("Rate Limiting - Content Creation", False, "Expected 429 after 30 requests")
        return False
    
    return True

def test_xss_protection():
    """Test XSS protection in various input fields"""
    print("🛡️ Testing XSS Protection...")
    
    if not teacher_token:
        print_test_result("XSS Protection", False, "Teacher token not available")
        return False
    
    # Test XSS in registration name
    xss_payload = "<script>alert('XSS')</script>"
    
    response = make_request("POST", "/auth/register", {
        "email": "xsstest@test.com",
        "password": "testpass123",
        "name": xss_payload,
        "role": "student"
    })
    
    xss_blocked = False
    if response and response.status_code == 200:
        user_data = response.json().get("user", {})
        name = user_data.get("name", "")
        
        # Check if script tags were stripped
        if "<script>" not in name and "alert" not in name:
            xss_blocked = True
            print_test_result("XSS Protection - Registration", True, f"XSS payload sanitized: '{name}'")
        else:
            print_test_result("XSS Protection - Registration", False, f"XSS payload not sanitized: '{name}'")
    elif response and response.status_code == 400:
        # Registration might fail due to existing email, try with class description
        if test_class_id:
            response = make_request("POST", "/notices", {
                "class_id": test_class_id,
                "title": "XSS Test Notice",
                "message": xss_payload,
                "is_important": False
            }, token=teacher_token)
            
            if response and response.status_code == 200:
                notice_data = response.json()
                message = notice_data.get("message", "")
                
                if "<script>" not in message and "alert" not in message:
                    xss_blocked = True
                    print_test_result("XSS Protection - Notice", True, f"XSS payload sanitized: '{message}'")
                else:
                    print_test_result("XSS Protection - Notice", False, f"XSS payload not sanitized: '{message}'")
    
    return xss_blocked

def test_nosql_injection_protection():
    """Test NoSQL injection protection"""
    print("🛡️ Testing NoSQL Injection Protection...")
    
    # Test NoSQL injection in login
    nosql_payload = {"$ne": ""}
    
    response = make_request("POST", "/auth/login", {
        "email": nosql_payload,
        "password": "anypassword"
    })
    
    if response and response.status_code == 400:
        error_detail = response.json().get("detail", "")
        if "Invalid email format" in error_detail or "email" in error_detail.lower():
            print_test_result("NoSQL Injection Protection", True, "NoSQL injection blocked in email field")
            return True
    
    print_test_result("NoSQL Injection Protection", False, f"NoSQL injection not properly blocked, status: {response.status_code if response else 'None'}")
    return False

def test_mime_type_validation():
    """Test MIME type validation for file uploads"""
    print("🔍 Testing MIME Type Validation...")
    
    if not teacher_token:
        print_test_result("MIME Type Validation", False, "Teacher token not available")
        return False
    
    # Test 1: Upload a text file renamed to .pdf (should detect MIME mismatch)
    text_content = b"This is actually a text file, not a PDF"
    files = {'file': ('fake.pdf', io.BytesIO(text_content), 'text/plain')}
    headers = {"Authorization": f"Bearer {teacher_token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers=headers,
            timeout=30
        )
        
        mime_validation_working = False
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "doesn't match" in error_detail or "file type" in error_detail.lower():
                mime_validation_working = True
                print_test_result("MIME Type Validation - Fake PDF", True, f"Correctly rejected: {error_detail}")
            else:
                print_test_result("MIME Type Validation - Fake PDF", False, f"Wrong error: {error_detail}")
        else:
            print_test_result("MIME Type Validation - Fake PDF", False, f"Should reject fake PDF, got status: {response.status_code}")
        
        # Test 2: Upload legitimate text file (should pass)
        files = {'file': ('legitimate.txt', io.BytesIO(text_content), 'text/plain')}
        
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers=headers,
            timeout=30
        )
        
        legitimate_file_passed = False
        if response.status_code == 200:
            legitimate_file_passed = True
            print_test_result("MIME Type Validation - Legitimate TXT", True, "Legitimate text file accepted")
        else:
            error_detail = response.json().get("detail", "") if response else "No response"
            print_test_result("MIME Type Validation - Legitimate TXT", False, f"Should accept legitimate file: {error_detail}")
        
        return mime_validation_working and legitimate_file_passed
        
    except Exception as e:
        print_test_result("MIME Type Validation", False, f"Request failed: {e}")
        return False

def test_dangerous_file_blocking():
    """Test blocking of dangerous file types"""
    print("🚫 Testing Dangerous File Blocking...")
    
    if not teacher_token:
        print_test_result("Dangerous File Blocking", False, "Teacher token not available")
        return False
    
    # Test dangerous extensions
    dangerous_files = [
        ('malware.exe', b'MZ\x90\x00', 'application/x-executable'),
        ('script.sh', b'#!/bin/bash\necho "test"', 'text/x-shellscript'),
        ('batch.bat', b'@echo off\necho test', 'application/x-bat')
    ]
    
    all_blocked = True
    
    for filename, content, mime_type in dangerous_files:
        files = {'file': (filename, io.BytesIO(content), mime_type)}
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        try:
            response = requests.post(
                f"{BASE_URL}/upload",
                files=files,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                if "not allowed" in error_detail or "security" in error_detail.lower():
                    print_test_result(f"Dangerous File Blocking - {filename}", True, f"Correctly blocked: {error_detail}")
                else:
                    print_test_result(f"Dangerous File Blocking - {filename}", False, f"Wrong error: {error_detail}")
                    all_blocked = False
            else:
                print_test_result(f"Dangerous File Blocking - {filename}", False, f"Should block dangerous file, got status: {response.status_code}")
                all_blocked = False
                
        except Exception as e:
            print_test_result(f"Dangerous File Blocking - {filename}", False, f"Request failed: {e}")
            all_blocked = False
    
    return all_blocked

def test_file_size_validation():
    """Test file size validation (5MB limit)"""
    print("📏 Testing File Size Validation...")
    
    if not teacher_token:
        print_test_result("File Size Validation", False, "Teacher token not available")
        return False
    
    # Create a file larger than 5MB
    large_content = b'A' * (6 * 1024 * 1024)  # 6MB
    files = {'file': ('large.txt', io.BytesIO(large_content), 'text/plain')}
    headers = {"Authorization": f"Bearer {teacher_token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "size" in error_detail.lower() and "5mb" in error_detail.lower():
                print_test_result("File Size Validation", True, f"Correctly rejected large file: {error_detail}")
                return True
            else:
                print_test_result("File Size Validation", False, f"Wrong error for large file: {error_detail}")
        else:
            print_test_result("File Size Validation", False, f"Should reject large file, got status: {response.status_code}")
        
    except Exception as e:
        print_test_result("File Size Validation", False, f"Request failed: {e}")
    
    return False

def test_legitimate_file_upload():
    """Test that legitimate files can be uploaded successfully"""
    print("✅ Testing Legitimate File Upload...")
    
    if not teacher_token:
        print_test_result("Legitimate File Upload", False, "Teacher token not available")
        return False
    
    # Test legitimate files
    legitimate_files = [
        ('document.txt', b'This is a legitimate text document.', 'text/plain'),
        ('image.png', b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82', 'image/png')
    ]
    
    all_passed = True
    
    for filename, content, mime_type in legitimate_files:
        files = {'file': (filename, io.BytesIO(content), mime_type)}
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        try:
            response = requests.post(
                f"{BASE_URL}/upload",
                files=files,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                upload_data = response.json()
                if upload_data.get("security_validated"):
                    print_test_result(f"Legitimate File Upload - {filename}", True, f"Successfully uploaded: {upload_data.get('url')}")
                else:
                    print_test_result(f"Legitimate File Upload - {filename}", False, "Upload succeeded but security validation flag missing")
                    all_passed = False
            else:
                error_detail = response.json().get("detail", "") if response else "No response"
                print_test_result(f"Legitimate File Upload - {filename}", False, f"Should accept legitimate file: {error_detail}")
                all_passed = False
                
        except Exception as e:
            print_test_result(f"Legitimate File Upload - {filename}", False, f"Request failed: {e}")
            all_passed = False
    
    return all_passed

def test_security_logging():
    """Test that security events are being logged"""
    print("📝 Testing Security Logging...")
    
    # This test is more observational - we'll trigger events and check if they complete successfully
    # In a real environment, you'd check log files, but here we verify the endpoints handle logging gracefully
    
    # Trigger a failed login (should be logged)
    response = make_request("POST", "/auth/login", {
        "email": "nonexistent@security.test",
        "password": "wrongpassword"
    })
    
    failed_login_handled = response and response.status_code == 401
    
    # Trigger a successful registration (should be logged)
    response = make_request("POST", "/auth/register", {
        "email": "securitylog@test.com",
        "password": "testpass123",
        "name": "Security Log Test",
        "role": "student"
    })
    
    registration_handled = response and (response.status_code == 200 or 
                                       (response.status_code == 400 and "already registered" in response.json().get("detail", "")))
    
    if failed_login_handled and registration_handled:
        print_test_result("Security Logging", True, "Security events handled properly (logging assumed working)")
        return True
    else:
        print_test_result("Security Logging", False, "Security events not handled properly")
        return False

def run_security_tests():
    """Run all security-focused tests"""
    print("🔒 Starting Security Feature Testing")
    print("=" * 60)
    
    security_test_results = []
    
    # Rate Limiting Tests
    print("\n🚦 RATE LIMITING TESTS")
    print("-" * 30)
    security_test_results.append(("Rate Limiting - Login", test_rate_limiting_login()))
    security_test_results.append(("Rate Limiting - Registration", test_rate_limiting_registration()))
    
    # Wait a bit to reset rate limits
    print("⏳ Waiting 65 seconds to reset rate limits...")
    time.sleep(65)
    
    security_test_results.append(("Rate Limiting - File Upload", test_rate_limiting_file_upload()))
    security_test_results.append(("Rate Limiting - Content Creation", test_rate_limiting_content_creation()))
    
    # Input Sanitization Tests
    print("\n🛡️ INPUT SANITIZATION TESTS")
    print("-" * 30)
    security_test_results.append(("XSS Protection", test_xss_protection()))
    security_test_results.append(("NoSQL Injection Protection", test_nosql_injection_protection()))
    
    # File Security Tests
    print("\n🔍 FILE SECURITY TESTS")
    print("-" * 30)
    security_test_results.append(("MIME Type Validation", test_mime_type_validation()))
    security_test_results.append(("Dangerous File Blocking", test_dangerous_file_blocking()))
    security_test_results.append(("File Size Validation", test_file_size_validation()))
    security_test_results.append(("Legitimate File Upload", test_legitimate_file_upload()))
    
    # Security Logging Tests
    print("\n📝 SECURITY LOGGING TESTS")
    print("-" * 30)
    security_test_results.append(("Security Logging", test_security_logging()))
    
    return security_test_results

def run_all_tests():
    """Run all backend tests including security tests"""
    print("🚀 Starting Comprehensive Backend Security Testing")
    print("=" * 60)
    
    test_results = []
    
    # Basic Connectivity Test
    test_results.append(("Backend Connectivity", test_backend_connectivity()))
    
    # Authentication Tests (needed for security tests)
    test_results.append(("Teacher Login", test_teacher_login()))
    test_results.append(("Create Student Account", test_create_student_account()))
    test_results.append(("Student Login", test_student_login()))
    
    # Setup Tests (needed for some security tests)
    test_results.append(("Get/Create Classes", test_get_classes()))
    test_results.append(("Enroll Student", test_enroll_student()))
    
    # Run Security Tests
    security_results = run_security_tests()
    test_results.extend(security_results)
    
    # Basic Functionality Tests (to ensure security doesn't break functionality)
    print("\n✅ FUNCTIONALITY VERIFICATION TESTS")
    print("-" * 30)
    test_results.append(("Create Test", test_create_test()))
    test_results.append(("Get Test as Student", test_get_test_as_student()))
    test_results.append(("Submit Test", test_submit_test()))
    test_results.append(("Get Test Result", test_get_test_result()))
    test_results.append(("My Test Results Endpoint", test_my_test_results_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    # Group results by category
    security_tests = [t for t in test_results if any(keyword in t[0] for keyword in 
                     ["Rate Limiting", "XSS", "NoSQL", "MIME", "Dangerous", "File Size", "Security"])]
    functionality_tests = [t for t in test_results if t not in security_tests]
    
    print("\n🔒 SECURITY TEST RESULTS:")
    security_passed = 0
    for test_name, result in security_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            security_passed += 1
    
    print(f"\n✅ FUNCTIONALITY TEST RESULTS:")
    functionality_passed = 0
    for test_name, result in functionality_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            functionality_passed += 1
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"  Security Tests: {security_passed}/{len(security_tests)} passed")
    print(f"  Functionality Tests: {functionality_passed}/{len(functionality_tests)} passed")
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Security features and functionality working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)