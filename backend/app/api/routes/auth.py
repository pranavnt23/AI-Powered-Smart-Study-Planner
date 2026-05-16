from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.auth_schema import RegisterSchema, LoginSchema
from app.services.auth_service import register_user, login_user
from app.core.database import SessionLocal

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register(
    data: RegisterSchema,
    db: Session = Depends(get_db)
):

    user = register_user(
        db,
        data.username,
        data.email,
        data.password
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "Email already exists"
            }
        )

    return {
        "status": True,
        "message": "User registered successfully",
        "data": {
            "username": user.username,
            "email": user.email
        }
    }

@router.post("/login")
def login(
    data: LoginSchema,
    db: Session = Depends(get_db)
):

    result = login_user(
        db,
        data.email,
        data.password
    )

    if not result:
        raise HTTPException(
            status_code=401,
            detail={
                "status": False,
                "message": "Invalid credentials"
            }
        )

    return {
        "status": True,
        "message": "Login successful",
        "data": result
    }