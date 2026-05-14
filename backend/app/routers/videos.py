from fastapi import APIRouter, Depends, HTTPException, Header
from app.schemas.video import VideoListResponse, VideoClaimRequest, VideoClaimResponse
from app.services import video_service
from app.repositories import participant_repository

router = APIRouter(prefix="/videos", tags=["Videos"])

async def get_current_participant(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer part-token-"):
        raise HTTPException(status_code=401, detail="Token de participante inválido ou não fornecido.")
    
    # Extrai o e-mail que vem diretamente embutido no token simulado "part-token-<email>"
    email = authorization.replace("Bearer part-token-", "")
    
    repo = participant_repository.ParticipantRepository()
    user = await repo.get_by_email(email)
    
    if not user:
        raise HTTPException(status_code=401, detail="Participante não encontrado no banco de dados.")
    
    return user["email"]

@router.get("", response_model=VideoListResponse)
def get_videos(email: str = Depends(get_current_participant)):
    return video_service.list_user_videos(email)

@router.post("", response_model=VideoClaimResponse, status_code=201)
def claim_video(request: VideoClaimRequest, email: str = Depends(get_current_participant)):
    return video_service.claim_video(email, request)
    
@router.get("/meus-videos", response_model=VideoListResponse, include_in_schema=False)
def get_meus_videos(email: str = Depends(get_current_participant)):
    return video_service.list_user_videos(email)

@router.post("/meus-videos", response_model=VideoClaimResponse, status_code=201, include_in_schema=False)
def claim_meus_videos(request: VideoClaimRequest, email: str = Depends(get_current_participant)):
    return video_service.claim_video(email, request)