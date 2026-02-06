import redis.asyncio as redis
from typing import Optional
import json
import time
from .config import get_settings

settings = get_settings()


class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
    
    async def store_otp(self, email: str, otp: str, expiry_minutes: int = None) -> bool:
        if expiry_minutes is None:
            expiry_minutes = settings.OTP_EXPIRY_MINUTES
        
        key = f"otp:{email}"
        await self.redis.setex(key, expiry_minutes * 60, otp)
        return True
    
    async def verify_otp(self, email: str, otp: str) -> bool:
        key = f"otp:{email}"
        stored_otp = await self.redis.get(key)
        
        if stored_otp and stored_otp == otp:
            await self.redis.delete(key)
            return True
        return False
    
    async def start_question_timer(self, user_id: int, question_number: int, time_limit: int) -> bool:
        key = f"timer:{user_id}:{question_number}"
        timer_data = {
            "started_at": str(int(time.time())),
            "time_limit": time_limit
        }
        
        await self.redis.setex(key, time_limit + 10, json.dumps(timer_data))
        return True
    
    async def check_question_timer(self, user_id: int, question_number: int) -> dict:
        key = f"timer:{user_id}:{question_number}"
        timer_data = await self.redis.get(key)
        
        if not timer_data:
            return {"valid": False, "time_remaining": 0, "expired": True}
        
        data = json.loads(timer_data)
        started_at = int(data["started_at"])
        time_limit = int(data["time_limit"])
        
        current_time = int(time.time())
        elapsed = current_time - started_at
        time_remaining = max(0, time_limit - elapsed)
        
        return {
            "valid": time_remaining > 0,
            "time_remaining": time_remaining,
            "expired": time_remaining <= 0
        }
    
    async def clear_question_timer(self, user_id: int, question_number: int) -> bool:
        key = f"timer:{user_id}:{question_number}"
        await self.redis.delete(key)
        return True
    
    async def check_rate_limit(self, identifier: str, limit: int, window_seconds: int) -> bool:
        key = f"ratelimit:{identifier}"
        current = await self.redis.get(key)
        
        if current is None:
            await self.redis.setex(key, window_seconds, "1")
            return True
        
        if int(current) >= limit:
            return False
        
        await self.redis.incr(key)
        return True
    
    async def store_test_state(self, user_id: int, state: dict, expiry_hours: int = 4) -> bool:
        key = f"test_state:{user_id}"
        await self.redis.setex(key, expiry_hours * 3600, json.dumps(state))
        return True
    
    async def get_test_state(self, user_id: int) -> Optional[dict]:
        key = f"test_state:{user_id}"
        state = await self.redis.get(key)
        return json.loads(state) if state else None
    
    async def clear_test_state(self, user_id: int) -> bool:
        key = f"test_state:{user_id}"
        await self.redis.delete(key)
        return True


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    return redis_client