from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import random
import json
import os
import logging

from ..database import get_db
from ..redis_client import get_redis, RedisClient
from ..schemas import (
    TestStartResponse, QuestionResponse, AnswerSubmission,
    AnswerSubmissionResponse, TestStatusResponse, TestCompletionRequest,
    TestResultSummary, ProctorEvent, ProctorEventResponse
)
from ..models import User, QuestionBank, TestSession, UserStatus, AuditLog
from ..auth import get_current_user, require_test_in_progress, require_test_not_started, get_user_from_query_token
from ..config import get_settings

router = APIRouter(prefix="/test", tags=["Test Management"])
settings = get_settings()
logger = logging.getLogger(__name__)


@router.post("/start", response_model=TestStartResponse)
async def start_test(
    user: User = Depends(require_test_not_started),
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    if user.status != UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test already started or completed"
        )
    
    all_questions = db.query(QuestionBank).filter(
        QuestionBank.is_active == True
    ).all()
    
    if len(all_questions) < settings.TOTAL_QUESTIONS_PER_TEST:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Not enough questions available"
        )
    
    selected_questions = random.sample(all_questions, settings.TOTAL_QUESTIONS_PER_TEST)
    random.shuffle(selected_questions)
    
    for idx, question in enumerate(selected_questions, start=1):
        options = ['A', 'B', 'C', 'D']
        random.shuffle(options)
        
        test_session = TestSession(
            user_id=user.id,
            question_id=question.id,
            question_number=idx,
            option_order=json.dumps(options),
            time_limit_seconds=settings.QUESTION_TIME_LIMIT_SECONDS
        )
        db.add(test_session)
    
    user.status = UserStatus.IN_PROGRESS
    user.test_started_at = datetime.utcnow()
    db.commit()
    
    await redis.store_test_state(user.id, {
        "started_at": user.test_started_at.isoformat(),
        "total_questions": settings.TOTAL_QUESTIONS_PER_TEST,
        "current_question": 1
    })
    
    return TestStartResponse(
        message="Test started",
        total_questions=settings.TOTAL_QUESTIONS_PER_TEST,
        time_limit_per_question=settings.QUESTION_TIME_LIMIT_SECONDS,
        started_at=user.test_started_at
    )


@router.get("/question/{question_number}", response_model=QuestionResponse)
async def get_question(
    question_number: int,
    user: User = Depends(require_test_in_progress),
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    if question_number < 1 or question_number > settings.TOTAL_QUESTIONS_PER_TEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid question number"
        )
    
    test_session = db.query(TestSession).filter(
        TestSession.user_id == user.id,
        TestSession.question_number == question_number
    ).first()
    
    if not test_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    if test_session.submitted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question already answered"
        )
    
    timer_status = await redis.check_question_timer(user.id, question_number)
    
    if not timer_status["valid"] and timer_status["time_remaining"] == 0:
        await redis.start_question_timer(
            user.id,
            question_number,
            test_session.time_limit_seconds
        )
    elif timer_status["expired"]:
        test_session.submitted_at = datetime.utcnow()
        test_session.auto_submitted = True
        test_session.time_taken_seconds = test_session.time_limit_seconds
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Time limit exceeded"
        )
    
    options = json.loads(test_session.option_order)
    
    return QuestionResponse(
        question_number=question_number,
        total_questions=settings.TOTAL_QUESTIONS_PER_TEST,
        image_url=f"/test/image/{question_number}",
        options=options,
        time_limit_seconds=test_session.time_limit_seconds
    )


@router.get("/image/{question_number}")
async def get_question_image(
    question_number: int,
    user: User = Depends(get_user_from_query_token),
    db: Session = Depends(get_db)
):
    if user.status != UserStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Test not in progress. Status: {user.status}"
        )
    
    test_session = db.query(TestSession).filter(
        TestSession.user_id == user.id,
        TestSession.question_number == question_number
    ).first()
    
    if not test_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    question = test_session.question
    image_path = os.path.join(settings.QUESTION_IMAGE_DIR, question.image_path)
    
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question image not found"
        )
    
    return FileResponse(
        image_path,
        media_type="image/png",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
    )


@router.post("/submit-answer", response_model=AnswerSubmissionResponse)
async def submit_answer(
    submission: AnswerSubmission,
    user: User = Depends(require_test_in_progress),
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    test_session = db.query(TestSession).filter(
        TestSession.user_id == user.id,
        TestSession.question_number == submission.question_number
    ).first()
    
    if not test_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    if test_session.submitted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question already answered"
        )
    
    timer_status = await redis.check_question_timer(user.id, submission.question_number)
    
    if timer_status["expired"]:
        test_session.submitted_at = datetime.utcnow()
        test_session.auto_submitted = True
        test_session.time_taken_seconds = test_session.time_limit_seconds
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Time limit exceeded"
        )
    
    if submission.time_taken_seconds > test_session.time_limit_seconds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time exceeds limit"
        )
    
    shuffled_options = json.loads(test_session.option_order)
    original_option_index = shuffled_options.index(submission.selected_option)
    original_options = ['A', 'B', 'C', 'D']
    mapped_answer = original_options[original_option_index]
    
    is_correct = (mapped_answer == test_session.question.correct_option)
    
    test_session.selected_option = submission.selected_option
    test_session.is_correct = is_correct
    test_session.time_taken_seconds = submission.time_taken_seconds
    test_session.submitted_at = datetime.utcnow()
    test_session.auto_submitted = False
    
    db.commit()
    await redis.clear_question_timer(user.id, submission.question_number)
    
    next_question = submission.question_number + 1
    if next_question > settings.TOTAL_QUESTIONS_PER_TEST:
        next_question = None
        message = "All questions completed"
    else:
        message = "Answer submitted"
    
    return AnswerSubmissionResponse(
        question_number=submission.question_number,
        submitted=True,
        next_question_number=next_question,
        message=message
    )


@router.get("/status", response_model=TestStatusResponse)
async def get_test_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    answered_count = db.query(TestSession).filter(
        TestSession.user_id == user.id,
        TestSession.submitted_at.isnot(None)
    ).count()
    
    current_session = db.query(TestSession).filter(
        TestSession.user_id == user.id,
        TestSession.submitted_at.is_(None)
    ).order_by(TestSession.question_number).first()
    
    current_question_number = current_session.question_number if current_session else None
    
    time_elapsed = None
    if user.test_started_at:
        elapsed = datetime.utcnow() - user.test_started_at
        time_elapsed = int(elapsed.total_seconds())
    
    return TestStatusResponse(
        status=user.status,
        current_question_number=current_question_number,
        total_questions=settings.TOTAL_QUESTIONS_PER_TEST,
        questions_answered=answered_count,
        blur_count=user.blur_count,
        warnings_issued=user.warnings_issued,
        time_elapsed_seconds=time_elapsed
    )


@router.post("/complete", response_model=TestResultSummary)
async def complete_test(
    completion: TestCompletionRequest,
    user: User = Depends(require_test_in_progress),
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    remaining_questions = db.query(TestSession).filter(
        TestSession.user_id == user.id,
        TestSession.submitted_at.is_(None)
    ).all()
    
    for session in remaining_questions:
        session.submitted_at = datetime.utcnow()
        session.auto_submitted = True
        session.time_taken_seconds = 0
    
    user.status = UserStatus.COMPLETED
    user.test_completed_at = datetime.utcnow()
    db.commit()
    
    await redis.clear_test_state(user.id)
    
    all_sessions = db.query(TestSession).filter(
        TestSession.user_id == user.id
    ).all()
    
    correct_count = sum(1 for s in all_sessions if s.is_correct)
    incorrect_count = sum(1 for s in all_sessions if s.is_correct == False and s.selected_option is not None)
    unanswered_count = sum(1 for s in all_sessions if s.selected_option is None)
    total_time = sum(s.time_taken_seconds or 0 for s in all_sessions)
    
    accuracy = (correct_count / len(all_sessions) * 100) if all_sessions else 0
    
    from ..email_service import email_service
    import asyncio
    asyncio.create_task(
        email_service.send_test_completion_email(user.email, correct_count, len(all_sessions))
    )
    
    return TestResultSummary(
        user_email=user.email,
        total_questions=len(all_sessions),
        correct_answers=correct_count,
        incorrect_answers=incorrect_count,
        unanswered=unanswered_count,
        accuracy_percentage=round(accuracy, 2),
        total_time_seconds=total_time,
        blur_count=user.blur_count,
        warnings_issued=user.warnings_issued,
        completed_at=user.test_completed_at
    )


@router.post("/proctor-event", response_model=ProctorEventResponse)
async def log_proctor_event(
    event: ProctorEvent,
    user: User = Depends(require_test_in_progress),
    db: Session = Depends(get_db)
):
    audit = AuditLog(
        user_id=user.id,
        event_type=event.event_type,
        details=event.details
    )
    db.add(audit)
    
    if event.event_type == "blur":
        user.blur_count += 1
        user.warnings_issued += 1
    elif event.event_type in ["copy_attempt", "right_click", "devtools"]:
        user.warnings_issued += 1
    
    db.commit()
    
    should_auto_submit = user.warnings_issued >= settings.MAX_BLUR_WARNINGS
    
    if should_auto_submit and user.status == UserStatus.IN_PROGRESS:
        user.status = UserStatus.COMPLETED
        user.test_completed_at = datetime.utcnow()
        
        remaining = db.query(TestSession).filter(
            TestSession.user_id == user.id,
            TestSession.submitted_at.is_(None)
        ).all()
        
        for session in remaining:
            session.submitted_at = datetime.utcnow()
            session.auto_submitted = True
        
        db.commit()
        
        message = "Test auto-submitted due to warnings"
    else:
        message = f"Warning {user.warnings_issued}/{settings.MAX_BLUR_WARNINGS}"
    
    return ProctorEventResponse(
        logged=True,
        warning_count=user.warnings_issued,
        should_auto_submit=should_auto_submit,
        message=message
    )