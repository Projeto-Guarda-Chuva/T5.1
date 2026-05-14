from fastapi import APIRouter
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(user_data: UserCreate):
    return user_service.register_user(user_data)

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin):
    return user_service.login_user(user_data)