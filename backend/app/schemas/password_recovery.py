from pydantic import BaseModel, EmailStr, Field, model_validator


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)
    password_confirmation: str

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.password != self.password_confirmation:
            raise ValueError("As senhas não coincidem.")
        return self
