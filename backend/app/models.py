from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from .database import Base


class UserStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class QuestionDifficulty(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    test_started_at = Column(DateTime(timezone=True), nullable=True)
    test_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    blur_count = Column(Integer, default=0)
    warnings_issued = Column(Integer, default=0)
    
    test_sessions = relationship("TestSession", back_populates="user", cascade="all, delete-orphan")


class QuestionBank(Base):
    __tablename__ = "question_bank"
    
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(500), nullable=False)
    correct_option = Column(String(1), nullable=False)
    
    difficulty = Column(Enum(QuestionDifficulty), default=QuestionDifficulty.MEDIUM)
    topic = Column(String(100), nullable=True)
    explanation = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    test_sessions = relationship("TestSession", back_populates="question")


class TestSession(Base):
    __tablename__ = "test_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("question_bank.id"), nullable=False)
    
    question_number = Column(Integer, nullable=False)
    option_order = Column(String(50), nullable=False)
    
    selected_option = Column(String(1), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    
    time_taken_seconds = Column(Integer, nullable=True)
    time_limit_seconds = Column(Integer, nullable=False)
    
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    auto_submitted = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="test_sessions")
    question = relationship("QuestionBank", back_populates="test_sessions")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    event_type = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())