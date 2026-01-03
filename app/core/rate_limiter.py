import time
from fastapi import HTTPException, Request
from pathlib import Path
from app.redis_client import redis_client

class RedisRateLimiter:
    LUA_SCRIPT = Path("app/lua/token_bucket.lua").read_text()

    @staticmethod
    async def check(
            request: Request,
            key_prefix: str,
            capacity: int,
            refill_rate: int
    ):
        ip = request.client.host
        redis_key = f"rate:{key_prefix}:{ip}"
        now = int(time.time())

        allowed = redis_client.eval(
            RedisRateLimiter.LUA_SCRIPT,
            1,
            redis_key,
            capacity,
            refill_rate,
            now
        )

        if allowed == 0:
            raise HTTPException(
                status_code=429,
                detail="Too many requests."
            )


