from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.rate_limiter import RedisRateLimiter
from app.redis_client import redis_client
from app.services.search_service import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.get("/skills/autocomplete")
async def autocomplete_skills(
    request: Request,
    query: str,
    db: Session = Depends(get_db)
):
    # Safety check
    if len(query) < 3:
        return []

    await RedisRateLimiter.check(
        request=request,
        key_prefix="skills_autocomplete",
        capacity=10,      # burst
        refill_rate=5     # tokens/sec
    )

    cache_key = f"skills:autocomplete:{query.lower()}"

    cached = redis_client.get(cache_key)
    if cached:
        return cached.split(",")

    skills = SearchService.search_skills(db, query)
    results = [s.name for s in skills]

    redis_client.setex(cache_key, 300, ",".join(results))

    return results


@router.get("/category/autocomplete/")
async def autocomplete_category(
    request: Request,
    query: str,
    db: Session = Depends(get_db)
):

    if len(query) < 3:
        return []

    await RedisRateLimiter.check(
        request=request,
        key_prefix="category_autocomplete",
        capacity=10,
        refill_rate=5
    )

    cache_key = f"category:autocomplete:{query.lower()}"

    cached = redis_client.get(cache_key)
    if cached:
        return cached.split(",")

    categories = SearchService.search_category(db, query)
    results = [s.category for s in categories]

    redis_client.setex(cache_key, 300, ",".join(results))

    return results

