from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.routers.posts import router as post_router
from app.routers.auth import router
from app.routers.feed import router as feed_router
from app.routers.search import router as search_router
from app.routers.profile import router as profile_router

app = FastAPI()

# ----- CORS CONFIG -----
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- SESSION MIDDLEWARE (OAuth) -----
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    same_site="lax",
    https_only=False
)

# ----- HEALTH CHECK -----
@app.get("/healthy")
async def check_healthy():
    return {"status": "Healthy"}

# ----- ROUTES -----
app.include_router(router)
app.include_router(post_router)
app.include_router(feed_router)
app.include_router(search_router)
app.include_router(profile_router)
