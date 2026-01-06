from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 환경 변수 불러와 설정
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    env: str = Field(default="local", alias="ENV")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS"
    )
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")


settings = Settings()
