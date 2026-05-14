from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.repositories.email_outbox_repository import EmailOutboxRepository
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.participant_video_repository import ParticipantVideoRepository
from app.repositories.video_file_repository import VideoFileRepository
from app.repositories.video_email_dispatch_repository import (
    VideoEmailDispatchRepository,
)
from app.schemas.participant_video_email import (
    ParticipantVideoStorageResponse,
    VideoEmailDispatchRequest,
    VideoEmailDispatchResponse,
)
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

router = APIRouter(
    prefix="/participantes",
    tags=["Participantes"],
)

participant_video_email_service = ParticipantVideoEmailService(
    participant_repository=ParticipantRepository(),
    video_repository=ParticipantVideoRepository(),
    dispatch_repository=VideoEmailDispatchRepository(),
    video_file_repository=VideoFileRepository(),
    email_sender=VideoEmailSender(EmailOutboxRepository()),
)
participant_video_storage_service = ParticipantVideoStorageService(
    participant_repository=ParticipantRepository(),
    video_repository=ParticipantVideoRepository(),
    video_file_repository=VideoFileRepository(),
)


class AtualizarStatusParticipacao(BaseModel):
    status_gravacao: str


@router.patch("/{participante_id}/status")
async def atualizar_status(participante_id: str, status: AtualizarStatusParticipacao):
    if status.status_gravacao not in ["ja_participei", "ainda_participarei"]:
        raise HTTPException(status_code=400, detail="Status inválido.")

    # TODO: Integração com MongoDB

    return {
        "message": "Status atualizado com sucesso!",
        "participante_id": participante_id,
        "novo_status": status.status_gravacao,
    }


class AceiteTermo(BaseModel):
    aceitou: bool
    versao_termo: str


@router.patch("/{participante_id}/aceite-termo")
async def registrar_aceite_termo(participante_id: str, aceite: AceiteTermo):
    if not aceite.aceitou:
        raise HTTPException(
            status_code=400,
            detail="O participante deve aceitar o termo para prosseguir.",
        )

    data_hora_atual = datetime.utcnow().isoformat()
    registro_auditoria = {
        "termo_aceite": {
            "aceitou": aceite.aceitou,
            "data_hora_aceite": data_hora_atual,
            "versao_termo": aceite.versao_termo,
        }
    }

    # TODO: Integração com MongoDB

    return {
        "message": "Aceite do termo registrado com sucesso!",
        "participante_id": participante_id,
        "auditoria": registro_auditoria["termo_aceite"],
    }


@router.post(
    "/{participante_id}/videos/{video_id}/arquivo",
    response_model=ParticipantVideoStorageResponse,
    status_code=status.HTTP_201_CREATED,
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
