from urllib.parse import urlencode

from google.auth.exceptions import InvalidValue
from starlette.responses import RedirectResponse
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
import httpx

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings
from app.core.oauth_config import oauth
from app.models.users import Users
from app.core.jwt_utils import create_access_token
from app.redis_client import redis_client

import json, uuid


class OAuthService:

    @staticmethod
    async def login(provider: str, request: Request):
        # 🔹 Google → STATELESS
        if provider == "google":
            params = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": f"{settings.REDIRECT_URI}/google/callback",
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "select_account",
            }

            url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
            return RedirectResponse(url)

        # 🔹 GitHub → keep Authlib (stateful)
        client = oauth.create_client(provider)
        redirect_uri = f"{settings.REDIRECT_URI}/{provider}/callback"
        return await client.authorize_redirect(request, redirect_uri)

    # --------------------------------------------------

    @staticmethod
    async def callback(provider: str, request: Request, db: Session):

        # 🔹 GOOGLE CALLBACK (STATELESS)
        if provider == "google":
            code = request.query_params.get("code")
            if not code:
                raise HTTPException(status_code=400, detail="Missing code")

            # Exchange code → token
            async with httpx.AsyncClient() as client:
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": f"{settings.REDIRECT_URI}/google/callback",
                    }
                )

            token_data = token_res.json()

            if "id_token" not in token_data:
                raise HTTPException(status_code=400, detail="Invalid Google token")

            # Verify ID token
            try:
                idinfo = id_token.verify_oauth2_token(
                    token_data["id_token"],
                    google_requests.Request(),
                    settings.GOOGLE_CLIENT_ID,
                    clock_skew_in_seconds=5
                )
            except InvalidValue:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid or expired Google token. Try again."
                )

            email = idinfo["email"]
            full_name = idinfo.get("name", "")
            photo = idinfo.get("picture")

        # 🔹 GITHUB CALLBACK (STATEFUL – unchanged)
        else:
            client = oauth.create_client(provider)
            token = await client.authorize_access_token(request)

            user = await client.get("user", token=token)
            emails = await client.get("user/emails", token=token)

            email = emails.json()[0]["email"]
            full_name = user.json().get("login")
            photo = user.json().get("avatar_url")

        # --------------------------------------------------
        # USER CREATION / LOGIN (UNCHANGED)

        first, *rest = full_name.split()
        last = " ".join(rest)

        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            user = Users(
                email=email,
                first_name=first,
                last_name=last,
                is_verified=True,
                profile_image=photo,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt = create_access_token(
            email=user.email,
            user_id=user.id,
            expires_delta=timedelta(minutes=30),
        )

        key = str(uuid.uuid4())
        redis_client.set(f"user_token:{key}", jwt, ex=120)

        redis_client.set(
            f"user_data:{key}",
            json.dumps({
                "id": user.id,
                "email": user.email,
                "name": user.first_name,
                "photoUrl": user.profile_image,
            }),
            ex=120,
        )

        return RedirectResponse(
            f"hackmates://oauth/callback?key={key}"
        )
