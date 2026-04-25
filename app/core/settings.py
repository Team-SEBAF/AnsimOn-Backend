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
    WEB_APP_URL: str | None = None
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS"
    )

    DATABASE_URL: str | None = None
    LOG_LEVEL: str = "INFO"

    AWS_REGION: str
    AWS_PROFILE: str | None = None
    COGNITO_CLIENT_ID: str | None = None
    COGNITO_USER_POOL_ID: str | None = None
    COGNITO_CLIENT_SECRET: str | None = None
    COGNITO_DOMAIN: str | None = None
    S3_BUCKET_NAME: str | None = None
    SQS_QUEUE_URL: str | None = None

    ECS_CLUSTER: str | None = None
    SSE_ECS_SERVICE: str | None = None
    SSE_SERVER_PORT: int = 8000
    AI_WORKER_ECS_SERVICE: str | None = None
    AI_WORKER_AUTOSCALING_MAX_CAPACITY: int = 5
    AI_WORKER_WARM_MIN_TASKS: int = 2

    SSE_RECORD_NAME: str | None = None
    ANSIMON_ZONE_NAME: str | None = None


settings = Settings()
