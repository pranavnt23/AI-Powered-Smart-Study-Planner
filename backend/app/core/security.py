from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
import os
import hashlib
import hmac
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") or "super-secret-require-production"
ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(
    plain_password: str,
    hashed_password: str
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def hash_otp(otp: str):
    return hmac.new(
        SECRET_KEY.encode(),
        otp.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_otp_hash(otp: str, otp_hash: str):
    return hmac.compare_digest(
        hmac.new(
            SECRET_KEY.encode(),
            otp.encode(),
            hashlib.sha256
        ).hexdigest(),
        otp_hash
    )


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
