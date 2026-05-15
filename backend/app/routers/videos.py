from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.video import VideoListResponse, VideoClaimRequest, VideoClaimResponse
from app.services import video_service

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.get("", response_model=VideoListResponse)
async def get_videos(email: str = Depends(get_current_user)):
    return await video_service.list_user_videos(email)

@router.post("", response_model=VideoClaimResponse, status_code=201)
async def claim_video(request: VideoClaimRequest, email: str = Depends(get_current_user)):
    return await video_service.claim_video(email, request)
    
@router.get("/meus-videos", response_model=VideoListResponse, include_in_schema=False)
async def get_meus_videos(email: str = Depends(get_current_user)):
    return await video_service.list_user_videos(email)

@router.post("/meus-videos", response_model=VideoClaimResponse, status_code=201, include_in_schema=False)
async def claim_meus_videos(request: VideoClaimRequest, email: str = Depends(get_current_user)):
    return await video_service.claim_video(email, request)
