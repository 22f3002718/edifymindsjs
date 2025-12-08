#!/usr/bin/env python3
"""
Admin Dashboard Backend Testing for EdifyMinds Junior
Tests all admin-related backend endpoints as specified in the review request:
1. Admin Authentication
2. GET /api/admin/users - List Users
3. PUT /api/admin/users/{user_id} - Update User
4. POST /api/admin/users/{user_id}/reset-password - Reset Password
5. DELETE /api/admin/users/{user_id} - Delete User
6. Access Control Testing
7. Admin User Auto-Creation
"""

import requests
import json
import time
from datetime import datetime

# Configuration - using production URL from frontend/.env
BASE_URL = "https://edify-manager.preview.emergentagent.com/api"

# Admin credentials from review request
ADMIN_EMAIL = "admin@edify.com"
ADMIN_PASSWORD = "admin123"

# Test credentials for non-admin users
TEACHER_EMAIL = "edify@gmail.com"
TEACHER_PASSWORD = "edify123"

# Global variables
admin_token = None
teacher_token = None
student_token = None
test_user_id = None

def print_test_result(test_name, success, message=""):
    """Print formatted test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")
    print()

def make_request(method, endpoint, data=None, token=None, expected_status=None):
    """Make HTTP request with proper error handling"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        
        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def test_admin_authentication():
    """Test admin user login and JWT token validation"""
    global admin_token
    
    print("🔐 Testing Admin Authentication...")
    
    response = make_request("POST", "/auth/login", {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response and response.status_code == 200:
        data = response.json()
        admin_token = data.get("access_token")
        user_info = data.get("user", {})
        
        # Verify JWT token is returned
        if not admin_token:
            print_test_result("Admin Authentication - JWT Token", False, "No access token returned")
            return False
        
        # Verify user object has role='admin'
        if user_info.get("role") != "admin":
            print_test_result("Admin Authentication - Role Check", False, f"Expected role 'admin', got '{user_info.get('role')}'")
            return False
        
        print_test_result("Admin Authentication", True, f"Logged in as {user_info.get('name')} with role '{user_info.get('role')}'")
        return True
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Admin Authentication", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_teacher_login():
    """Login as teacher for access control testing"""
    global teacher_token
    
    print("👨‍🏫 Testing Teacher Login...")
    
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

def test_create_test_student():
    """Create a test student for testing purposes"""
    global student_token, test_user_id
    
    print("👤 Creating Test Student...")
    
    response = make_request("POST", "/auth/register", {
        "email": "teststudent@admin.test",
        "password": "student123",
        "name": "Test Student for Admin",
        "role": "student"
    })
    
    if response and response.status_code == 200:
        data = response.json()
        student_token = data.get("access_token")
        user_info = data.get("user", {})
        test_user_id = user_info.get("id")
        print_test_result("Create Test Student", True, f"Created student: {user_info.get('name')}")
        return True
    elif response and response.status_code == 400 and "already registered" in response.json().get("detail", ""):
        # Student already exists, try to login
        response = make_request("POST", "/auth/login", {
            "email": "teststudent@admin.test",
            "password": "student123"
        })
        if response and response.status_code == 200:
            data = response.json()
            student_token = data.get("access_token")
            user_info = data.get("user", {})
            test_user_id = user_info.get("id")
            print_test_result("Create Test Student", True, "Test student already exists, logged in")
            return True
    
    error_msg = response.json().get("detail", "Unknown error") if response else "No response"
    print_test_result("Create Test Student", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    return False

def test_get_users_no_filters():
    """Test GET /api/admin/users without filters"""
    print("📋 Testing GET /api/admin/users (no filters)...")
    
    response = make_request("GET", "/admin/users", token=admin_token)
    
    if response and response.status_code == 200:
        users = response.json()
        
        if isinstance(users, list) and len(users) > 0:
            # Check that password_hash is excluded
            password_excluded = all("password_hash" not in user for user in users)
            
            if password_excluded:
                print_test_result("GET Users - No Filters", True, f"Retrieved {len(users)} users, password_hash properly excluded")
                return True
            else:
                print_test_result("GET Users - No Filters", False, "password_hash not excluded from response")
                return False
        else:
            print_test_result("GET Users - No Filters", False, "No users returned or invalid format")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("GET Users - No Filters", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def test_get_users_with_role_filter():
    """Test GET /api/admin/users with role filters"""
    print("🔍 Testing GET /api/admin/users with role filters...")
    
    test_cases = [
        ("student", "student"),
        ("teacher", "teacher"),
        ("admin", "admin")
    ]
    
    all_passed = True
    
    for role_filter, expected_role in test_cases:
        response = make_request("GET", f"/admin/users?role={role_filter}", token=admin_token)
        
        if response and response.status_code == 200:
            users = response.json()
            
            if isinstance(users, list):
                # Check that all returned users have the expected role
                correct_roles = all(user.get("role") == expected_role for user in users)
                
                if correct_roles:
                    print_test_result(f"GET Users - Role Filter ({role_filter})", True, f"Retrieved {len(users)} {role_filter}(s)")
                else:
                    print_test_result(f"GET Users - Role Filter ({role_filter})", False, "Some users have incorrect roles")
                    all_passed = False
            else:
                print_test_result(f"GET Users - Role Filter ({role_filter})", False, "Invalid response format")
                all_passed = False
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            print_test_result(f"GET Users - Role Filter ({role_filter})", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
            all_passed = False
    
    return all_passed

def test_get_users_with_search():
    """Test GET /api/admin/users with search parameter"""
    print("🔎 Testing GET /api/admin/users with search...")
    
    test_cases = [
        ("admin", "Should find admin user"),
        ("edify", "Should find edify user")
    ]
    
    all_passed = True
    
    for search_term, description in test_cases:
        response = make_request("GET", f"/admin/users?search={search_term}", token=admin_token)
        
        if response and response.status_code == 200:
            users = response.json()
            
            if isinstance(users, list):
                # Check that search results contain the search term in name or email
                relevant_results = all(
                    search_term.lower() in user.get("name", "").lower() or 
                    search_term.lower() in user.get("email", "").lower()
                    for user in users
                ) if users else True  # Empty results are valid
                
                if relevant_results:
                    print_test_result(f"GET Users - Search ({search_term})", True, f"{description}: {len(users)} results")
                else:
                    print_test_result(f"GET Users - Search ({search_term})", False, "Search results don't match search term")
                    all_passed = False
            else:
                print_test_result(f"GET Users - Search ({search_term})", False, "Invalid response format")
                all_passed = False
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            print_test_result(f"GET Users - Search ({search_term})", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
            all_passed = False
    
    return all_passed

def test_update_user():
    """Test PUT /api/admin/users/{user_id}"""
    print("✏️ Testing PUT /api/admin/users/{user_id}...")
    
    if not test_user_id:
        print_test_result("Update User", False, "Test user ID not available")
        return False
    
    # Test 1: Update user's name
    response = make_request("PUT", f"/admin/users/{test_user_id}", {
        "name": "Updated Test Student Name"
    }, token=admin_token)
    
    name_update_success = False
    if response and response.status_code == 200:
        updated_user = response.json()
        if updated_user.get("name") == "Updated Test Student Name":
            print_test_result("Update User - Name", True, "Name updated successfully")
            name_update_success = True
        else:
            print_test_result("Update User - Name", False, f"Name not updated correctly: {updated_user.get('name')}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Update User - Name", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 2: Update user's email (use unique email)
    unique_email = f"updated.student.{int(time.time())}@admin.test"
    response = make_request("PUT", f"/admin/users/{test_user_id}", {
        "email": unique_email
    }, token=admin_token)
    
    email_update_success = False
    if response and response.status_code == 200:
        updated_user = response.json()
        if updated_user.get("email") == unique_email:
            print_test_result("Update User - Email", True, "Email updated successfully")
            email_update_success = True
        else:
            print_test_result("Update User - Email", False, f"Email not updated correctly: {updated_user.get('email')}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Update User - Email", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 3: Update user's role
    response = make_request("PUT", f"/admin/users/{test_user_id}", {
        "role": "teacher"
    }, token=admin_token)
    
    role_update_success = False
    if response and response.status_code == 200:
        updated_user = response.json()
        if updated_user.get("role") == "teacher":
            print_test_result("Update User - Role", True, "Role updated successfully")
            role_update_success = True
        else:
            print_test_result("Update User - Role", False, f"Role not updated correctly: {updated_user.get('role')}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Update User - Role", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 4: Try updating with duplicate email (should fail)
    response = make_request("PUT", f"/admin/users/{test_user_id}", {
        "email": ADMIN_EMAIL  # Admin's email should already exist
    }, token=admin_token)
    
    duplicate_email_blocked = False
    if response and response.status_code == 400:
        error_detail = response.json().get("detail", "")
        if "already in use" in error_detail or "already exists" in error_detail:
            print_test_result("Update User - Duplicate Email Block", True, "Duplicate email correctly rejected")
            duplicate_email_blocked = True
        else:
            print_test_result("Update User - Duplicate Email Block", False, f"Wrong error for duplicate email: {error_detail}")
    else:
        print_test_result("Update User - Duplicate Email Block", False, f"Should reject duplicate email, got status: {response.status_code if response else 'None'}")
    
    # Test 5: Try updating with invalid role (should fail)
    response = make_request("PUT", f"/admin/users/{test_user_id}", {
        "role": "invalid_role"
    }, token=admin_token)
    
    invalid_role_blocked = False
    if response and response.status_code == 400:
        error_detail = response.json().get("detail", "")
        if "Invalid role" in error_detail:
            print_test_result("Update User - Invalid Role Block", True, "Invalid role correctly rejected")
            invalid_role_blocked = True
        else:
            print_test_result("Update User - Invalid Role Block", False, f"Wrong error for invalid role: {error_detail}")
    else:
        print_test_result("Update User - Invalid Role Block", False, f"Should reject invalid role, got status: {response.status_code if response else 'None'}")
    
    return all([name_update_success, email_update_success, role_update_success, duplicate_email_blocked, invalid_role_blocked])

def test_reset_password():
    """Test POST /api/admin/users/{user_id}/reset-password"""
    print("🔑 Testing POST /api/admin/users/{user_id}/reset-password...")
    
    if not test_user_id:
        print_test_result("Reset Password", False, "Test user ID not available")
        return False
    
    # Test 1: Reset password to valid password
    response = make_request("POST", f"/admin/users/{test_user_id}/reset-password", {
        "new_password": "newpassword123"
    }, token=admin_token)
    
    valid_reset_success = False
    if response and response.status_code == 200:
        result = response.json()
        if "success" in result.get("message", "").lower():
            print_test_result("Reset Password - Valid", True, "Password reset successfully")
            valid_reset_success = True
        else:
            print_test_result("Reset Password - Valid", False, f"Unexpected response: {result}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Reset Password - Valid", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Test 2: Try password less than 6 characters (should fail)
    response = make_request("POST", f"/admin/users/{test_user_id}/reset-password", {
        "new_password": "123"
    }, token=admin_token)
    
    short_password_blocked = False
    if response and response.status_code == 400:
        error_detail = response.json().get("detail", "")
        if "at least 6 characters" in error_detail:
            print_test_result("Reset Password - Short Password Block", True, "Short password correctly rejected")
            short_password_blocked = True
        else:
            print_test_result("Reset Password - Short Password Block", False, f"Wrong error for short password: {error_detail}")
    else:
        print_test_result("Reset Password - Short Password Block", False, f"Should reject short password, got status: {response.status_code if response else 'None'}")
    
    return valid_reset_success and short_password_blocked

def test_delete_user():
    """Test DELETE /api/admin/users/{user_id}"""
    print("🗑️ Testing DELETE /api/admin/users/{user_id}...")
    
    # First create a new test user to delete
    response = make_request("POST", "/auth/register", {
        "email": f"deleteme.{int(time.time())}@admin.test",
        "password": "delete123",
        "name": "User To Delete",
        "role": "student"
    })
    
    if not (response and response.status_code == 200):
        print_test_result("Delete User", False, "Could not create user to delete")
        return False
    
    user_to_delete = response.json().get("user", {})
    delete_user_id = user_to_delete.get("id")
    
    if not delete_user_id:
        print_test_result("Delete User", False, "Could not get ID of user to delete")
        return False
    
    # Delete the user
    response = make_request("DELETE", f"/admin/users/{delete_user_id}", token=admin_token)
    
    delete_success = False
    if response and response.status_code == 200:
        result = response.json()
        if "success" in result.get("message", "").lower():
            print_test_result("Delete User - Success", True, "User deleted successfully")
            delete_success = True
        else:
            print_test_result("Delete User - Success", False, f"Unexpected response: {result}")
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Delete User - Success", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
    
    # Verify user is actually deleted by trying to get them
    response = make_request("GET", f"/admin/users?search={user_to_delete.get('email')}", token=admin_token)
    
    user_not_found = False
    if response and response.status_code == 200:
        users = response.json()
        if isinstance(users, list) and len(users) == 0:
            print_test_result("Delete User - Verification", True, "Deleted user not found in list")
            user_not_found = True
        else:
            print_test_result("Delete User - Verification", False, "Deleted user still appears in list")
    else:
        print_test_result("Delete User - Verification", False, "Could not verify user deletion")
    
    return delete_success and user_not_found

def test_access_control_no_auth():
    """Test admin endpoints without authentication (should return 401)"""
    print("🚫 Testing Access Control - No Authentication...")
    
    endpoints = [
        "/admin/users",
        f"/admin/users/{test_user_id if test_user_id else 'dummy-id'}",
        f"/admin/users/{test_user_id if test_user_id else 'dummy-id'}/reset-password",
    ]
    
    all_blocked = True
    
    for endpoint in endpoints:
        if "reset-password" in endpoint:
            response = make_request("POST", endpoint, {"new_password": "test123"})
        elif "/admin/users/" in endpoint and not endpoint.endswith("/reset-password"):
            response = make_request("PUT", endpoint, {"name": "test"})
        else:
            response = make_request("GET", endpoint)
        
        if response and response.status_code == 401:
            print_test_result(f"No Auth - {endpoint}", True, "Correctly requires authentication")
        else:
            print_test_result(f"No Auth - {endpoint}", False, f"Should require auth, got status: {response.status_code if response else 'None'}")
            all_blocked = False
    
    return all_blocked

def test_access_control_non_admin():
    """Test admin endpoints as non-admin user (should return 403)"""
    print("🚫 Testing Access Control - Non-Admin Access...")
    
    if not teacher_token:
        print_test_result("Non-Admin Access Control", False, "Teacher token not available")
        return False
    
    endpoints_and_methods = [
        ("GET", "/admin/users"),
        ("PUT", f"/admin/users/{test_user_id if test_user_id else 'dummy-id'}", {"name": "test"}),
        ("POST", f"/admin/users/{test_user_id if test_user_id else 'dummy-id'}/reset-password", {"new_password": "test123"}),
        ("DELETE", f"/admin/users/{test_user_id if test_user_id else 'dummy-id'}")
    ]
    
    all_blocked = True
    
    for method, endpoint, *data in endpoints_and_methods:
        request_data = data[0] if data else None
        response = make_request(method, endpoint, request_data, token=teacher_token)
        
        if response and response.status_code == 403:
            print_test_result(f"Non-Admin - {method} {endpoint}", True, "Correctly denied access to non-admin")
        else:
            print_test_result(f"Non-Admin - {method} {endpoint}", False, f"Should deny non-admin access, got status: {response.status_code if response else 'None'}")
            all_blocked = False
    
    return all_blocked

def test_admin_user_auto_creation():
    """Test that admin@edify.com exists and has admin role"""
    print("🔧 Testing Admin User Auto-Creation...")
    
    # Get all admin users
    response = make_request("GET", "/admin/users?role=admin", token=admin_token)
    
    if response and response.status_code == 200:
        admin_users = response.json()
        
        # Check if admin@edify.com exists
        admin_user = next((user for user in admin_users if user.get("email") == ADMIN_EMAIL), None)
        
        if admin_user:
            if admin_user.get("role") == "admin":
                print_test_result("Admin User Auto-Creation", True, f"Admin user exists: {admin_user.get('name')} ({admin_user.get('email')})")
                return True
            else:
                print_test_result("Admin User Auto-Creation", False, f"Admin user exists but has wrong role: {admin_user.get('role')}")
                return False
        else:
            print_test_result("Admin User Auto-Creation", False, "Admin user admin@edify.com not found")
            return False
    else:
        error_msg = response.json().get("detail", "Unknown error") if response else "No response"
        print_test_result("Admin User Auto-Creation", False, f"Status: {response.status_code if response else 'None'}, Error: {error_msg}")
        return False

def run_all_admin_tests():
    """Run all admin dashboard backend tests"""
    print("🚀 Starting Admin Dashboard Backend Testing")
    print("=" * 60)
    
    test_results = []
    
    # 1. Admin Authentication
    print("\n🔐 ADMIN AUTHENTICATION TESTS")
    print("-" * 30)
    test_results.append(("Admin Authentication", test_admin_authentication()))
    
    # Setup non-admin users for access control testing
    print("\n👥 SETUP NON-ADMIN USERS")
    print("-" * 30)
    test_results.append(("Teacher Login", test_teacher_login()))
    test_results.append(("Create Test Student", test_create_test_student()))
    
    # 2. Admin User Auto-Creation
    print("\n🔧 ADMIN USER AUTO-CREATION TEST")
    print("-" * 30)
    test_results.append(("Admin User Auto-Creation", test_admin_user_auto_creation()))
    
    # 3. GET /api/admin/users tests
    print("\n📋 GET /api/admin/users TESTS")
    print("-" * 30)
    test_results.append(("GET Users - No Filters", test_get_users_no_filters()))
    test_results.append(("GET Users - Role Filters", test_get_users_with_role_filter()))
    test_results.append(("GET Users - Search", test_get_users_with_search()))
    
    # 4. PUT /api/admin/users/{user_id} tests
    print("\n✏️ PUT /api/admin/users/{user_id} TESTS")
    print("-" * 30)
    test_results.append(("Update User", test_update_user()))
    
    # 5. POST /api/admin/users/{user_id}/reset-password tests
    print("\n🔑 POST /api/admin/users/{user_id}/reset-password TESTS")
    print("-" * 30)
    test_results.append(("Reset Password", test_reset_password()))
    
    # 6. DELETE /api/admin/users/{user_id} tests
    print("\n🗑️ DELETE /api/admin/users/{user_id} TESTS")
    print("-" * 30)
    test_results.append(("Delete User", test_delete_user()))
    
    # 7. Access Control tests
    print("\n🚫 ACCESS CONTROL TESTS")
    print("-" * 30)
    test_results.append(("Access Control - No Auth", test_access_control_no_auth()))
    test_results.append(("Access Control - Non-Admin", test_access_control_non_admin()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ADMIN DASHBOARD TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    # Group results by category
    auth_tests = [t for t in test_results if "Authentication" in t[0] or "Auto-Creation" in t[0]]
    endpoint_tests = [t for t in test_results if any(keyword in t[0] for keyword in ["GET Users", "Update User", "Reset Password", "Delete User"])]
    access_control_tests = [t for t in test_results if "Access Control" in t[0]]
    setup_tests = [t for t in test_results if any(keyword in t[0] for keyword in ["Teacher Login", "Create Test Student"])]
    
    print("\n🔐 AUTHENTICATION & SETUP RESULTS:")
    for test_name, result in auth_tests + setup_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print("\n📡 ENDPOINT FUNCTIONALITY RESULTS:")
    for test_name, result in endpoint_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print("\n🚫 ACCESS CONTROL RESULTS:")
    for test_name, result in access_control_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n📈 OVERALL RESULTS:")
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All admin dashboard tests passed! Backend functionality working correctly.")
        return True
    else:
        failed_tests = [name for name, result in test_results if not result]
        print(f"\n⚠️  {total - passed} test(s) failed:")
        for test_name in failed_tests:
            print(f"    ❌ {test_name}")
        print("\nPlease review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_admin_tests()
    exit(0 if success else 1)