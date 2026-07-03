import asyncio
import time
from pathlib import Path

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from typer.testing import CliRunner

from exact_mcp.cli import app
from exact_mcp.tokens import EncryptedFileTokenStore, OAuthTokens


def configure_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path | None = None) -> bytes:
    encryption_key = Fernet.generate_key()
    values = {
        "EXACT_MCP_EXACT_CLIENT_ID": "client-id",
        "EXACT_MCP_EXACT_CLIENT_SECRET": "client-secret",
        "EXACT_MCP_EXACT_REDIRECT_URI": "http://127.0.0.1:8765/oauth/callback",
        "EXACT_MCP_TOKEN_ENCRYPTION_KEY": encryption_key.decode(),
    }
    if tmp_path is not None:
        values["EXACT_MCP_TOKEN_FILE"] = str(tmp_path / "tokens.enc")
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return encryption_key


def test_auth_url_prints_exact_authorization_url(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_environment(monkeypatch)

    result = CliRunner().invoke(app, ["auth-url"])

    assert result.exit_code == 0
    assert "https://start.exactonline.nl/api/oauth2/auth?" in result.stdout
    assert "client_id=client-id" in result.stdout
    assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A8765%2Foauth%2Fcallback" in result.stdout
    assert "State:" in result.stdout


def test_auth_status_reports_when_authorization_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    configure_environment(monkeypatch, tmp_path)

    result = CliRunner().invoke(app, ["auth-status"])

    assert result.exit_code == 1
    assert "not authorized" in result.stdout.lower()


def test_auth_status_reports_time_until_expiry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    encryption_key = configure_environment(monkeypatch, tmp_path)
    save_tokens(
        tmp_path / "tokens.enc",
        encryption_key,
        OAuthTokens(
            access_token="access",
            refresh_token="refresh",
            expires_at=1492,
            obtained_at=400,
        ),
    )
    monkeypatch.setattr("exact_mcp.cli.time.time", lambda: 1000)

    result = CliRunner().invoke(app, ["auth-status"])

    assert result.exit_code == 0
    assert "expires in 8m 12s" in result.stdout
    assert "1492" not in result.stdout


def test_auth_status_reports_time_since_expiry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    encryption_key = configure_environment(monkeypatch, tmp_path)
    save_tokens(
        tmp_path / "tokens.enc",
        encryption_key,
        OAuthTokens(
            access_token="access",
            refresh_token="refresh",
            expires_at=955,
            obtained_at=400,
        ),
    )
    monkeypatch.setattr("exact_mcp.cli.time.time", lambda: 1000)

    result = CliRunner().invoke(app, ["auth-status"])

    assert result.exit_code == 0
    assert "expired 45s ago" in result.stdout
    assert "955" not in result.stdout


@respx.mock
def test_exchange_code_encrypts_returned_tokens(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    encryption_key = configure_environment(monkeypatch, tmp_path)
    respx.post("https://start.exactonline.nl/api/oauth2/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "access-secret",
                "refresh_token": "refresh-secret",
                "expires_in": 600,
            },
        )
    )

    result = CliRunner().invoke(app, ["exchange-code", "authorization-code"])

    assert result.exit_code == 0
    assert "authorized" in result.stdout.lower()
    token_contents = (tmp_path / "tokens.enc").read_bytes()
    assert b"access-secret" not in token_contents
    assert b"refresh-secret" not in token_contents
    stored = asyncio.run(EncryptedFileTokenStore(tmp_path / "tokens.enc", encryption_key).load())
    assert stored is not None
    assert stored.refresh_token == "refresh-secret"


@respx.mock
def test_auth_accepts_callback_and_persists_refresh_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    encryption_key = configure_environment(monkeypatch, tmp_path)

    def exchange(request: httpx.Request) -> httpx.Response:
        assert b"code=abc%2Bdef" in request.content
        return httpx.Response(
            200,
            json={
                "access_token": "access-secret",
                "refresh_token": "refresh-secret",
                "expires_in": 600,
            },
        )

    respx.post("https://start.exactonline.nl/api/oauth2/token").mock(side_effect=exchange)

    result = CliRunner().invoke(
        app,
        ["auth"],
        input="http://127.0.0.1:8765/oauth/callback?code=abc%26%2343%3Bdef&state=csrf\n",
    )

    assert result.exit_code == 0
    assert "https://start.exactonline.nl/api/oauth2/auth?" in result.stdout
    assert "authorized" in result.stdout.lower()
    assert "abc" not in result.stdout
    stored = asyncio.run(EncryptedFileTokenStore(tmp_path / "tokens.enc", encryption_key).load())
    assert stored is not None
    assert stored.refresh_token == "refresh-secret"


@respx.mock
def test_auth_rejects_callback_without_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    configure_environment(monkeypatch, tmp_path)
    route = respx.post("https://start.exactonline.nl/api/oauth2/token").mock(
        return_value=httpx.Response(500)
    )

    result = CliRunner().invoke(
        app,
        ["auth"],
        input="http://127.0.0.1:8765/oauth/callback?state=csrf\n",
    )

    assert result.exit_code == 1
    assert "callback URL" in result.stdout
    assert route.call_count == 0


def save_tokens(path: Path, key: bytes, tokens: OAuthTokens) -> None:
    asyncio.run(EncryptedFileTokenStore(path, key).save(tokens))


def test_auth_refresh_reports_token_under_minimum_age(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    encryption_key = configure_environment(monkeypatch, tmp_path)
    now = time.time()
    save_tokens(
        tmp_path / "tokens.enc",
        encryption_key,
        OAuthTokens(
            access_token="access",
            refresh_token="refresh",
            expires_at=now + 30,
            obtained_at=now - 500,
        ),
    )

    result = CliRunner().invoke(app, ["auth-refresh"])

    assert result.exit_code == 0
    assert "younger than 570 seconds" in result.stdout
    assert "wait" in result.stdout.lower()


@respx.mock
def test_auth_refresh_reports_when_access_token_is_not_near_expiry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    encryption_key = configure_environment(monkeypatch, tmp_path)
    now = time.time()
    save_tokens(
        tmp_path / "tokens.enc",
        encryption_key,
        OAuthTokens(
            access_token="access",
            refresh_token="refresh",
            expires_at=now + 300,
            obtained_at=now - 600,
        ),
    )
    route = respx.post("https://start.exactonline.nl/api/oauth2/token").mock(
        return_value=httpx.Response(500)
    )

    result = CliRunner().invoke(app, ["auth-refresh"])

    assert result.exit_code == 0
    assert "not near expiry" in result.stdout
    assert route.call_count == 0


@respx.mock
def test_auth_refresh_rotates_persisted_refresh_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    encryption_key = configure_environment(monkeypatch, tmp_path)
    now = time.time()
    save_tokens(
        tmp_path / "tokens.enc",
        encryption_key,
        OAuthTokens(
            access_token="old-access",
            refresh_token="old-refresh",
            expires_at=now + 30,
            obtained_at=now - 600,
        ),
    )
    respx.post("https://start.exactonline.nl/api/oauth2/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 600,
            },
        )
    )

    result = CliRunner().invoke(app, ["auth-refresh"])

    assert result.exit_code == 0
    assert "refreshed" in result.stdout.lower()
    stored = asyncio.run(EncryptedFileTokenStore(tmp_path / "tokens.enc", encryption_key).load())
    assert stored is not None
    assert stored.refresh_token == "new-refresh"


def test_cli_help_lists_oauth_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "auth" in result.stdout
    assert "auth-url" in result.stdout
    assert "auth-refresh" in result.stdout
    assert "exchange-code" in result.stdout
    assert "auth-status" in result.stdout
    assert "serve" in result.stdout


def test_serve_runs_fastmcp_with_selected_transport(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    configure_environment(monkeypatch, tmp_path)
    calls: list[str] = []

    class Server:
        def run(self, transport: str) -> None:
            calls.append(f"run:{transport}")

    def configure(settings: object) -> None:
        del settings
        calls.append("logging")

    def build(settings: object) -> Server:
        del settings
        calls.append("build")
        return Server()

    monkeypatch.setattr("exact_mcp.cli.configure_logging", configure)
    monkeypatch.setattr("exact_mcp.cli.build_server", build)

    result = CliRunner().invoke(app, ["serve", "--transport", "stdio"])

    assert result.exit_code == 0
    assert calls == ["logging", "build", "run:stdio"]
