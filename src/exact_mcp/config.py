"""Application settings loaded from the environment."""

from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlparse

from cryptography.fernet import Fernet
from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration for one Exact Online identity."""

    model_config = SettingsConfigDict(
        env_prefix="EXACT_MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    exact_client_id: str = Field(min_length=1)
    exact_client_secret: SecretStr
    exact_redirect_uri: AnyHttpUrl
    token_encryption_key: SecretStr
    token_file: Path = Path("tokens.enc")

    exact_api_base: AnyHttpUrl = AnyHttpUrl("https://start.exactonline.nl/api/v1")
    exact_authorize_url: AnyHttpUrl = AnyHttpUrl("https://start.exactonline.nl/api/oauth2/auth")
    exact_token_url: AnyHttpUrl = AnyHttpUrl("https://start.exactonline.nl/api/oauth2/token")

    transport: Literal["stdio", "streamable-http"] = "stdio"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    inbound_bearer_token: SecretStr | None = None

    rate_minutely_limit: int = Field(default=60, ge=1)
    rate_daily_limit: int = Field(default=5000, ge=1)
    rate_reserve: int = Field(default=5, ge=0)
    max_retries: int = Field(default=4, ge=0, le=10)
    max_pages: int = Field(default=20, ge=1, le=100)
    max_records: int = Field(default=1000, ge=1, le=5000)
    request_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    refresh_skew_seconds: int = Field(default=60, ge=0, le=300)

    @field_validator("exact_api_base", "exact_authorize_url", "exact_token_url")
    @classmethod
    def exact_urls_are_https(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.scheme != "https":
            raise ValueError("Exact endpoints must use HTTPS")
        return value

    @field_validator("token_encryption_key")
    @classmethod
    def valid_fernet_key(cls, value: SecretStr) -> SecretStr:
        try:
            Fernet(value.get_secret_value().encode())
        except (TypeError, ValueError) as exc:
            raise ValueError("token_encryption_key must be a valid Fernet key") from exc
        return value

    @field_validator("exact_redirect_uri")
    @classmethod
    def redirect_is_https_or_loopback(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        host = urlparse(str(value)).hostname
        if value.scheme != "https" and host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("redirect URI must use HTTPS unless it is loopback")
        return value

    @model_validator(mode="after")
    def reserve_is_below_limit(self) -> Self:
        if self.rate_reserve >= self.rate_minutely_limit:
            raise ValueError("rate reserve must be below the minutely limit")
        return self

