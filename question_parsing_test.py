#!/usr/bin/env python3
"""
Test various question parsing formats
"""

import requests

BASE_URL = "https://fortify-uploads.preview.emergentagent.com/api"
TEACHER_EMAIL = "edify@gmail.com"
TEACHER_PASSWORD = "edify123"

def test_question_formats():
    """Test various question formats"""
    print("🧠 Testing Various Question Parsing Formats")
    print("=" * 50)
    
    # Login as teacher
    login_response = requests.post(f"{BASE_URL}/auth/login", 
                                 json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD})
    teacher_token = login_response.json()["access_token"]
    
    # Get class
    classes_response = requests.get(f"{BASE_URL}/classes", 
                                  headers={"Authorization": f"Bearer {teacher_token}"})
    class_id = classes_response.json()[0]["id"]
    
    test_cases = [
        {
            "name": "2 Options Format",
            "text": """Q1. Is Python a programming language?
A) Yes
B) No
ANSWER: A

Q2. Is the Earth flat?
A) Yes
B) No
ANSWER: B""",
            "expected_questions": 2,
            "expected_options": [2, 2]
        },
        {
            "name": "6 Options Format",
            "text": """Q1. Which of these is a color?
A) Red
B) Blue
C) Green
D) Yellow
E) Purple
F) Orange
ANSWER: A

Q2. Pick any letter:
A) A
B) B
C) C
D) D
E) E
F) F
ANSWER: C""",
            "expected_questions": 2,
            "expected_options": [6, 6]
        },
        {
            "name": "Mixed Options Format",
            "text": """Q1. True or False?
A) True
B) False
ANSWER: A

Q2. Pick a number:
A) One
B) Two
C) Three
D) Four
E) Five
ANSWER: C

Q3. Choose a vowel:
A) A
B) E
C) I
ANSWER: B""",
            "expected_questions": 3,
            "expected_options": [2, 5, 3]
        },
        {
            "name": "Different Q Formats",
            "text": """Q. What is 1+1?
A) 1
B) 2
C) 3
ANSWER: B

Q1) What is 2+2?
A) 3
B) 4
C) 5
ANSWER: B

Q2: What is 3+3?
A) 5
B) 6
C) 7
ANSWER: B""",
            "expected_questions": 3,
            "expected_options": [3, 3, 3]
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}...")
        
        response = requests.post(f"{BASE_URL}/tests",
                               json={
                                   "class_id": class_id,
                                   "title": f"Parse Test {i}",
                                   "description": f"Testing {test_case['name']}",
                                   "duration_minutes": 30,
                                   "questions_text": test_case['text']
                               },
                               headers={"Authorization": f"Bearer {teacher_token}"})
        
        if response.status_code != 200:
            print(f"❌ Failed to create test: {response.status_code}")
            all_passed = False
            continue
        
        test_data = response.json()
        questions = test_data.get("questions", [])
        
        # Check number of questions
        if len(questions) != test_case['expected_questions']:
            print(f"❌ Expected {test_case['expected_questions']} questions, got {len(questions)}")
            all_passed = False
            continue
        
        # Check number of options for each question
        options_match = True
        for j, question in enumerate(questions):
            expected_options = test_case['expected_options'][j]
            actual_options = len(question.get('options', []))
            if actual_options != expected_options:
                print(f"❌ Question {j+1}: Expected {expected_options} options, got {actual_options}")
                options_match = False
        
        if not options_match:
            all_passed = False
            continue
        
        # Check if correct answers are parsed
        answers_parsed = all('correct_answer' in q for q in questions)
        if not answers_parsed:
            print("❌ Correct answers not parsed properly")
            all_passed = False
            continue
        
        print(f"✅ {test_case['name']} parsed correctly")
    
    if all_passed:
        print("\n🎉 All question parsing formats work correctly!")
        return True
    else:
        print("\n❌ Some question parsing formats failed")
        return False

if __name__ == "__main__":
    success = test_question_formats()
    exit(0 if success else 1)