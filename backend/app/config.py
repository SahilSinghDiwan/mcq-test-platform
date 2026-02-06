from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    APP_NAME: str = Field(default="MCQ Testing Platform")
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=180)
    
    DATABASE_URL: str
    REDIS_URL: str
    
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_TLS: bool = Field(default=True)
    
    OTP_EXPIRY_MINUTES: int = Field(default=5)
    OTP_LENGTH: int = Field(default=6)
    QUESTION_TIME_LIMIT_SECONDS: int = Field(default=120)
    MAX_BLUR_WARNINGS: int = Field(default=2)
    TOTAL_QUESTIONS_PER_TEST: int = Field(default=20)
    
    QUESTION_IMAGE_DIR: str
    WATERMARK_OPACITY: float = Field(default=0.15)
    
    CORS_ORIGINS: List[str]
    RATE_LIMIT_OTP: str = Field(default="30/hour")


@lru_cache()
def get_settings() -> Settings:
    return Settings()