from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class QuestionDifficulty(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerification(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    status: UserStatus


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    status: UserStatus
    created_at: datetime
    test_started_at: Optional[datetime] = None
    test_completed_at: Optional[datetime] = None
    blur_count: int
    warnings_issued: int


class QuestionBase(BaseModel):
    image_path: str
    correct_option: str = Field(..., pattern="^[A-D]$")
    difficulty: QuestionDifficulty
    topic: Optional[str] = None
    explanation: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    question_number: int
    total_questions: int
    image_url: str
    options: List[str]
    time_limit_seconds: int


class QuestionInDB(QuestionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime


class TestStartResponse(BaseModel):
    message: str
    total_questions: int
    time_limit_per_question: int
    started_at: datetime


class AnswerSubmission(BaseModel):
    question_number: int
    selected_option: str = Field(..., pattern="^[A-D]$")
    time_taken_seconds: int


class AnswerSubmissionResponse(BaseModel):
    question_number: int
    submitted: bool
    next_question_number: Optional[int] = None
    message: str


class TestStatusResponse(BaseModel):
    status: UserStatus
    current_question_number: Optional[int] = None
    total_questions: int
    questions_answered: int
    blur_count: int
    warnings_issued: int
    time_elapsed_seconds: Optional[int] = None


class TestCompletionRequest(BaseModel):
    reason: str = "user_completed"


class TestResultSummary(BaseModel):
    user_email: str
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    accuracy_percentage: float
    total_time_seconds: int
    blur_count: int
    warnings_issued: int
    completed_at: datetime


class WhitelistRequest(BaseModel):
    email: EmailStr


class WhitelistResponse(BaseModel):
    email: str
    status: UserStatus
    message: str


class BulkResultsResponse(BaseModel):
    total_candidates: int
    completed: int
    in_progress: int
    pending: int
    results: List[TestResultSummary]


class ProctorEvent(BaseModel):
    event_type: str
    details: Optional[str] = None
    timestamp: datetime


class ProctorEventResponse(BaseModel):
    logged: bool
    warning_count: int
    should_auto_submit: bool
    message: str