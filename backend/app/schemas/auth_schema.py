from pydantic import BaseModel
from pydantic import EmailStr

class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: str
    password: str

class SendOtpSchema(BaseModel):
    email: EmailStr

class VerifyOtpSchema(BaseModel):
    email: EmailStr
    otp: str

class LogoutSchema(BaseModel):
    session_id: int
