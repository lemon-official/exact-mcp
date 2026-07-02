from pathlib import Path

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from typer.testing import CliRunner

from exact_mcp.cli import app


def configure_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path | None = None) -> None:
    values = {
        "EXACT_MCP_EXACT_CLIENT_ID": "client-id",
        "EXACT_MCP_EXACT_CLIENT_SECRET": "client-secret",
        "EXACT_MCP_EXACT_REDIRECT_URI": "http://127.0.0.1:8765/oauth/callback",
        "EXACT_MCP_TOKEN_ENCRYPTION_KEY": Fernet.generate_key().decode(),
    }
    if tmp_path is not None:
        values["EXACT_MCP_TOKEN_FILE"] = str(tmp_path / "tokens.enc")
    for name, value in values.items():
        monkeypatch.setenv(name, value)


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


@respx.mock
def test_exchange_code_encrypts_returned_tokens(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    configure_environment(monkeypatch, tmp_path)
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


def test_cli_help_lists_oauth_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "auth-url" in result.stdout
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
