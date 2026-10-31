from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_model: str = Field(default="openai/gpt-oss-20b")
    database_url: str
    groq_api_key: SecretStr
    llm_timeout_seconds: float = Field(default=30.0, gt=0)
    database_timeout_seconds: float = Field(default=10.0, gt=0)
    log_level: str = Field(default="INFO")

    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings() # pyright: ignore[reportCallIssue]
