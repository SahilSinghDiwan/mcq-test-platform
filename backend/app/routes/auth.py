from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..redis_client import get_redis, RedisClient
from ..schemas import OTPRequest, OTPVerification, TokenResponse
from ..models import User, UserStatus
from ..auth import generate_otp, create_access_token
from ..email_service import email_service
from ..config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()
logger = logging.getLogger(__name__)


@router.post("/request-otp", status_code=status.HTTP_200_OK)
async def request_otp(
    request: OTPRequest,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    can_proceed = await redis.check_rate_limit(f"otp_request:{request.email}", limit=3, window_seconds=3600)
    
    if not can_proceed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Try again in 1 hour."
        )
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not whitelisted."
        )
    
    if user.status == UserStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test already completed."
        )
    
    if user.status == UserStatus.BLOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account blocked."
        )
    
    otp = generate_otp()
    await redis.store_otp(request.email, otp)
    
    email_sent = await email_service.send_otp_email(request.email, otp)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email."
        )
    
    return {
        "message": f"OTP sent to {request.email}",
        "expires_in_minutes": settings.OTP_EXPIRY_MINUTES
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    request: OTPVerification,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    is_valid = await redis.verify_otp(request.email, request.otp)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        status=user.status
    )


@router.get("/status")
async def check_auth_status():
    return {"service": "authentication", "status": "operational"}