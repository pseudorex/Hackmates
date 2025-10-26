# main.py
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from models import Base
from database import engine
from routers import auth

app = FastAPI()

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key="fssvsdvadvdv")

# Create DB tables
Base.metadata.create_all(bind=engine)

# Health check
@app.get("/healthy")
async def check_healthy():
    return {"status": "Healthy"}

# Include routers
app.include_router(auth.router)

