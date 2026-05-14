import uuid
from fastapi import HTTPException
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.repositories import participant_repository

def register_user(data: UserCreate) -> TokenResponse:
    if participant_repository.get_user_by_email(data.email):
        raise HTTPException(status_code=400, detail="Este e-mail já está em uso.")

    new_user = {
        "id": f"usr-{uuid.uuid4().hex[:8]}",
        "name": data.name,
        "email": data.email,
        "password": data.password,  # Em produção, senhas devem ter hash aplicado (ex: passlib)
        "consent_accepted": data.consent_accepted
    }
    
    participant_repository.create_user(new_user)
    token = f"fake-jwt-token-{new_user['id']}"
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(**new_user)
    )

def login_user(data: UserLogin) -> TokenResponse:
    user = participant_repository.get_user_by_email(data.email)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
        
    token = f"fake-jwt-token-{user['id']}"
    return TokenResponse(access_token=token, user=UserResponse(**user))