import os

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

load_dotenv()


def _get_mailer() -> FastMail:
    conf = ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
        MAIL_FROM=os.getenv("MAIL_FROM", ""),
        MAIL_PORT=587,
        MAIL_SERVER="smtp.gmail.com",
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
    )
    return FastMail(conf)


async def send_password_reset_email(to_email: str, code: str) -> None:
    message = MessageSchema(
        subject="Recuperação de senha — T5.1",
        recipients=[to_email],
        body=(
            f"Olá!\n\n"
            f"Recebemos uma solicitação para redefinir sua senha.\n\n"
            f"Use o código abaixo para cadastrar uma nova senha:\n\n"
            f"    {code}\n\n"
            f"Este código expira em 15 minutos.\n\n"
            f"Se você não solicitou a recuperação, ignore este e-mail."
        ),
        subtype=MessageType.plain,
    )
    await _get_mailer().send_message(message)
