import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env" if os.getenv("ENV", "local") == "local" else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    env: str = Field(default="local", alias="ENV")
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS"
    )

    DATABASE_URL: str | None = None
    LOG_LEVEL: str = "INFO"

    AWS_REGION: str
    AWS_PROFILE: str | None = None
    COGNITO_CLIENT_ID: str
    COGNITO_USER_POOL_ID: str
    COGNITO_CLIENT_SECRET: str


settings = Settings()
