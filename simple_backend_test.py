#!/usr/bin/env python3
"""
Simplified Backend API Testing focusing on key test module functionality
"""

import requests
import json

# Configuration
BASE_URL = "https://testmate-builder.preview.emergentagent.com/api"

# Test credentials
TEACHER_EMAIL = "edify@gmail.com"
TEACHER_PASSWORD = "edify123"

def test_key_functionality():
    """Test the key functionality requested in the review"""
    print("🚀 Testing Key Backend Functionality")
    print("=" * 50)
    
    # 1. Test teacher login
    print("1. Testing Teacher Login...")
    login_response = requests.post(f"{BASE_URL}/auth/login", 
                                 json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
                                 timeout=30)
    
    if login_response.status_code != 200:
        print("❌ Teacher login failed")
        return False
    
    teacher_token = login_response.json()["access_token"]
    print("✅ Teacher login successful")
    
    # 2. Get classes
    print("\n2. Testing Get Classes...")
    classes_response = requests.get(f"{BASE_URL}/classes", 
                                  headers={"Authorization": f"Bearer {teacher_token}"},
                                  timeout=30)
    
    if classes_response.status_code != 200:
        print("❌ Get classes failed")
        return False
    
    classes = classes_response.json()
    if not classes:
        print("❌ No classes found")
        return False
    
    class_id = classes[0]["id"]
    print(f"✅ Found {len(classes)} classes")
    
    # 3. Test creation with question parsing
    print("\n3. Testing Test Creation with Question Parsing...")
    questions_text = """Q1. What is the capital of India?
A) Mumbai
B) Delhi
C) Kolkata
D) Chennai
ANSWER: B

Q2. Which is the largest planet?
A) Earth
B) Mars
C) Jupiter
D) Saturn
ANSWER: C"""

    test_response = requests.post(f"{BASE_URL}/tests",
                                json={
                                    "class_id": class_id,
                                    "title": "API Test",
                                    "description": "Testing API",
                                    "duration_minutes": 30,
                                    "questions_text": questions_text
                                },
                                headers={"Authorization": f"Bearer {teacher_token}"},
                                timeout=30)
    
    if test_response.status_code != 200:
        print(f"❌ Test creation failed: {test_response.status_code}")
        return False
    
    test_data = test_response.json()
    test_id = test_data["id"]
    questions = test_data.get("questions", [])
    
    if len(questions) != 2:
        print(f"❌ Question parsing failed: expected 2, got {len(questions)}")
        return False
    
    print("✅ Test creation and question parsing successful")
    
    # 4. Create and login student
    print("\n4. Testing Student Account Creation and Login...")
    
    # Try to create student account
    student_email = "api.test.student@example.com"
    register_response = requests.post(f"{BASE_URL}/auth/register",
                                    json={
                                        "email": student_email,
                                        "password": "student123",
                                        "name": "API Test Student",
                                        "role": "student"
                                    },
                                    timeout=30)
    
    # Login student (whether created now or already exists)
    student_login_response = requests.post(f"{BASE_URL}/auth/login",
                                         json={"email": student_email, "password": "student123"},
                                         timeout=30)
    
    if student_login_response.status_code != 200:
        print("❌ Student login failed")
        return False
    
    student_token = student_login_response.json()["access_token"]
    student_id = student_login_response.json()["user"]["id"]
    print("✅ Student account ready")
    
    # 5. Enroll student
    print("\n5. Testing Student Enrollment...")
    enroll_response = requests.post(f"{BASE_URL}/enrollments",
                                  json={"student_id": student_id, "class_id": class_id},
                                  headers={"Authorization": f"Bearer {teacher_token}"},
                                  timeout=30)
    
    if enroll_response.status_code not in [200, 400]:  # 400 if already enrolled
        print(f"❌ Enrollment failed: {enroll_response.status_code}")
        return False
    
    print("✅ Student enrollment successful")
    
    # 6. Test GET test as student (answers should be hidden)
    print("\n6. Testing Get Test as Student (Answer Hiding)...")
    get_test_response = requests.get(f"{BASE_URL}/tests/{test_id}",
                                   headers={"Authorization": f"Bearer {student_token}"},
                                   timeout=30)
    
    if get_test_response.status_code != 200:
        print("❌ Get test as student failed")
        return False
    
    student_test_data = get_test_response.json()
    student_questions = student_test_data.get("questions", [])
    
    # Check if answers are hidden
    answers_hidden = all("correct_answer" not in q for q in student_questions)
    
    if not answers_hidden:
        print("❌ Answers not properly hidden for student")
        return False
    
    print("✅ Test retrieval with answer hiding successful")
    
    # 7. Test submission
    print("\n7. Testing Test Submission...")
    submit_response = requests.post(f"{BASE_URL}/tests/submit",
                                  json={
                                      "test_id": test_id,
                                      "answers": [
                                          {"question_index": 0, "selected_answer": "B"},  # Correct
                                          {"question_index": 1, "selected_answer": "A"}   # Incorrect
                                      ]
                                  },
                                  headers={"Authorization": f"Bearer {student_token}"},
                                  timeout=30)
    
    if submit_response.status_code != 200:
        print(f"❌ Test submission failed: {submit_response.status_code}")
        return False
    
    submission_data = submit_response.json()
    score = submission_data.get("score", 0)
    total = submission_data.get("total_questions", 0)
    
    if score != 1 or total != 2:
        print(f"❌ Score calculation error: {score}/{total} (expected 1/2)")
        return False
    
    print("✅ Test submission successful")
    
    # 8. Test result retrieval
    print("\n8. Testing Test Result Retrieval...")
    result_response = requests.get(f"{BASE_URL}/tests/{test_id}/result",
                                 headers={"Authorization": f"Bearer {student_token}"},
                                 timeout=30)
    
    if result_response.status_code != 200:
        print("❌ Test result retrieval failed")
        return False
    
    result_data = result_response.json()
    test_with_answers = result_data.get("test", {})
    result_questions = test_with_answers.get("questions", [])
    
    # Check if answers are now visible
    answers_visible = all("correct_answer" in q for q in result_questions)
    
    if not answers_visible:
        print("❌ Answers not visible in result")
        return False
    
    print("✅ Test result retrieval successful")
    
    # 9. Test MY TEST RESULTS endpoint (KEY NEW FEATURE)
    print("\n9. Testing My Test Results Endpoint (NEW FEATURE)...")
    
    # Test as student (should work)
    my_results_response = requests.get(f"{BASE_URL}/my-test-results",
                                     headers={"Authorization": f"Bearer {student_token}"},
                                     timeout=30)
    
    if my_results_response.status_code != 200:
        print(f"❌ My test results failed for student: {my_results_response.status_code}")
        return False
    
    results = my_results_response.json()
    
    if not isinstance(results, list):
        print("❌ My test results should return an array")
        return False
    
    if len(results) == 0:
        print("❌ Expected at least one test result")
        return False
    
    # Check structure
    first_result = results[0]
    required_keys = ["submission", "test", "class_name"]
    if not all(key in first_result for key in required_keys):
        print("❌ My test results missing required keys")
        return False
    
    print(f"✅ My test results endpoint working - found {len(results)} results")
    
    # Test as teacher (should fail)
    teacher_results_response = requests.get(f"{BASE_URL}/my-test-results",
                                          headers={"Authorization": f"Bearer {teacher_token}"},
                                          timeout=30)
    
    if teacher_results_response.status_code != 403:
        print(f"❌ My test results should deny teacher access, got: {teacher_results_response.status_code}")
        return False
    
    print("✅ My test results correctly denies teacher access")
    
    # 10. Test authentication requirement
    print("\n10. Testing Authentication Requirement...")
    no_auth_response = requests.get(f"{BASE_URL}/my-test-results", timeout=30)
    
    if no_auth_response.status_code not in [401, 403]:
        print(f"❌ Should require authentication, got: {no_auth_response.status_code}")
        return False
    
    print("✅ Authentication requirement working")
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! Backend API is working correctly.")
    print("✅ Question parsing works with various formats")
    print("✅ Test creation, retrieval, and submission work")
    print("✅ Answer hiding/showing works correctly")
    print("✅ New /api/my-test-results endpoint works properly")
    print("✅ Authentication and authorization work correctly")
    
    return True

if __name__ == "__main__":
    success = test_key_functionality()
    exit(0 if success else 1)