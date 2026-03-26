from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.posts import router as post_router
from app.routers.auth import router
from app.routers.feed import router as feed_router
from app.routers.search import router as search_router
from app.routers.profile import router as profile_router
from app.core.config import settings
from app.routers.skill_detail import router as skill_detail_router
app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ----- CORS CONFIG -----
origins = settings.ALLOWED_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(skill_detail_router)

