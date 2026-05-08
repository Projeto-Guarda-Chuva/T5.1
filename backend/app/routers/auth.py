from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.repositories.user_repository import UserRepository
from app.schemas.admin import AdminCreateRequest, AdminCreateResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

_auth_service = AuthService(UserRepository())


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest) -> TokenResponse:
    token = await _auth_service.authenticate(credentials.email, credentials.password)

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=token)


@router.post(
    "/register",
    response_model=AdminCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: AdminCreateRequest,
    _: str = Depends(get_current_user),
) -> AdminCreateResponse:
    admin = await _auth_service.create_admin(data)

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )

    return admin
