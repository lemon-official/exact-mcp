import logging
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from exact_mcp.config import Settings
from exact_mcp.logging import configure_logging, redact


def logging_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "exact_client_id": "client-id",
        "exact_client_secret": "client-secret",
        "exact_redirect_uri": "https://example.test/oauth/callback",
        "token_encryption_key": Fernet.generate_key().decode(),
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


def test_redact_masks_nested_credentials_and_bearer_tokens() -> None:
    value = {
        "Authorization": "Bearer header-secret",
        "nested": [
            {"access_token": "access-secret", "safe": "visible"},
            "prefix Bearer inline-secret suffix",
        ],
        "client_secret": "client-secret",
        "code": "authorization-code",
        "state": "csrf-state",
    }

    sanitized = redact(value)

    rendered = repr(sanitized)
    assert "header-secret" not in rendered
    assert "access-secret" not in rendered
    assert "inline-secret" not in rendered
    assert "client-secret" not in rendered
    assert "authorization-code" not in rendered
    assert "csrf-state" not in rendered
    assert sanitized["nested"][0]["safe"] == "visible"
    assert rendered.count("<redacted>") >= 5


def test_configure_logging_writes_stderr_and_optional_file(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    log_file = tmp_path / "logs" / "exact-mcp.log"
    settings = logging_settings(log_level="DEBUG", log_file=log_file)

    configure_logging(settings)
    logging.getLogger("exact_mcp.test").info("runtime event")
    for handler in logging.getLogger().handlers:
        handler.flush()

    captured = capsys.readouterr()
    assert "runtime event" in captured.err
    assert captured.out == ""
    assert "runtime event" in log_file.read_text()
