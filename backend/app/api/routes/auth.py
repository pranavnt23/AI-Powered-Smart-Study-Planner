from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from email.message import EmailMessage
import os
import random
import smtplib
import logging

from app.schemas.auth_schema import (
    RegisterSchema,
    LoginSchema,
    SendOtpSchema,
    VerifyOtpSchema,
)
from app.services.auth_service import register_user, login_user
from app.core.database import SessionLocal

router = APIRouter(prefix="/auth", tags=["Auth"])

logger = logging.getLogger(__name__)

otp_store = {}
verified_emails = set()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def get_smtp_config():
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("EMAIL_FROM") or user or "no-reply@example.com"
    use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
    use_ssl = os.getenv("EMAIL_USE_SSL", "false").lower() in ("1", "true", "yes")
    no_auth = os.getenv("SMTP_NO_AUTH", "false").lower() in ("1", "true", "yes")
    debug_email = os.getenv("SMTP_DEBUG", "false").lower() in ("1", "true", "yes")

    if debug_email:
        return host, port, user, password, sender, use_tls, use_ssl, no_auth, debug_email

    if not host or not sender:
        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "message": "SMTP configuration is missing. Please set SMTP_HOST, SMTP_PORT, and EMAIL_FROM in your environment."
            }
        )

    if not no_auth and (not user or not password):
        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "message": "SMTP authentication is required. Please set SMTP_USER and SMTP_PASSWORD, or enable SMTP_NO_AUTH for a local unauthenticated SMTP server."
            }
        )

    return host, port, user, password, sender, use_tls, use_ssl, no_auth, debug_email


def send_otp_email(email: str, otp: str):
    host, port, user, password, sender, use_tls, use_ssl, no_auth, debug_email = get_smtp_config()

    message = EmailMessage()
    message["Subject"] = "Your Smart Study Planner verification code"
    message["From"] = sender
    message["To"] = email
    message.set_content(
        f"Your One-Time Password (OTP) is: {otp}\n\n"
        "Enter this code in the app to verify your email address. "
        "The code expires in 10 minutes."
    )

    if debug_email:
        print(f"[DEBUG EMAIL] Sending OTP to {email}: {otp}")
        return

    if use_ssl:
        server = smtplib.SMTP_SSL(host, port, timeout=15)
    else:
        server = smtplib.SMTP(host, port, timeout=15)

    with server:
        if use_tls and not use_ssl:
            server.starttls()

        if not no_auth and user and password:
            server.login(user, password)

        server.send_message(message)


@router.post("/send-otp")
def send_otp(data: SendOtpSchema):
    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    otp_store[data.email] = {
        "otp": otp,
        "expires": expires_at,
    }

    try:
        send_otp_email(data.email, otp)
    except smtplib.SMTPAuthenticationError as e:
        otp_store.pop(data.email, None)
        logger.exception("SMTP authentication failed while sending OTP")
        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "message": "Unable to send OTP: email provider authentication failed. Please check your SMTP credentials or use an app password."
            }
        )
    except smtplib.SMTPException as e:
        otp_store.pop(data.email, None)
        logger.exception("SMTP error while sending OTP")
        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "message": "Unable to send OTP due to an SMTP error. Please check your SMTP configuration."
            }
        )
    except Exception as e:
        otp_store.pop(data.email, None)
        logger.exception("Unexpected error while sending OTP")
        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "message": "Unable to send OTP due to an internal error. Please try again later."
            }
        )

    return {
        "status": True,
        "message": "OTP sent to your email address. Please check your inbox."
    }


@router.post("/verify-otp")
def verify_otp(data: VerifyOtpSchema):
    record = otp_store.get(data.email)

    if not record:
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "No OTP request found for this email. Please send OTP first."
            }
        )

    if datetime.utcnow() > record["expires"]:
        otp_store.pop(data.email, None)
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "OTP expired. Please request a new code."
            }
        )

    if record["otp"] != data.otp.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "Invalid OTP. Please check the code and try again."
            }
        )

    otp_store.pop(data.email, None)
    verified_emails.add(data.email)

    return {
        "status": True,
        "message": "Email verified successfully. You may continue with registration."
    }


@router.post("/register")
def register(
    data: RegisterSchema,
    db: Session = Depends(get_db)
):
    if data.email not in verified_emails:
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "Email must be verified before registration."
            }
        )

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

    verified_emails.discard(data.email)

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
