import json, uuid
from fastapi import Request
from sqlalchemy.orm import Session
from datetime import timedelta
from starlette.responses import HTMLResponse

from app.models.users import Users
from app.redis_client import redis_client
from app.core.oauth_config import oauth
from app.core.config import settings
from app.core.jwt_utils import create_access_token

REDIRECT_URI = settings.REDIRECT_URI

class OAuthService:

    @staticmethod
    async def login(provider: str, request: Request):
        client = oauth.create_client(provider)
        return await client.authorize_redirect(request, REDIRECT_URI)

    @staticmethod
    async def callback(request: Request, db: Session):
        is_google = "google" in str(request.url)
        provider = oauth.create_client("google" if is_google else "github")

        token = await provider.authorize_access_token(request)

        if is_google:
            info = token["userinfo"]
            email = info["email"]
            full_name = info.get("name", "")
            photo = info.get("picture")
        else:
            user = await provider.get("user", token=token)
            emails = await provider.get("user/emails", token=token)
            email = emails.json()[0]["email"]
            full_name = user.json().get("login")
            photo = user.json().get("avatar_url")

        first, *rest = full_name.split()
        last = " ".join(rest)

        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            user = Users(
                email=email,
                first_name=first,
                last_name=last,
                is_verified=True,
                profile_image=photo
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt = create_access_token(email=user.email, user_id=user.id, expires_delta=timedelta(minutes=30))
        key = str(uuid.uuid4())

        redis_client.set(f"user_token:{key}", jwt, ex=120)
        redis_client.set(f"user_data:{key}", json.dumps({
            "id": user.id,
            "email": user.email,
            "name": user.first_name,
            "photoUrl": user.profile_image
        }), ex=120)

        return HTMLResponse(
            f"<script>window.location.href='hackmates://oauth/callback?key={key}'</script>"
        )
