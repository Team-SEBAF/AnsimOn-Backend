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
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS"
    )
    DATABASE_URL: str | None = Field(default=None, alias="DATABASE_URL")
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    AWS_REGION: str | None = Field(default=None, alias="AWS_REGION")
    COGNITO_CLIENT_ID: str | None = Field(default=None, alias="COGNITO_CLIENT_ID")
    COGNITO_USER_POOL_ID: str | None = Field(default=None, alias="COGNITO_USER_POOL_ID")
    COGNITO_CLIENT_SECRET: str | None = Field(default=None, alias="COGNITO_CLIENT_SECRET")


settings = Settings()
