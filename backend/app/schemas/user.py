from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: str
    email: EmailStr
    name: str

    class Config:
        from_attributes = True  # for ORM objects
