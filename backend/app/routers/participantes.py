from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.dependencies import get_current_user
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
from app.schemas.participant import ParticipantResponse
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


@router.get("/me", response_model=ParticipantResponse)
async def obter_participante_atual(
    current_user_email: str = Depends(get_current_user),
) -> ParticipantResponse:
    participant = await ParticipantRepository().get_by_email(current_user_email)

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
    participant = await ParticipantRepository().get_by_email(current_user_email)

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

    participant_video_repository = ParticipantVideoRepository()
    video = await participant_video_repository.get_by_id_and_participant(
        participant["id"],
        video_id,
    )

    if video is None:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado para o participante.")

    file_id = str(video.get("file_id", "")).strip()
    if not file_id:
        raise HTTPException(
            status_code=404,
            detail="O arquivo deste vídeo ainda não foi salvo no banco de dados.",
        )

    stored_video_file = await VideoFileRepository().get_file(file_id)
    if stored_video_file is None:
        raise HTTPException(
            status_code=404,
            detail="O arquivo deste vídeo não pôde ser recuperado do banco de dados.",
        )

    if (
        stored_video_file.get("participant_id") != participant["id"]
        or stored_video_file.get("video_id") != video["id"]
    ):
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


@router.patch("/{participante_id}/status")
async def atualizar_status(participante_id: str, status: AtualizarStatusParticipacao):
    if status.status_gravacao not in ["ja_participei", "ainda_participarei"]:
        raise HTTPException(status_code=400, detail="Status inválido.")

    participant = await ParticipantRepository().update_fields(
        participante_id,
        {
            "status_gravacao": status.status_gravacao,
            "status_gravacao_atualizado_em": datetime.utcnow().replace(
                microsecond=0
            ).isoformat(),
        },
    )

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

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

    participant = await ParticipantRepository().update_fields(
        participante_id,
        {
            "consent_accepted": True,
            "consent": registro_auditoria["termo_aceite"],
        },
    )

    if participant is None:
        raise HTTPException(status_code=404, detail="Participante não encontrado.")

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
    "/me/video-do-dia/email",
    response_model=VideoEmailDispatchResponse,
    status_code=status.HTTP_200_OK,
)
async def enviar_video_do_dia_do_participante_atual_por_email(
    envio: VideoEmailDispatchRequest,
    current_user_email: str = Depends(get_current_user),
) -> VideoEmailDispatchResponse:
    participant = await ParticipantRepository().get_by_email(current_user_email)

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
