from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.repositories.email_outbox_repository import EmailOutboxRepository
from app.repositories.participant_recording_event_repository import (
    ParticipantRecordingEventRepository,
)
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.participant_video_repository import ParticipantVideoRepository
from app.repositories.video_file_repository import VideoFileRepository
from app.repositories.video_email_dispatch_repository import (
    VideoEmailDispatchRepository,
)
from app.repositories.video_repository import VideoRepository
from app.schemas.participant import ParticipantResponse
from app.schemas.participant_recording import ParticipationEventResponse
from app.schemas.participant_video_email import (
    ParticipantVideoStorageResponse,
    VideoEmailDispatchRequest,
    VideoEmailDispatchResponse,
)
from app.schemas.video import VideoListResponse
from app.services import video_service
from app.services.participant_recording_service import ParticipantRecordingService
from app.services.participant_video_email_service import (
    ParticipantEmailMissingError,
    ParticipantNotFoundError,
    ParticipantVideoEmailService,
    ParticipantVideoFileMissingError,
    ParticipantVideoNotFoundError,
    ParticipantVideoUnavailableError,
)
from app.services.participant_video_storage_service import (
    ParticipantVideoStorageService,
    ParticipantVideoUploadInvalidError,
)
from app.services.video_email_sender import EmailDeliveryError, VideoEmailSender
from app.time_utils import utc_now

router = APIRouter(
    prefix="/participantes",
    tags=["Participantes"],
)
router_alias = APIRouter(
    prefix="/participants",
    tags=["Participants"],
)

participant_repository = ParticipantRepository()
participant_video_repository = ParticipantVideoRepository()
video_repository = VideoRepository()
video_file_repository = VideoFileRepository()
participant_recording_service = ParticipantRecordingService(
    participant_repository=participant_repository,
    event_repository=ParticipantRecordingEventRepository(),
    video_repository=video_repository,
    participant_video_repository=participant_video_repository,
)
participant_video_email_service = ParticipantVideoEmailService(
    participant_repository=participant_repository,
    video_repository=video_repository,
    participant_video_repository=participant_video_repository,
    dispatch_repository=VideoEmailDispatchRepository(),
    video_file_repository=video_file_repository,
    email_sender=VideoEmailSender(EmailOutboxRepository()),
)
participant_video_storage_service = ParticipantVideoStorageService(
    participant_repository=participant_repository,
    participant_video_repository=participant_video_repository,
    video_repository=video_repository,
    video_file_repository=video_file_repository,
)


class AtualizarStatusParticipacao(BaseModel):
    status_gravacao: str


class AceiteTermo(BaseModel):
    aceitou: bool
    versao_termo: str


@router.get("/me", response_model=ParticipantResponse)
async def obter_participante_atual(
    current_user_email: str = Depends(get_current_user),
) -> ParticipantResponse:
    participant = await participant_repository.get_by_email(current_user_email)

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    return ParticipantResponse(
        id=participant["id"],
        name=participant.get("name") or participant.get("nome") or "",
        email=participant["email"],
    )


@router.get("/me/videos/{video_id}/arquivo")
async def obter_arquivo_do_video_do_participante_atual(
    video_id: str,
    current_user_email: str = Depends(get_current_user),
) -> Response:
    participant = await participant_repository.get_by_email(current_user_email)

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    participant_video_link = await participant_video_repository.get_by_id_and_participant(
        participant["id"],
        video_id,
    )

    if participant_video_link is None:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado para o participante.")

    canonical_video = await video_repository.get_by_id(
        str(participant_video_link.get("video_id") or participant_video_link.get("id"))
    )

    if canonical_video is None:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado no catálogo principal.")

    file_id = str(canonical_video.get("file_id", "")).strip()
    if not file_id:
        raise HTTPException(
            status_code=404,
            detail="O arquivo deste vídeo ainda não foi salvo no banco de dados.",
        )

    stored_video_file = await video_file_repository.get_file(file_id)
    if stored_video_file is None:
        raise HTTPException(
            status_code=404,
            detail="O arquivo deste vídeo não pôde ser recuperado do banco de dados.",
        )

    if stored_video_file.get("video_id") != canonical_video["id"]:
        raise HTTPException(
            status_code=409,
            detail="O arquivo salvo no banco de dados não está vinculado a este vídeo.",
        )

    return Response(
        content=stored_video_file["content"],
        media_type=stored_video_file["content_type"],
        headers={
            "Content-Disposition": f'inline; filename="{stored_video_file["filename"]}"'
        },
    )


@router.post(
    "/me/ainda-vou-participar",
    response_model=ParticipationEventResponse,
    status_code=status.HTTP_200_OK,
)
@router_alias.post(
    "/will-participate",
    response_model=ParticipationEventResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def registrar_que_ainda_vai_participar(
    current_user_email: str = Depends(get_current_user),
) -> ParticipationEventResponse:
    participant = await participant_repository.get_by_email(current_user_email)

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    return await participant_recording_service.mark_will_participate(participant["id"])


@router.post(
    "/me/ja-participei",
    response_model=ParticipationEventResponse,
    status_code=status.HTTP_200_OK,
)
@router_alias.post(
    "/already-participated",
    response_model=ParticipationEventResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def registrar_que_ja_participou(
    current_user_email: str = Depends(get_current_user),
) -> ParticipationEventResponse:
    participant = await participant_repository.get_by_email(current_user_email)

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    return await participant_recording_service.mark_already_participated(
        participant["id"]
    )


@router.get(
    "/{participante_id}/videos",
    response_model=VideoListResponse,
    status_code=status.HTTP_200_OK,
)
@router_alias.get(
    "/{participante_id}/videos",
    response_model=VideoListResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def listar_videos_do_participante(
    participante_id: str,
    _: str = Depends(get_current_user),
) -> VideoListResponse:
    participant = await participant_repository.get_by_id(participante_id)

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    return await video_service.list_participant_videos(participante_id)


@router.patch("/{participante_id}/status", status_code=status.HTTP_200_OK)
async def atualizar_status(
    participante_id: str,
    status_payload: AtualizarStatusParticipacao,
) -> dict:
    try:
        event_response = await participant_recording_service.register_status(
            participante_id,
            status_payload.status_gravacao,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "não encontrado" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    return {
        "message": "Status atualizado com sucesso!",
        "participante_id": event_response.participant_id,
        "novo_status": status_payload.status_gravacao,
        "registrado_em": event_response.recorded_at,
        "videos_associados": event_response.associated_video_ids,
    }


@router.patch("/{participante_id}/aceite-termo")
async def registrar_aceite_termo(participante_id: str, aceite: AceiteTermo):
    if not aceite.aceitou:
        raise HTTPException(
            status_code=400,
            detail="O participante deve aceitar o termo para prosseguir.",
        )

    normalized_term_version = aceite.versao_termo.strip()

    if not normalized_term_version:
        raise HTTPException(
            status_code=400,
            detail="A versão do termo precisa ser informada.",
        )

    participant = await participant_repository.update_fields(
        participante_id,
        {
            "consent_accepted": True,
            "consent": {
                "aceitou": aceite.aceitou,
                "data_hora_aceite": utc_now().isoformat(),
                "versao_termo": normalized_term_version,
            },
        },
    )

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    return {
        "message": "Aceite do termo registrado com sucesso!",
        "participante_id": participante_id,
        "auditoria": participant["consent"],
    }


@router.post(
    "/{participante_id}/videos/{video_id}/arquivo",
    response_model=ParticipantVideoStorageResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def salvar_arquivo_de_video(
    participante_id: str,
    video_id: str,
    video: UploadFile = File(...),
) -> ParticipantVideoStorageResponse:
    try:
        saved_video = await participant_video_storage_service.attach_video_file(
            participante_id,
            video_id,
            filename=video.filename or "video.mp4",
            content_type=video.content_type,
            file_bytes=await video.read(),
        )
    except ParticipantVideoUploadInvalidError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        await video.close()

    return ParticipantVideoStorageResponse(
        participant_id=participante_id,
        video={
            "id": saved_video["id"],
            "title": saved_video["title"],
            "recorded_at": saved_video["recorded_at"],
            "filename": saved_video["filename"],
            "content_type": saved_video["content_type"],
            "size_bytes": saved_video["size_bytes"],
        },
        message="Arquivo do vídeo salvo no MongoDB com sucesso.",
    )


@router.post(
    "/me/video-do-dia/email",
    response_model=VideoEmailDispatchResponse,
    status_code=status.HTTP_200_OK,
)
async def enviar_video_do_dia_do_participante_atual_por_email(
    envio: VideoEmailDispatchRequest,
    current_user_email: str = Depends(get_current_user),
) -> VideoEmailDispatchResponse:
    participant = await participant_repository.get_by_email(current_user_email)

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    try:
        return await participant_video_email_service.send_video_of_day(
            participant["id"],
            envio,
        )
    except ParticipantEmailMissingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ParticipantVideoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ParticipantVideoUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ParticipantVideoFileMissingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post(
    "/{participante_id}/video-do-dia/email",
    response_model=VideoEmailDispatchResponse,
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/{participante_id}/videos/enviar-email",
    response_model=VideoEmailDispatchResponse,
    include_in_schema=False,
)
async def enviar_video_do_dia_por_email(
    participante_id: str,
    envio: VideoEmailDispatchRequest,
) -> VideoEmailDispatchResponse:
    try:
        return await participant_video_email_service.send_video_of_day(
            participante_id,
            envio,
        )
    except ParticipantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ParticipantEmailMissingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ParticipantVideoNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ParticipantVideoUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ParticipantVideoFileMissingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
