from pydantic import BaseModel, EmailStr, Field, model_validator


class AdminCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)
    password_confirmation: str

    @model_validator(mode="after")
    def passwords_match(self) -> "AdminCreateRequest":
        if self.password != self.password_confirmation:
            raise ValueError("As senhas não coincidem.")
        return self


class AdminCreateResponse(BaseModel):
    name: str
    email: str
    is_active: bool
