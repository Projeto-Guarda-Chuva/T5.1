from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext

from app.dependencies import get_current_user
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.user_repository import UserRepository
from app.schemas.admin import AdminCreateRequest, AdminCreateResponse
from app.schemas.auth import (
    GoogleLoginRequest,
    GoogleLoginResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.change_password import ChangePasswordRequest
from app.schemas.password_recovery import ForgotPasswordRequest, ResetPasswordRequest
from app.services.auth_service import (
    AuthService,
    GoogleAuthConfigurationError,
    GoogleAuthError,
    GoogleAuthUnavailableError,
)
from app.services.email_service import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Auth"])

_auth_service = AuthService(UserRepository())
_user_repo = UserRepository()
_participant_repo = ParticipantRepository()
_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


@router.post("/google", response_model=GoogleLoginResponse, status_code=status.HTTP_200_OK)
async def login_with_google(payload: GoogleLoginRequest) -> GoogleLoginResponse:
    try:
        auth_result = await _auth_service.authenticate_google(payload.credential)
    except GoogleAuthConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except GoogleAuthUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except GoogleAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    participant = await _participant_repo.get_by_email(auth_result["email"])

    if participant is None:
        participant = await _participant_repo.create(
            {
                "id": f"part-{uuid4().hex[:8]}",
                "name": auth_result["name"],
                "email": auth_result["email"],
                "registered_at": datetime.utcnow().replace(microsecond=0).isoformat(),
                "consent_accepted": False,
            }
        )
    elif not participant.get("name"):
        participant = await _participant_repo.update_fields(
            participant["id"],
            {"name": auth_result["name"]},
        )

    return GoogleLoginResponse(
        access_token=auth_result["access_token"],
        participant_id=participant["id"],
        email=auth_result["email"],
        nome=auth_result["name"],
        is_new_user=bool(auth_result["is_new_user"]),
    )


@router.post("/register-participante", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_participante(data: RegisterRequest) -> RegisterResponse:
    """Registra um novo participante (público, sem autenticação)"""
    if await _user_repo.exists_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        )
    
    hashed_password = _password_context.hash(data.password)
    user_data = {
        "nome": data.nome,
        "email": data.email,
        "hashed_password": hashed_password,
        "is_active": True,
    }
    
    await _user_repo.create(user_data)

    participant = await _participant_repo.get_by_email(data.email)

    if participant is None:
        participant = await _participant_repo.create(
            {
                "id": f"part-{uuid4().hex[:8]}",
                "name": data.nome,
                "email": data.email,
                "registered_at": datetime.utcnow().replace(microsecond=0).isoformat(),
                "consent_accepted": False,
            }
        )
    
    return RegisterResponse(
        participant_id=participant["id"],
        email=data.email,
        nome=data.nome,
        message="Cadastro realizado com sucesso!"
    )


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


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(data: ForgotPasswordRequest) -> dict:
    code = await _auth_service.generate_reset_code(data.email)

    if code is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="E-mail não cadastrado.",
        )

    await send_password_reset_email(data.email, code)
    return {"message": "Código de recuperação enviado para o e-mail."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(data: ResetPasswordRequest) -> dict:
    success = await _auth_service.reset_password(data.email, data.code, data.password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado.",
        )

    return {"message": "Senha redefinida com sucesso."}


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    current_user: str = Depends(get_current_user),
) -> dict:
    success = await _auth_service.change_password(
        current_user, data.current_password, data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta.",
        )

    return {"message": "Senha alterada com sucesso."}
