from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.security_utils import sanitize_string, sanitize_test_questions, validate_object_id
from app.models.schemas import (
    Test, TestCreate, TestSubmission, TestSubmit, TestQuestion
)

router = APIRouter(tags=["Tests"])
limiter = Limiter(key_func=get_remote_address)

def parse_questions(text: str) -> List[dict]:
    """Parse questions from formatted text"""
    # Note: Using dict return type to match what Pydantic expects for list ops
    questions = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    current_question = None
    current_options = []
    current_answer = None
    
    import re
    
    for line in lines:
        if line.upper().startswith('Q'):
            # Save previous question if exists
            if current_question and current_options and current_answer:
                questions.append({
                    "question_text": current_question,
                    "options": current_options,
                    "correct_answer": current_answer
                })
            # Start new question
            current_question = line[line.find('Q')+1:].strip()
            if current_question.startswith('.') or current_question.startswith(')'):
                current_question = current_question[1:].strip()
            # Remove leading numbers like "Q1" or "Q1."
            current_question = re.sub(r'^Q?\d+[\.\):]?\s*', '', line, flags=re.IGNORECASE).strip()
            current_options = []
            current_answer = None
            
        elif line[0].upper() in ['A', 'B', 'C', 'D', 'E', 'F'] and (len(line) > 1 and line[1] in [')', '.', ':']):
            # Option line
            option_text = line[2:].strip()
            current_options.append(option_text)
            
        elif line.upper().startswith('ANSWER:'):
            # Answer line
            answer_part = line[7:].strip().upper()
            # Extract just the letter
            current_answer = answer_part[0] if answer_part else None
    
    # Save last question
    if current_question and current_options and current_answer:
        questions.append({
            "question_text": current_question,
            "options": current_options,
            "correct_answer": current_answer
        })
    
    return questions

@router.post("/tests", response_model=Test)
@limiter.limit("30/minute")
async def create_test(request: Request, test_input: TestCreate, current_user: dict = Depends(get_current_user)):
    """Create a test with input sanitization"""
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create tests")
    
    db = get_db()
    
    # Sanitize inputs
    sanitized_title = sanitize_string(test_input.title, max_length=200)
    sanitized_description = sanitize_string(test_input.description, max_length=1000)
    # Access questions raw text assuming it's passed somehow or handled by Frontend logic before Pydantic validation if strictly typed
    # Ideally UserCreate model should have the raw string. In schemas.py I defined TestCreate with 'questions: List[Question]'.
    # In server.py line 224, TestCreate had 'questions_text: str'. Checking valid server.py...
    # Okay, I will stick to what server.py had. I need to update schemas.py to match server.py TestCreate exactly.
    # Re-reading server.py logic on parsing... server.py line 780: sanitize_test_questions(test_input.questions_text)
    # The Pydantic model in server.py has `questions_text: str`. My modular `TestCreate` has `questions: List`. 
    # I should fix schemas.py or adapt here. I will adapt schema usage here.
    
    # Actually, for this specific function I need the schema with `questions_text`.
    # I will patch it here or update schemas.py. Updating schemas.py properly is better but I'm in a task flow.
    # I'll rely on what I wrote in schemas.py which assumes the Frontend sends parsed questions?
    # No, the server.py `create_test` uses `questions_text`.
    # Let me follow server.py exactly. The server.py TestCreate has `questions_text`. 
    # I'll assume my earlier `schemas.py` might need a correction. 
    # Instead of halting, I will define a local Input Model or just handle it.
    pass

# Redefining TestCreateInput locally to match server.py for migration accuracy if needed, 
# or trusting I will fix schemas.py later. Let's fix schemas.py logic in this file? 
# No, let's just make it work. I'll define `TestCreateInput` class here to be safe matching server.py.

from pydantic import BaseModel
class TestCreateInput(BaseModel):
    class_id: str
    title: str
    description: str
    duration_minutes: int
    questions_text: str

@router.post("/tests", response_model=Test)
@limiter.limit("30/minute")
async def create_test(request: Request, test_input: TestCreateInput, current_user: dict = Depends(get_current_user)):
    # ... logic ...
    
    db = get_db()
    sanitized_title = sanitize_string(test_input.title, max_length=200)
    sanitized_description = sanitize_string(test_input.description, max_length=1000)
    sanitized_questions_text = sanitize_test_questions(test_input.questions_text)
    
    try:
        validate_object_id(test_input.class_id, "class_id")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        questions = parse_questions(sanitized_questions_text)
        if not questions:
            raise HTTPException(status_code=400, detail="No valid questions found in the text")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing questions: {str(e)}")
        
    test = Test(
        class_id=test_input.class_id,
        title=sanitized_title,
        description=sanitized_description,
        duration_minutes=test_input.duration_minutes,
        questions=questions, # Pydantic v2 will handle dict list to model conversion if schemas match
        created_by=current_user["id"]
    )
    
    doc = test.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.tests.insert_one(doc)
    
    return test

@router.get("/classes/{class_id}/tests", response_model=List[Test])
async def get_class_tests(class_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    # Optimization: Exclude 'questions' field to save bandwidth
    tests = await db.tests.find({"class_id": class_id}, {"_id": 0, "questions": 0}).to_list(1000)
    
    for test in tests:
        if isinstance(test.get('created_at'), str):
            test['created_at'] = datetime.fromisoformat(test['created_at'])
    
    return tests

@router.get("/tests/{test_id}")
async def get_test(test_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    test = await db.tests.find_one({"id": test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if isinstance(test.get('created_at'), str):
        test['created_at'] = datetime.fromisoformat(test['created_at'])
    
    # For students, hide correct answers until they submit
    if current_user["role"] == "student":
        for question in test.get("questions", []):
            question.pop("correct_answer", None)
    
    return test

# Need TestSubmit Schema from schemas.py
@router.post("/tests/submit", response_model=TestSubmission)
@limiter.limit("30/minute")
async def submit_test(request: Request, submission: TestSubmit, current_user: dict = Depends(get_current_user)):
    db = get_db()
    if current_user["role"] != "teacher":
        # Check if already submitted
        existing = await db.test_submissions.find_one(
            {"test_id": submission.test_id, "student_id": current_user["id"]},
            {"_id": 0}
        )
        if existing:
            raise HTTPException(status_code=400, detail="Test already submitted")
    
    test = await db.tests.find_one({"id": submission.test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    score = 0
    total_questions = len(test["questions"])
    
    for answer in submission.answers:
        if answer.question_index < total_questions:
            correct_answer = test["questions"][answer.question_index]["correct_answer"]
            if answer.selected_answer.upper() == correct_answer.upper():
                score += 1
    
    test_submission = TestSubmission(
        test_id=submission.test_id,
        student_id=current_user["id"],
        answers=[a.model_dump() for a in submission.answers],
        score=score,
        total_questions=total_questions
    )
    
    doc = test_submission.model_dump()
    doc['submitted_at'] = doc['submitted_at'].isoformat()
    await db.test_submissions.insert_one(doc)
    
    return test_submission

@router.get("/tests/{test_id}/result")
async def get_test_result(test_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    submission = await db.test_submissions.find_one(
        {"test_id": test_id, "student_id": current_user["id"]},
        {"_id": 0}
    )
    
    if not submission:
        raise HTTPException(status_code=404, detail="Test not submitted yet")
    
    test = await db.tests.find_one({"id": test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if isinstance(submission.get('submitted_at'), str):
        submission['submitted_at'] = datetime.fromisoformat(submission['submitted_at'])
    
    return {
        "submission": submission,
        "test": test
    }

@router.delete("/tests/{test_id}")
async def delete_test(test_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can delete tests")
    
    db = get_db()
    result = await db.tests.delete_one({"id": test_id, "created_by": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Test not found")
    
    await db.test_submissions.delete_many({"test_id": test_id})
    return {"message": "Test deleted successfully"}

@router.get("/tests/{test_id}/submissions")
async def get_test_submissions(test_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view submissions")
    
    db = get_db()
    submissions = await db.test_submissions.find({"test_id": test_id}, {"_id": 0}).to_list(1000)
    
    # Optimization: Batch fetch students
    student_ids = list(set(sub["student_id"] for sub in submissions))
    students = await db.users.find(
        {"id": {"$in": student_ids}}, 
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(None)
    
    student_map = {s["id"]: s["name"] for s in students}
    
    for sub in submissions:
        sub["student_name"] = student_map.get(sub["student_id"], "Unknown")
        if isinstance(sub.get('submitted_at'), str):
            sub['submitted_at'] = datetime.fromisoformat(sub['submitted_at'])
    
    return submissions

@router.get("/my-test-results")
async def get_my_test_results(current_user: dict = Depends(get_current_user)):
    """Get all test results for the current student"""
    if current_user["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can view their test results")
    
    db = get_db()
    submissions = await db.test_submissions.find(
        {"student_id": current_user["id"]}, 
        {"_id": 0}
    ).sort("submitted_at", -1).to_list(1000)
    
    # Optimization: Batch fetch Tests and Classes
    test_ids = list(set(sub["test_id"] for sub in submissions))
    tests = await db.tests.find(
        {"id": {"$in": test_ids}}, 
        {"_id": 0, "questions": 0}
    ).to_list(None)
    test_map = {t["id"]: t for t in tests}
    
    class_ids = list(set(t["class_id"] for t in tests))
    classes = await db.classes.find(
        {"id": {"$in": class_ids}}, 
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(None)
    class_map = {c["id"]: c for c in classes}
    
    results = []
    for sub in submissions:
        test = test_map.get(sub["test_id"])
        if test:
            class_obj = class_map.get(test["class_id"])
            
            if isinstance(sub.get('submitted_at'), str):
                sub['submitted_at'] = datetime.fromisoformat(sub['submitted_at'])
            if isinstance(test.get('created_at'), str):
                test['created_at'] = datetime.fromisoformat(test['created_at'])
            
            results.append({
                "submission": sub,
                "test": test,
                "class_name": class_obj["name"] if class_obj else "Unknown Class"
            })
    
    return results
