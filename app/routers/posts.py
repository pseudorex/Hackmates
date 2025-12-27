from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.post_response import PostResponse
from app.models.posts import Post
from app.core.cloudinary_config import upload_image
from app.schemas.post_response import UpdateResponseStatusSchema
from app.services.post_service import PostService

router = APIRouter(
    prefix="/posts",
    tags=["Posts"]
)

@router.post("/")
async def create_post(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    duration: str = Form(None),
    photo: UploadFile = File(None),

    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    photo_url = None

    if photo:
        result = upload_image(photo.file)
        photo_url = result.get("secure_url")

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
    current_user = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Cannot apply to own post
    if post.created_by == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot apply to your own post")

    existing = db.query(PostResponse).filter(
        PostResponse.post_id == post_id,
        PostResponse.responder_id == current_user["user_id"]
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already applied")

    response = PostResponse(
        post_id=post_id,
        responder_id=current_user["user_id"],
        message="Quick applied"
    )

    db.add(response)
    db.commit()

    return {
        "message": "Quick apply successful",
        "status": "pending"
    }



@router.get("/{post_id}/responses")
def get_post_responses(
    post_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post or post.created_by != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return db.query(PostResponse).filter(
        PostResponse.post_id == post_id
    ).all()


@router.put("/responses/{response_id}")
def update_response_status(
    response_id: int,
    payload: UpdateResponseStatusSchema,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    response = db.query(PostResponse).filter(PostResponse.id == response_id).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    post = db.query(Post).filter(Post.id == response.post_id).first()

    if post.created_by != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    response.status = payload.status
    db.commit()

    return {
        "message": f"Response {payload.status}",
        "chat_enabled": False
    }
