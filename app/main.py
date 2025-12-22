from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routers.auth import router
from app.database import engine, Base
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# ----- CORS CONFIG -----
origins = [
    "*"   # Allow all origins (for testing)
    # Later, you can restrict:
    # "http://localhost:3000",
    # "http://localhost:5173",
    # "https://your-flutter-web-app.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- SESSION MIDDLEWARE (OAuth) -----
app.add_middleware(SessionMiddleware, secret_key="fssvsdvadvdv")

# ----- CREATE DATABASE TABLES -----
Base.metadata.create_all(bind=engine)

# ----- HEALTH CHECK -----
@app.get("/healthy")
async def check_healthy():
    return {"status": "Healthy"}

# ----- ROUTES -----
app.include_router(router)
