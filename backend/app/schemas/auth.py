from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., min_length=1)


class GoogleLoginResponse(TokenResponse):
    participant_id: str
    email: str
    nome: str
    is_new_user: bool = False


class RegisterRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterResponse(BaseModel):
    participant_id: str
    email: str
    nome: str
    message: str
