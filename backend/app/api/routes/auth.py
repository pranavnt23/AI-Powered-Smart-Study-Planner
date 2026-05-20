from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
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
    LogoutSchema,
)
from app.services.auth_service import register_user, login_user, logout_session
from app.core.database import SessionLocal
from app.models.email_verification import EmailVerification
from app.core.security import hash_otp, verify_otp_hash

router = APIRouter(prefix="/auth", tags=["Auth"])

logger = logging.getLogger(__name__)


def utc_now():
    return datetime.now(timezone.utc)


def as_aware_utc(value: datetime):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password(password: str) -> bool:
    return len(password) >= 8


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
    message["Subject"] = "🚀 Smart Study Planner - Verification Code"
    message["From"] = sender
    message["To"] = email

    # -----------------------------
    # Plain text fallback
    # -----------------------------
    text_content = f"""
Smart Study Planner Verification

Your OTP is: {otp}

This code expires in 10 minutes.

If this wasn't you, ignore this email.

Smart Study AI
"""

    message.set_content(text_content)

    # -----------------------------
    # DARK THEME HTML EMAIL
    # -----------------------------
    html_content = f"""
    <html>
      <body style="margin:0; padding:0; font-family:Arial, sans-serif; background-color:#0f172a;">
        
        <div style="max-width:520px; margin:40px auto; background-color:#111827; padding:28px; border-radius:44px; box-shadow:0 10px 25px rgba(0,0,0,0.6);">

          <h2 style="color:#6366f1; text-align:center; margin-bottom:10px;">
            🚀 Smart Study Planner
          </h2>

          <p style="color:#e5e7eb; font-size:15px;">
            Hello,
          </p>

          <p style="color:#9ca3af; font-size:14px;">
            Use the OTP below to verify your email address:
          </p>

          <div style="text-align:center; margin:30px 0;">
            <div style="display:inline-block; padding:14px 24px; border-radius:10px; background-color:#1f2937; border:1px solid #374151;">
              <span style="font-size:28px; letter-spacing:6px; font-weight:bold; color:#ffffff;">
                {otp}
              </span>
            </div>
          </div>

          <p style="text-align:center; color:#fbbf24; font-weight:bold; font-size:14px;">
            ⏳ Expires in 10 minutes
          </p>

          <div style="margin-top:25px; padding-top:15px; border-top:1px solid #374151;">
            
            <p style="color:#6b7280; font-size:12px;">
              If you did not request this code, you can safely ignore this email.
            </p>

            <p style="color:#4b5563; font-size:11px; text-align:center; margin-top:15px;">
              © Smart Study AI • Your Personalized Learning Assistant
            </p>

          </div>

        </div>

      </body>
    </html>
    """

    message.add_alternative(html_content, subtype="html")

    # -----------------------------
    # Debug mode
    # -----------------------------
    if debug_email:
        print(f"[DEBUG EMAIL] Sending OTP to {email}: {otp}")
        return

    # -----------------------------
    # SMTP CONNECTION
    # -----------------------------
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
def send_otp(
    data: SendOtpSchema,
    db: Session = Depends(get_db)
):
    email = normalize_email(data.email)
    otp = generate_otp()
    expires_at = utc_now() + timedelta(minutes=10)
    otp_hash = hash_otp(otp)

    verification = EmailVerification(
        email=email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        is_used=False
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    try:
        send_otp_email(data.email, otp)
    except smtplib.SMTPAuthenticationError:
        db.delete(verification)
        db.commit()
        logger.exception("SMTP authentication failed while sending OTP")
        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "message": "Unable to send OTP: email provider authentication failed. Please check your SMTP credentials or use an app password."
            }
        )
    except smtplib.SMTPException:
        db.delete(verification)
        db.commit()
        logger.exception("SMTP error while sending OTP")
        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "message": "Unable to send OTP due to an SMTP error. Please check your SMTP configuration."
            }
        )
    except Exception:
        db.delete(verification)
        db.commit()
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
def verify_otp(
    data: VerifyOtpSchema,
    db: Session = Depends(get_db)
):
    email = normalize_email(data.email)
    record = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.is_used == False
    ).order_by(EmailVerification.created_at.desc()).first()

    if not record:
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "No active OTP request found for this email. Please request a new code."
            }
        )

    if utc_now() > as_aware_utc(record.expires_at):
        record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "OTP expired. Please request a new verification code."
            }
        )

    if not verify_otp_hash(data.otp.strip(), record.otp_hash):
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "Invalid OTP. Please check the one-time code and try again."
            }
        )

    record.is_used = True
    record.verified_at = utc_now()
    db.commit()

    return {
        "status": True,
        "message": "Email verified successfully. You may continue with registration."
    }


@router.post("/register")
def register(
    data: RegisterSchema,
    db: Session = Depends(get_db)
):
    email = normalize_email(data.email)

    if len(data.username.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "Username must be at least 3 characters long."
            }
        )

    if not validate_password(data.password):
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "Password must be at least 8 characters long."
            }
        )

    verification_record = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.is_used == True,
        EmailVerification.verified_at != None
    ).order_by(EmailVerification.verified_at.desc()).first()

    if not verification_record:
        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "message": "Email must be verified before registration. Request a verification code and confirm it first."
            }
        )

    user = register_user(
        db,
        data.username,
        email,
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

    if result != None and isinstance(result, str):
        raise HTTPException(
            status_code=401,
            detail={
                "status": False,
                "message": "Invalid email or password."
            }
        )

    return {
        "status": True,
        "message": "Login successful",
        "data": result
    }


@router.post("/logout")
def logout(
    data: LogoutSchema,
    db: Session = Depends(get_db)
):
    session = logout_session(db, data.session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "status": False,
                "message": "Session not found or already ended."
            }
        )

    return {
        "status": True,
        "message": "Logged out successfully."
    }

