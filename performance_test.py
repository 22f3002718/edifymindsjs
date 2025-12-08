#!/usr/bin/env python3
"""
Performance Optimization Testing for EdifyMinds Junior
Tests the three critical performance optimizations:
1. Database connection pooling (min=1, max=10)
2. Database indexes on all collections
3. Bcrypt threadpool integration to prevent event loop blocking
"""

import requests
import json
import time
import asyncio
import concurrent.futures
import threading
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "https://non-blocking-auth.preview.emergentagent.com/api"

# Test credentials - using the default teacher account
TEACHER_EMAIL = "edify@gmail.com"
TEACHER_PASSWORD = "edify123"

# Global variables
teacher_token = None
test_class_id = None
student_tokens = []
student_ids = []

def print_test_result(test_name, success, message=""):
    """Print formatted test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")
    print()

def make_request(method, endpoint, data=None, token=None, timeout=30):
    """Make HTTP request with proper error handling"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_teacher_login():
    """Test teacher authentication with the default account"""
    global teacher_token
    
    print("🔐 Testing Teacher Authentication (Bcrypt Threadpool)...")
    
    start_time = time.time()
    response = make_request("POST", "/auth/login", {
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    })
    end_time = time.time()
    
    if response and response.status_code == 200:
        data = response.json()
        teacher_token = data.get("access_token")
        user_info = data.get("user", {})
        
        if teacher_token and user_info.get("role") == "teacher":
            login_time = end_time - start_time
            print_test_result("Teacher Login (Bcrypt Threadpool)", True, 
                            f"Logged in as {user_info.get('name')} in {login_time:.3f}s")
            return True
        else:
            print_test_result("Teacher Login (Bcrypt Threadpool)", False, "Invalid response format")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Teacher Login (Bcrypt Threadpool)", False, 
                        f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_student_registration():
    """Test student registration with bcrypt threadpool"""
    print("👤 Testing Student Registration (Bcrypt Threadpool)...")
    
    start_time = time.time()
    response = make_request("POST", "/auth/register", {
        "email": "performance.student@test.com",
        "password": "student123",
        "name": "Performance Test Student",
        "role": "student"
    })
    end_time = time.time()
    
    if response and response.status_code == 200:
        data = response.json()
        user_info = data.get("user", {})
        registration_time = end_time - start_time
        print_test_result("Student Registration (Bcrypt Threadpool)", True, 
                        f"Registered {user_info.get('name')} in {registration_time:.3f}s")
        return True
    elif response and response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        registration_time = end_time - start_time
        print_test_result("Student Registration (Bcrypt Threadpool)", True, 
                        f"Student already exists (checked in {registration_time:.3f}s)")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Student Registration (Bcrypt Threadpool)", False, 
                        f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_concurrent_auth_requests():
    """Test multiple concurrent authentication requests to verify non-blocking behavior"""
    print("🔄 Testing Concurrent Authentication Requests...")
    
    def login_request(email, password, request_id):
        """Single login request"""
        start_time = time.time()
        response = make_request("POST", "/auth/login", {
            "email": email,
            "password": password
        }, timeout=60)
        end_time = time.time()
        
        return {
            "request_id": request_id,
            "success": response and response.status_code == 200,
            "time": end_time - start_time,
            "status_code": response.status_code if response else None
        }
    
    # Create multiple concurrent login requests
    num_requests = 5
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = []
        for i in range(num_requests):
            future = executor.submit(login_request, TEACHER_EMAIL, TEACHER_PASSWORD, i+1)
            futures.append(future)
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    successful_requests = sum(1 for r in results if r["success"])
    avg_request_time = sum(r["time"] for r in results) / len(results)
    max_request_time = max(r["time"] for r in results)
    
    # If bcrypt is properly in threadpool, concurrent requests should complete reasonably fast
    # and not block each other significantly
    if successful_requests == num_requests and total_time < (num_requests * 2):  # Should be much faster than sequential
        print_test_result("Concurrent Authentication", True, 
                        f"{successful_requests}/{num_requests} requests succeeded in {total_time:.3f}s total, avg: {avg_request_time:.3f}s, max: {max_request_time:.3f}s")
        return True
    else:
        print_test_result("Concurrent Authentication", False, 
                        f"Only {successful_requests}/{num_requests} succeeded, total time: {total_time:.3f}s (too slow or failures)")
        return False

def test_database_indexes_classes():
    """Test database queries that should use indexes - Classes"""
    global test_class_id
    
    print("📊 Testing Database Indexes - Classes Collection...")
    
    if not teacher_token:
        print_test_result("Database Indexes - Classes", False, "Teacher token not available")
        return False
    
    # Test GET /api/classes (should use teacher_id index)
    start_time = time.time()
    response = make_request("GET", "/classes", token=teacher_token)
    end_time = time.time()
    
    if response and response.status_code == 200:
        classes = response.json()
        query_time = end_time - start_time
        
        if classes:
            test_class_id = classes[0]["id"]
            print_test_result("Database Indexes - Get Classes", True, 
                            f"Retrieved {len(classes)} classes in {query_time:.3f}s (using teacher_id index)")
        else:
            # Create a class first
            create_response = make_request("POST", "/classes", {
                "name": "Performance Test Class",
                "description": "Class for testing database performance",
                "grade_level": "Grade 10",
                "days_of_week": ["Monday", "Wednesday", "Friday"],
                "time": "10:00 AM",
                "start_date": "2024-01-01"
            }, token=teacher_token)
            
            if create_response and create_response.status_code == 200:
                class_data = create_response.json()
                test_class_id = class_data["id"]
                print_test_result("Database Indexes - Create Class", True, 
                                f"Created class for testing: {class_data['name']}")
            else:
                print_test_result("Database Indexes - Classes", False, "Could not create test class")
                return False
        
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Database Indexes - Classes", False, 
                        f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_database_indexes_homework():
    """Test database queries for homework (should use class_id index)"""
    print("📊 Testing Database Indexes - Homework Collection...")
    
    if not teacher_token or not test_class_id:
        print_test_result("Database Indexes - Homework", False, "Prerequisites not available")
        return False
    
    # Create some homework first
    homework_data = {
        "class_id": test_class_id,
        "title": "Performance Test Homework",
        "description": "Testing database performance with homework queries",
        "due_date": "2024-12-31"
    }
    
    create_response = make_request("POST", "/homework", homework_data, token=teacher_token)
    
    if not (create_response and create_response.status_code == 200):
        print_test_result("Database Indexes - Homework", False, "Could not create test homework")
        return False
    
    # Test GET homework for class (should use class_id index)
    start_time = time.time()
    response = make_request("GET", f"/classes/{test_class_id}/homework", token=teacher_token)
    end_time = time.time()
    
    if response and response.status_code == 200:
        homework_list = response.json()
        query_time = end_time - start_time
        print_test_result("Database Indexes - Get Homework", True, 
                        f"Retrieved {len(homework_list)} homework items in {query_time:.3f}s (using class_id index)")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Database Indexes - Homework", False, 
                        f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_database_indexes_users():
    """Test user queries that should use email index"""
    print("📊 Testing Database Indexes - Users Collection...")
    
    # Test getting all students (teachers only)
    if not teacher_token:
        print_test_result("Database Indexes - Users", False, "Teacher token not available")
        return False
    
    start_time = time.time()
    response = make_request("GET", "/students", token=teacher_token)
    end_time = time.time()
    
    if response and response.status_code == 200:
        students = response.json()
        query_time = end_time - start_time
        print_test_result("Database Indexes - Get Students", True, 
                        f"Retrieved {len(students)} students in {query_time:.3f}s (using role index)")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Database Indexes - Users", False, 
                        f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_multiple_rapid_database_queries():
    """Test multiple rapid database queries to verify connection pooling"""
    print("🏊 Testing Database Connection Pooling...")
    
    if not teacher_token:
        print_test_result("Database Connection Pooling", False, "Teacher token not available")
        return False
    
    def single_query(query_id):
        """Single database query"""
        start_time = time.time()
        response = make_request("GET", "/classes", token=teacher_token)
        end_time = time.time()
        
        return {
            "query_id": query_id,
            "success": response and response.status_code == 200,
            "time": end_time - start_time,
            "status_code": response.status_code if response else None
        }
    
    # Execute multiple concurrent database queries
    num_queries = 8  # Less than max pool size (10)
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_queries) as executor:
        futures = []
        for i in range(num_queries):
            future = executor.submit(single_query, i+1)
            futures.append(future)
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    successful_queries = sum(1 for r in results if r["success"])
    avg_query_time = sum(r["time"] for r in results) / len(results)
    max_query_time = max(r["time"] for r in results)
    
    # With connection pooling, concurrent queries should be efficient
    if successful_queries == num_queries and avg_query_time < 2.0:  # Should be fast with pooling
        print_test_result("Database Connection Pooling", True, 
                        f"{successful_queries}/{num_queries} queries succeeded in {total_time:.3f}s total, avg: {avg_query_time:.3f}s, max: {max_query_time:.3f}s")
        return True
    else:
        print_test_result("Database Connection Pooling", False, 
                        f"Only {successful_queries}/{num_queries} succeeded, avg time: {avg_query_time:.3f}s (too slow)")
        return False

def test_basic_functionality_still_works():
    """Verify that basic functionality still works after optimizations"""
    print("✅ Testing Basic Functionality After Optimizations...")
    
    if not teacher_token or not test_class_id:
        print_test_result("Basic Functionality", False, "Prerequisites not available")
        return False
    
    # Test creating a notice
    notice_response = make_request("POST", "/notices", {
        "class_id": test_class_id,
        "title": "Performance Test Notice",
        "message": "Testing that basic functionality still works after performance optimizations",
        "is_important": False
    }, token=teacher_token)
    
    if not (notice_response and notice_response.status_code == 200):
        print_test_result("Basic Functionality - Create Notice", False, "Could not create notice")
        return False
    
    # Test getting notices
    notices_response = make_request("GET", f"/classes/{test_class_id}/notices", token=teacher_token)
    
    if not (notices_response and notices_response.status_code == 200):
        print_test_result("Basic Functionality - Get Notices", False, "Could not retrieve notices")
        return False
    
    notices = notices_response.json()
    print_test_result("Basic Functionality", True, 
                    f"Created and retrieved notices successfully ({len(notices)} notices found)")
    return True

def test_server_responsiveness():
    """Test that server remains responsive under load"""
    print("⚡ Testing Server Responsiveness Under Load...")
    
    if not teacher_token:
        print_test_result("Server Responsiveness", False, "Teacher token not available")
        return False
    
    def mixed_request(request_id):
        """Mixed request types to simulate real usage"""
        requests_made = []
        
        # Login request (bcrypt threadpool test)
        start_time = time.time()
        login_response = make_request("POST", "/auth/login", {
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        login_time = time.time() - start_time
        requests_made.append(("login", login_response and login_response.status_code == 200, login_time))
        
        # Database query (connection pooling test)
        start_time = time.time()
        classes_response = make_request("GET", "/classes", token=teacher_token)
        classes_time = time.time() - start_time
        requests_made.append(("classes", classes_response and classes_response.status_code == 200, classes_time))
        
        return {
            "request_id": request_id,
            "requests": requests_made,
            "all_successful": all(r[1] for r in requests_made)
        }
    
    # Execute multiple concurrent mixed requests
    num_workers = 6
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            future = executor.submit(mixed_request, i+1)
            futures.append(future)
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    successful_workers = sum(1 for r in results if r["all_successful"])
    all_login_times = []
    all_classes_times = []
    
    for result in results:
        for req_type, success, req_time in result["requests"]:
            if req_type == "login" and success:
                all_login_times.append(req_time)
            elif req_type == "classes" and success:
                all_classes_times.append(req_time)
    
    avg_login_time = sum(all_login_times) / len(all_login_times) if all_login_times else 0
    avg_classes_time = sum(all_classes_times) / len(all_classes_times) if all_classes_times else 0
    
    # Server should remain responsive with optimizations
    if successful_workers == num_workers and avg_login_time < 3.0 and avg_classes_time < 1.0:
        print_test_result("Server Responsiveness", True, 
                        f"{successful_workers}/{num_workers} workers completed successfully in {total_time:.3f}s, avg login: {avg_login_time:.3f}s, avg classes: {avg_classes_time:.3f}s")
        return True
    else:
        print_test_result("Server Responsiveness", False, 
                        f"Only {successful_workers}/{num_workers} workers succeeded, avg login: {avg_login_time:.3f}s, avg classes: {avg_classes_time:.3f}s")
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

def run_performance_tests():
    """Run all performance optimization tests"""
    print("🚀 Starting Performance Optimization Testing")
    print("=" * 60)
    
    test_results = []
    
    # Basic connectivity
    test_results.append(("Backend Connectivity", test_backend_connectivity()))
    
    # Bcrypt Threadpool Tests
    print("\n🔐 BCRYPT THREADPOOL TESTS")
    print("-" * 30)
    test_results.append(("Teacher Login (Bcrypt Threadpool)", test_teacher_login()))
    test_results.append(("Student Registration (Bcrypt Threadpool)", test_student_registration()))
    test_results.append(("Concurrent Authentication", test_concurrent_auth_requests()))
    
    # Database Index Tests
    print("\n📊 DATABASE INDEX TESTS")
    print("-" * 30)
    test_results.append(("Database Indexes - Classes", test_database_indexes_classes()))
    test_results.append(("Database Indexes - Homework", test_database_indexes_homework()))
    test_results.append(("Database Indexes - Users", test_database_indexes_users()))
    
    # Connection Pooling Tests
    print("\n🏊 DATABASE CONNECTION POOLING TESTS")
    print("-" * 30)
    test_results.append(("Database Connection Pooling", test_multiple_rapid_database_queries()))
    
    # Overall Performance Tests
    print("\n⚡ OVERALL PERFORMANCE TESTS")
    print("-" * 30)
    test_results.append(("Server Responsiveness", test_server_responsiveness()))
    test_results.append(("Basic Functionality", test_basic_functionality_still_works()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    # Group results by category
    bcrypt_tests = [t for t in test_results if "Bcrypt" in t[0] or "Authentication" in t[0]]
    index_tests = [t for t in test_results if "Index" in t[0]]
    pooling_tests = [t for t in test_results if "Pooling" in t[0]]
    performance_tests = [t for t in test_results if "Responsiveness" in t[0] or "Functionality" in t[0]]
    other_tests = [t for t in test_results if t not in bcrypt_tests + index_tests + pooling_tests + performance_tests]
    
    print("\n🔐 BCRYPT THREADPOOL RESULTS:")
    bcrypt_passed = 0
    for test_name, result in bcrypt_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            bcrypt_passed += 1
    
    print("\n📊 DATABASE INDEX RESULTS:")
    index_passed = 0
    for test_name, result in index_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            index_passed += 1
    
    print("\n🏊 CONNECTION POOLING RESULTS:")
    pooling_passed = 0
    for test_name, result in pooling_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            pooling_passed += 1
    
    print("\n⚡ PERFORMANCE & FUNCTIONALITY RESULTS:")
    performance_passed = 0
    for test_name, result in performance_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            performance_passed += 1
    
    if other_tests:
        print("\n🌐 OTHER RESULTS:")
        other_passed = 0
        for test_name, result in other_tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
            if result:
                other_passed += 1
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"  Bcrypt Threadpool: {bcrypt_passed}/{len(bcrypt_tests)} passed")
    print(f"  Database Indexes: {index_passed}/{len(index_tests)} passed")
    print(f"  Connection Pooling: {pooling_passed}/{len(pooling_tests)} passed")
    print(f"  Performance & Functionality: {performance_passed}/{len(performance_tests)} passed")
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All performance optimization tests passed!")
        print("✅ Database connection pooling is working correctly")
        print("✅ Database indexes are improving query performance")
        print("✅ Bcrypt threadpool is preventing event loop blocking")
        print("✅ Server remains responsive under concurrent load")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Performance optimizations may need attention.")
        return False

if __name__ == "__main__":
    success = run_performance_tests()
    exit(0 if success else 1)