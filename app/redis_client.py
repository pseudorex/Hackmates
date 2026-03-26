import redis
from app.core.config import settings

REDIS_HOST = getattr(settings, "REDIS_HOST", "localhost")
REDIS_PORT = int(getattr(settings, "REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)
