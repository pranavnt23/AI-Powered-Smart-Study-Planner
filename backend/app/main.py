from fastapi import FastAPI

from app.api.routes.auth import router as auth_router

from app.core.database import (
    Base,
    engine
)

from app.models.user import User
from app.models.email_verification import EmailVerification

Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth_router)

@app.get("/")
def home():
    return {
        "message": "AI Smart Study Planner Backend Running"
    }