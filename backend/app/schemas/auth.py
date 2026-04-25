from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    tenant_name: str
    name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    tenant_id: int
    name: str
    email: EmailStr
