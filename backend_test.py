#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for EdifyMinds Junior Test Module
Tests all backend endpoints with focus on the new test features
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://file-upload-system-2.preview.emergentagent.com/api"

# Test credentials
TEACHER_EMAIL = "edify@gmail.com"
TEACHER_PASSWORD = "edify123"
STUDENT_EMAIL = "test.student@example.com"
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

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting Comprehensive Backend API Testing")
    print("=" * 60)
    
    test_results = []
    
    # Connectivity Test
    test_results.append(("Backend Connectivity", test_backend_connectivity()))
    
    # Authentication Tests
    test_results.append(("Teacher Login", test_teacher_login()))
    test_results.append(("Create Student Account", test_create_student_account()))
    test_results.append(("Student Login", test_student_login()))
    
    # Setup Tests
    test_results.append(("Get/Create Classes", test_get_classes()))
    test_results.append(("Enroll Student", test_enroll_student()))
    
    # Question Parsing Tests
    test_results.append(("Question Parsing", test_question_parsing()))
    
    # Test Flow Tests
    test_results.append(("Create Test", test_create_test()))
    test_results.append(("Get Test as Student", test_get_test_as_student()))
    test_results.append(("Get Test as Teacher", test_get_test_as_teacher()))
    test_results.append(("Submit Test", test_submit_test()))
    test_results.append(("Get Test Result", test_get_test_result()))
    
    # New Endpoint Tests
    test_results.append(("My Test Results Endpoint", test_my_test_results_endpoint()))
    test_results.append(("Authentication Required", test_authentication_required()))
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend API is working correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)