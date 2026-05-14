from datetime import datetime
from fastapi import HTTPException
from app.repositories import video_repository
from app.schemas.video import VideoListResponse, VideoClaimRequest, VideoClaimResponse

def list_user_videos(email: str) -> VideoListResponse:
    videos = video_repository.get_videos_by_email(email)
    return VideoListResponse(
        items=videos,
        total=len(videos),
        message="Videos retrieved successfully." if videos else "Nenhum vídeo encontrado."
    )

def claim_video(user_email: str, request: VideoClaimRequest) -> VideoClaimResponse:
    unclaimed_videos = video_repository.get_unclaimed_videos()
    
    # O horário da requisição vem no formato "HH:MM"
    req_hour, req_minute = map(int, request.participation_time.split(":"))
    
    target_video = None
    for v in unclaimed_videos:
        try:
            # Exemplo de data no JSON: "2026-05-14T14:30:00"
            video_dt = datetime.fromisoformat(v["created_at"])
            # Procura um vídeo com o mesmo horário e minuto (simplificado para o escopo atual)
            if video_dt.hour == req_hour and video_dt.minute == req_minute:
                target_video = v
                break
        except ValueError:
            continue
            
    if not target_video:
        raise HTTPException(status_code=404, detail="Não conseguimos localizar nenhum vídeo com esse horário exato.")
        
    updated_video = video_repository.update_video_participant(target_video["id"], user_email)
    
    return VideoClaimResponse(
        **updated_video,
        message="Video associado à sua conta com sucesso."
    )