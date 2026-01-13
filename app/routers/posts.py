from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.post_response import UpdateResponseStatusSchema, MyPostResponse
from app.services.post_service import PostService
from app.core.cloudinary_config import upload_image

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)


@router.post("/")
async def create_post(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    duration: str | None = Form(None),
    images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    photo_url = []

    if images:
        for image in images:
            result = upload_image(image.file)
            photo_url.append(result["secure_url"])

    post = PostService.create_post(
        db=db,
        title=title,
        description=description,
        category=category,
        duration=duration,
        photo_url=photo_url,
        created_by=current_user["user_id"]
    )

    return {
        "message": "Post created successfully",
        "post_id": post.id
    }


@router.post("/{post_id}/quick-apply")
def quick_apply(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return PostService.quick_apply(
        db=db,
        post_id=post_id,
        user_id=current_user["user_id"]
    )


@router.get("/{post_id}/responses")
def get_post_responses(
    post_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return PostService.get_post_responses(
        db=db,
        post_id=post_id,
        user_id=current_user["user_id"]
    )


@router.put("/responses/{response_id}")
def update_response_status(
    response_id: int,
    payload: UpdateResponseStatusSchema,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return PostService.update_response_status(
        db=db,
        response_id=response_id,
        status=payload.status,
        user_id=current_user["user_id"]
    )


@router.get("/me", response_model=list[MyPostResponse])
def read_my_posts(
    limit: int = Query(10, le=50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return PostService.get_my_posts(
        db=db,
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset
    )
