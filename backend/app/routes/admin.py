from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os

from ..database import get_db
from ..schemas import (
    WhitelistRequest, WhitelistResponse, BulkResultsResponse,
    TestResultSummary, QuestionCreate, QuestionInDB
)
from ..models import User, UserStatus, QuestionBank, TestSession
from ..config import get_settings

router = APIRouter(prefix="/admin", tags=["Admin"])
settings = get_settings()


@router.post("/whitelist", response_model=WhitelistResponse)
async def add_to_whitelist(
    request: WhitelistRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == request.email).first()
    
    if existing_user:
        return WhitelistResponse(
            email=existing_user.email,
            status=existing_user.status,
            message="User already exists"
        )
    
    new_user = User(
        email=request.email,
        status=UserStatus.PENDING
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return WhitelistResponse(
        email=new_user.email,
        status=new_user.status,
        message="User added successfully"
    )


@router.delete("/whitelist/{email}")
async def remove_from_whitelist(
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": f"User {email} removed"}


@router.get("/whitelist")
async def list_whitelist(
    db: Session = Depends(get_db),
    status_filter: UserStatus = None,
    limit: int = 100,
    offset: int = 0
):
    query = db.query(User)
    
    if status_filter:
        query = query.filter(User.status == status_filter)
    
    total = query.count()
    users = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "status": u.status,
                "created_at": u.created_at,
                "test_started_at": u.test_started_at,
                "test_completed_at": u.test_completed_at
            }
            for u in users
        ]
    }


@router.get("/results", response_model=BulkResultsResponse)
async def get_all_results(
    db: Session = Depends(get_db),
    completed_only: bool = True
):
    total_candidates = db.query(User).count()
    completed = db.query(User).filter(User.status == UserStatus.COMPLETED).count()
    in_progress = db.query(User).filter(User.status == UserStatus.IN_PROGRESS).count()
    pending = db.query(User).filter(User.status == UserStatus.PENDING).count()
    
    if completed_only:
        users = db.query(User).filter(User.status == UserStatus.COMPLETED).all()
    else:
        users = db.query(User).all()
    
    results = []
    for user in users:
        sessions = db.query(TestSession).filter(TestSession.user_id == user.id).all()
        
        if not sessions:
            continue
        
        correct_count = sum(1 for s in sessions if s.is_correct)
        incorrect_count = sum(1 for s in sessions if s.is_correct == False and s.selected_option is not None)
        unanswered_count = sum(1 for s in sessions if s.selected_option is None)
        total_time = sum(s.time_taken_seconds or 0 for s in sessions)
        
        accuracy = (correct_count / len(sessions) * 100) if sessions else 0
        
        results.append(TestResultSummary(
            user_email=user.email,
            total_questions=len(sessions),
            correct_answers=correct_count,
            incorrect_answers=incorrect_count,
            unanswered=unanswered_count,
            accuracy_percentage=round(accuracy, 2),
            total_time_seconds=total_time,
            blur_count=user.blur_count,
            warnings_issued=user.warnings_issued,
            completed_at=user.test_completed_at or user.created_at
        ))
    
    return BulkResultsResponse(
        total_candidates=total_candidates,
        completed=completed,
        in_progress=in_progress,
        pending=pending,
        results=results
    )


@router.get("/results/{email}", response_model=TestResultSummary)
async def get_user_result(
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    sessions = db.query(TestSession).filter(TestSession.user_id == user.id).all()
    
    if not sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No test data found"
        )
    
    correct_count = sum(1 for s in sessions if s.is_correct)
    incorrect_count = sum(1 for s in sessions if s.is_correct == False and s.selected_option is not None)
    unanswered_count = sum(1 for s in sessions if s.selected_option is None)
    total_time = sum(s.time_taken_seconds or 0 for s in sessions)
    
    accuracy = (correct_count / len(sessions) * 100) if sessions else 0
    
    return TestResultSummary(
        user_email=user.email,
        total_questions=len(sessions),
        correct_answers=correct_count,
        incorrect_answers=incorrect_count,
        unanswered=unanswered_count,
        accuracy_percentage=round(accuracy, 2),
        total_time_seconds=total_time,
        blur_count=user.blur_count,
        warnings_issued=user.warnings_issued,
        completed_at=user.test_completed_at or user.created_at
    )


@router.post("/questions", response_model=QuestionInDB)
async def add_question(
    question: QuestionCreate,
    db: Session = Depends(get_db)
):
    image_path = os.path.join(settings.QUESTION_IMAGE_DIR, question.image_path)
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image not found: {question.image_path}"
        )
    
    new_question = QuestionBank(
        image_path=question.image_path,
        correct_option=question.correct_option,
        difficulty=question.difficulty,
        topic=question.topic,
        explanation=question.explanation
    )
    
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    
    return new_question


@router.get("/questions", response_model=List[QuestionInDB])
async def list_questions(
    db: Session = Depends(get_db),
    active_only: bool = True,
    limit: int = 100
):
    query = db.query(QuestionBank)
    
    if active_only:
        query = query.filter(QuestionBank.is_active == True)
    
    questions = query.limit(limit).all()
    
    return questions


@router.put("/questions/{question_id}/deactivate")
async def deactivate_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    question = db.query(QuestionBank).filter(QuestionBank.id == question_id).first()
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    question.is_active = False
    db.commit()
    
    return {"message": f"Question {question_id} deactivated"}


@router.post("/reset-user/{email}")
async def reset_user_status(
    email: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.query(TestSession).filter(TestSession.user_id == user.id).delete()
    
    user.status = UserStatus.PENDING
    user.test_started_at = None
    user.test_completed_at = None
    user.blur_count = 0
    user.warnings_issued = 0
    
    db.commit()
    
    return {"message": f"User {email} reset"}


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_questions = db.query(QuestionBank).filter(QuestionBank.is_active == True).count()
    total_sessions = db.query(TestSession).count()
    
    avg_score = db.query(func.avg(TestSession.is_correct)).filter(
        TestSession.is_correct.isnot(None)
    ).scalar()
    
    avg_time = db.query(func.avg(TestSession.time_taken_seconds)).filter(
        TestSession.time_taken_seconds.isnot(None)
    ).scalar()
    
    return {
        "total_users": total_users,
        "total_active_questions": total_questions,
        "total_test_sessions": total_sessions,
        "average_accuracy": round(float(avg_score or 0) * 100, 2),
        "average_time_per_question": round(float(avg_time or 0), 2),
        "status_breakdown": {
            "pending": db.query(User).filter(User.status == UserStatus.PENDING).count(),
            "in_progress": db.query(User).filter(User.status == UserStatus.IN_PROGRESS).count(),
            "completed": db.query(User).filter(User.status == UserStatus.COMPLETED).count(),
            "blocked": db.query(User).filter(User.status == UserStatus.BLOCKED).count()
        }
    }