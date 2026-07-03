from pydantic import BaseModel, EmailStr, Field, field_validator


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

    @field_validator("nome")
    @classmethod
    def validate_nome(cls, value: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("must contain at least 1 character")

        return normalized_value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must contain at least 1 character")

        return value


class RegisterResponse(BaseModel):
    participant_id: str
    email: str
    nome: str
    message: str
