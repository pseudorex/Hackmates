from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.rate_limiter import RedisRateLimiter
from app.services.skill_detail_service import SkillDetailService

router = APIRouter(
    prefix="/skills",
    tags=["Skills Details"]
)


@router.get("/search-with-details")
async def search_skills_with_details(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db)
):
    await RedisRateLimiter.check(
        request=request,
        key_prefix="skills_search_details",
        capacity=20,
        refill_rate=10
    )

    results = SkillDetailService.search_skills_with_count(db, q, limit)

    return {
        "query": q,
        "results": results,
        "total": len(results)
    }


@router.get("/{skill_name}/details")
async def get_skill_details(
    skill_name: str,
    request: Request,
    db: Session = Depends(get_db)
):
    await RedisRateLimiter.check(
        request=request,
        key_prefix="skill_details",
        capacity=30,
        refill_rate=15
    )

    result = SkillDetailService.get_skill_details(db, skill_name)

    if not result.get("found"):
        raise HTTPException(
            status_code=404,
            detail=f"Skill '{skill_name}' not found"
        )

    return result


@router.get("/{skill_name}/accounts")
async def get_skill_accounts(
    skill_name: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    await RedisRateLimiter.check(
        request=request,
        key_prefix="skill_accounts",
        capacity=30,
        refill_rate=15
    )

    result = SkillDetailService.get_skill_accounts(db, skill_name, skip, limit)

    if not result.get("found"):
        raise HTTPException(
            status_code=404,
            detail=f"No accounts found for skill '{skill_name}'"
        )

    return result


@router.get("/{skill_name}/posts")
async def get_skill_posts(
    skill_name: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    await RedisRateLimiter.check(
        request=request,
        key_prefix="skill_posts",
        capacity=30,
        refill_rate=15
    )

    result = SkillDetailService.get_skill_posts(db, skill_name, skip, limit)

    if not result.get("found"):
        raise HTTPException(
            status_code=404,
            detail=f"No posts found for skill '{skill_name}'"
        )

    return result