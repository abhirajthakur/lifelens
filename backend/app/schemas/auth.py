from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str


class TokenData(BaseModel):
    user_id: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class SingupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
