from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.session import UserSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)


def utc_now():
    return datetime.now(timezone.utc)

def register_user(
    db: Session,
    username: str,
    email: str,
    password: str
):
    email = email.strip().lower()

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        return None

    hashed_password = hash_password(password)

    new_user = User(
        username=username.strip(),
        email=email,
        password_hash=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

def login_user(
    db: Session,
    email: str,
    password: str
):
    login_id = email.strip().lower()

    user = db.query(User).filter(
        (User.email == login_id) | (func.lower(User.username) == login_id)
    ).first()

    if not user:
        return "not_found"

    if not verify_password(
        password,
        user.password_hash
    ):
        return "invalid_credentials"

    token = create_access_token({
        "sub": str(user.id),
        "email": user.email
    })

    user.last_login = utc_now()
    db.add(user)

    expires_at = utc_now() + timedelta(minutes=30)
    session_record = UserSession(
        user_id=user.id,
        session_token=token,
        expires_at=expires_at,
        is_active=True
    )

    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    return {
        "access_token": token,
        "token_type": "bearer",
        "session_id": session_record.id,
        "expires_at": expires_at.isoformat()
    }


def logout_session(
    db: Session,
    session_id: int
):
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.is_active == True
    ).first()

    if not session:
        return None

    session.is_active = False
    db.add(session)
    db.commit()
    db.refresh(session)

    return session
