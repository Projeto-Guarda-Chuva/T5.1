from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URL: str
    DATABASE_NAME: str = "t51"
    VIDEO_GRIDFS_BUCKET_NAME: str = "videos"
    VIDEO_SEED_FILE_PATH: str | None = None
    VIDEO_SEED_TARGET_VIDEO_ID: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_STARTTLS: bool = True
    SMTP_TIMEOUT_SECONDS: int = 120
    MAIL_SERVER: str | None = None
    MAIL_PORT: int | None = None
    MAIL_USERNAME: str | None = None
    MAIL_PASSWORD: str | None = None
    MAIL_FROM: str | None = None
    MAIL_STARTTLS: bool | None = None
    FRONTEND_URL: str | None = None

    @property
    def resolved_smtp_host(self) -> str | None:
        if self.SMTP_HOST:
            return self.SMTP_HOST

        if self.MAIL_SERVER:
            return self.MAIL_SERVER

        reference_email = self.resolved_smtp_username or self.resolved_smtp_from_email

        if reference_email and reference_email.lower().endswith("@gmail.com"):
            return "smtp.gmail.com"

        return None

    @property
    def resolved_smtp_port(self) -> int:
        if self.SMTP_HOST:
            return self.SMTP_PORT

        if self.MAIL_PORT is not None:
            return self.MAIL_PORT

        return self.SMTP_PORT

    @property
    def resolved_smtp_username(self) -> str | None:
        return self.SMTP_USERNAME or self.MAIL_USERNAME

    @property
    def resolved_smtp_password(self) -> str | None:
        return self.SMTP_PASSWORD or self.MAIL_PASSWORD

    @property
    def resolved_smtp_from_email(self) -> str | None:
        return self.SMTP_FROM_EMAIL or self.MAIL_FROM

    @property
    def resolved_smtp_use_starttls(self) -> bool:
        if self.MAIL_STARTTLS is not None:
            return self.MAIL_STARTTLS

        return self.SMTP_USE_STARTTLS

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
