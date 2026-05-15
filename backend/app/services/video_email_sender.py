import asyncio
import logging
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    """Raised when the email provider cannot deliver the message."""


class VideoEmailSender:
    """Send the participant video email using SMTP or a local development outbox."""

    def __init__(self, outbox_repository) -> None:
        self._outbox_repository = outbox_repository

    async def send_video_email(
        self,
        participant: dict[str, Any],
        video: dict[str, Any],
        video_file: dict[str, Any],
        reference_date: date,
    ) -> dict[str, str]:
        message = self._build_message(participant, video, video_file, reference_date)

        if self._smtp_is_configured():
            await asyncio.to_thread(self._send_via_smtp, message)
            return {"delivery_mode": "smtp"}

        await self._queue_in_outbox(
            message,
            participant,
            video,
            video_file,
            reference_date,
        )
        return {"delivery_mode": "outbox"}

    def _build_message(
        self,
        participant: dict[str, Any],
        video: dict[str, Any],
        video_file: dict[str, Any],
        reference_date: date,
    ) -> EmailMessage:
        formatted_date = reference_date.strftime("%d/%m/%Y")
        formatted_recorded_at = self._format_recorded_at(video.get("recorded_at"))
        formatted_file_size = self._format_size_bytes(video_file["size_bytes"])
        participant_name = self._resolve_participant_name(participant)
        subject = f"Projeto Guarda-Chuva | Vídeo da sua participação"

        greeting = (
            f"Olá, {participant_name}!"
            if participant_name
            else "Olá!"
        )

        body = (
            f"{greeting}\n\n"
            "Encaminhamos em anexo o vídeo da sua participação no Projeto Guarda-Chuva.\n\n"
            "Detalhes do envio:\n"
            f"- Data da participação: {formatted_date}\n"
            f"- Horário da gravação: {formatted_recorded_at}\n"
            f"- Referência do conteúdo: {video.get('title', 'Vídeo da sua participação')}\n"
            "- Formato do arquivo: vídeo MP4\n"
            f"- Tamanho do arquivo: {formatted_file_size}\n\n"
            "Recomendamos guardar esta mensagem caso você queira acessar o arquivo novamente mais tarde.\n\n"
            "Atenciosamente,\n"
            "Equipe do Projeto Guarda-Chuva\n"
        )

        message = EmailMessage()
        message["To"] = participant["email"]
        message["Subject"] = subject
        message["From"] = settings.resolved_smtp_from_email or "no-reply@aguaviva.local"
        message.set_content(body)
        maintype, subtype = self._split_content_type(video_file["content_type"])
        message.add_attachment(
            video_file["content"],
            maintype=maintype,
            subtype=subtype,
            filename=video_file["filename"],
        )
        return message

    def _resolve_participant_name(self, participant: dict[str, Any]) -> str:
        raw_name = participant.get("name") or participant.get("nome") or ""
        return str(raw_name).strip()

    def _smtp_is_configured(self) -> bool:
        return bool(settings.resolved_smtp_host and settings.resolved_smtp_from_email)

    def _send_via_smtp(self, message: EmailMessage) -> None:
        try:
            with smtplib.SMTP(
                settings.resolved_smtp_host,
                settings.resolved_smtp_port,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            ) as smtp_client:
                smtp_client.ehlo()

                if settings.resolved_smtp_use_starttls:
                    smtp_client.starttls()
                    smtp_client.ehlo()

                if settings.resolved_smtp_username:
                    smtp_client.login(
                        settings.resolved_smtp_username,
                        settings.resolved_smtp_password or "",
                    )

                smtp_client.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            logger.exception("Failed to send attached video email via SMTP.")
            raise EmailDeliveryError(
                "Falha ao enviar o e-mail com o vídeo anexado."
            ) from exc

    async def _queue_in_outbox(
        self,
        message: EmailMessage,
        participant: dict[str, Any],
        video: dict[str, Any],
        video_file: dict[str, Any],
        reference_date: date,
    ) -> None:
        if message.is_multipart():
            body_part = message.get_body(preferencelist=("plain",))
            body_text = body_part.get_content() if body_part is not None else ""
        else:
            body_text = message.get_content()

        await self._outbox_repository.create(
            {
                "queued_at": datetime.utcnow().replace(microsecond=0).isoformat(),
                "participant_id": participant["id"],
                "participant_email": participant["email"],
                "reference_date": reference_date.isoformat(),
                "video_id": video["id"],
                "subject": message["Subject"],
                "body": body_text,
                "attachment_filename": video_file["filename"],
                "attachment_content_type": video_file["content_type"],
                "attachment_size_bytes": video_file["size_bytes"],
                "video_file_id": video_file["file_id"],
            }
        )

    def _format_recorded_at(self, recorded_at: str | datetime | None) -> str:
        if not recorded_at:
            return "Horário não informado"

        if isinstance(recorded_at, datetime):
            return recorded_at.strftime("%d/%m/%Y às %H:%M")

        try:
            parsed_recorded_at = datetime.fromisoformat(recorded_at)
        except (TypeError, ValueError):
            return recorded_at

        return parsed_recorded_at.strftime("%d/%m/%Y às %H:%M")

    def _split_content_type(self, content_type: str) -> tuple[str, str]:
        if "/" not in content_type:
            return ("application", "octet-stream")

        maintype, subtype = content_type.split("/", maxsplit=1)
        return (maintype, subtype)

    def _format_size_bytes(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"

        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"

        return f"{size_bytes / (1024 * 1024):.1f} MB"
