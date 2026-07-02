import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError

from exact_mcp.config import Settings


def valid_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "exact_client_id": "client-id",
        "exact_client_secret": "client-secret",
        "exact_redirect_uri": "https://example.test/oauth/callback",
        "token_encryption_key": Fernet.generate_key().decode(),
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


def test_settings_have_safe_exact_and_transport_defaults() -> None:
    settings = valid_settings()

    assert str(settings.exact_api_base) == "https://start.exactonline.nl/api/v1"
    assert str(settings.exact_authorize_url) == "https://start.exactonline.nl/api/oauth2/auth"
    assert str(settings.exact_token_url) == "https://start.exactonline.nl/api/oauth2/token"
    assert settings.transport == "stdio"
    assert settings.rate_minutely_limit == 60
    assert settings.rate_daily_limit == 5000
    assert settings.rate_reserve == 5


def test_settings_reject_non_https_exact_endpoint() -> None:
    with pytest.raises(ValidationError, match="HTTPS"):
        valid_settings(exact_api_base="http://exact.example/api/v1")


def test_settings_reject_reserve_at_or_above_minutely_limit() -> None:
    with pytest.raises(ValidationError, match="reserve"):
        valid_settings(rate_minutely_limit=5, rate_reserve=5)


def test_settings_validate_fernet_key() -> None:
    with pytest.raises(ValidationError, match="Fernet"):
        valid_settings(token_encryption_key="not-a-key")
