"""Command-line interface for Exact Online authorization and server startup."""

import asyncio
import html
import logging
import math
import time
from typing import NoReturn

import httpx
import typer
from pydantic import ValidationError

from exact_mcp.auth import OAuthManager, RefreshResult, authorization_code_from_callback
from exact_mcp.config import Settings
from exact_mcp.errors import ExactMCPError
from exact_mcp.logging import configure_logging
from exact_mcp.server import build_server
from exact_mcp.tokens import EncryptedFileTokenStore, OAuthTokens

app = typer.Typer(
    name="exact-mcp",
    help="Authorize and run the Exact Online MCP server.",
    no_args_is_help=True,
)
logger = logging.getLogger(__name__)


def _configuration_error(error: Exception) -> NoReturn:
    typer.echo(f"Configuration error: {error}", err=True)
    raise typer.Exit(2)


def _settings() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except (ValidationError, ValueError) as exc:
        _configuration_error(exc)


def _store(settings: Settings) -> EncryptedFileTokenStore:
    key = settings.token_encryption_key.get_secret_value().encode()
    return EncryptedFileTokenStore(settings.token_file, key)


def _manager(
    settings: Settings,
    http: httpx.AsyncClient,
    store: EncryptedFileTokenStore,
) -> OAuthManager:
    return OAuthManager(
        client_id=settings.exact_client_id,
        client_secret=settings.exact_client_secret.get_secret_value(),
        redirect_uri=str(settings.exact_redirect_uri),
        authorize_url=str(settings.exact_authorize_url),
        token_url=str(settings.exact_token_url),
        store=store,
        http=http,
        refresh_skew_seconds=settings.refresh_skew_seconds,
    )


async def _authorization_url(settings: Settings) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as http:
        return _manager(settings, http, _store(settings)).authorization_url()


async def _exchange_authorization_code(settings: Settings, code: str) -> OAuthTokens:
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as http:
        return await _manager(settings, http, _store(settings)).exchange_code(code)


async def _refresh_authorization(settings: Settings) -> RefreshResult:
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as http:
        return await _manager(settings, http, _store(settings)).refresh_if_due()


def _authorization_failure(error: ExactMCPError) -> NoReturn:
    typer.echo(f"Authorization failed: {error.message}", err=True)
    raise typer.Exit(1) from error


def _format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    if minutes:
        return f"{minutes}m {remaining_seconds}s"
    return f"{remaining_seconds}s"


@app.command("auth-url")
def auth_url() -> None:
    """Print the Exact Online authorization URL and CSRF state value."""
    settings = _settings()

    url, state = asyncio.run(_authorization_url(settings))
    typer.echo(url)
    typer.echo(f"State: {state}")
    typer.echo(
        "After approval, copy the code query parameter from the redirect URL "
        "and run: exact-mcp exchange-code CODE"
    )


@app.command("auth")
def auth() -> None:
    """Authorize Exact Online from a pasted OAuth callback URL."""
    settings = _settings()
    url, state = asyncio.run(_authorization_url(settings))
    typer.echo(url)
    typer.echo(f"State: {state}")
    callback_url = typer.prompt("Paste the complete callback URL", hide_input=True)
    try:
        code = authorization_code_from_callback(callback_url)
        asyncio.run(_exchange_authorization_code(settings, code))
    except ExactMCPError as exc:
        _authorization_failure(exc)
    typer.echo(f"Exact Online authorized; encrypted tokens saved to {settings.token_file}")


@app.command("exchange-code")
def exchange_code(code: str = typer.Argument(..., help="Code returned by Exact Online")) -> None:
    """Exchange an Exact authorization code and encrypt the resulting tokens."""
    settings = _settings()

    try:
        asyncio.run(_exchange_authorization_code(settings, html.unescape(code).strip()))
    except ExactMCPError as exc:
        _authorization_failure(exc)
    typer.echo(f"Exact Online authorized; encrypted tokens saved to {settings.token_file}")


@app.command("auth-refresh")
def auth_refresh() -> None:
    """Refresh encrypted Exact credentials when the access token is near expiry."""
    settings = _settings()
    try:
        result = asyncio.run(_refresh_authorization(settings))
    except ExactMCPError as exc:
        _authorization_failure(exc)

    if result.status == "too_young":
        wait_seconds = math.ceil(570 - result.age_seconds)
        typer.echo(
            "Token is younger than 570 seconds "
            f"({_format_duration(result.age_seconds)} old); "
            f"wait {_format_duration(wait_seconds)}."
        )
        return
    if result.status == "not_due":
        remaining = result.tokens.expires_at - time.time()
        typer.echo(f"Access token is not near expiry; it expires in {_format_duration(remaining)}.")
        return
    typer.echo(
        f"Exact Online authorization refreshed; encrypted tokens saved to {settings.token_file}"
    )


@app.command("auth-status")
def auth_status() -> None:
    """Report whether encrypted Exact Online tokens are available."""
    settings = _settings()
    try:
        tokens = asyncio.run(_store(settings).load())
    except ValueError as exc:
        typer.echo(f"Token file error: {exc}", err=True)
        raise typer.Exit(1) from exc
    if tokens is None:
        typer.echo("Exact Online is not authorized.")
        raise typer.Exit(1)
    remaining = tokens.expires_at - time.time()
    if remaining >= 0:
        typer.echo(
            f"Exact Online is authorized; access token expires in {_format_duration(remaining)}."
        )
    else:
        typer.echo(
            f"Exact Online is authorized; access token expired {_format_duration(-remaining)} ago."
        )


@app.command("serve")
def serve(
    transport: str | None = typer.Option(
        None,
        "--transport",
        help="MCP transport: stdio or streamable-http",
    ),
) -> None:
    """Run the Exact Online MCP server."""
    settings = _settings()
    selected = transport or settings.transport
    if selected not in {"stdio", "streamable-http"}:
        typer.echo("Transport must be stdio or streamable-http.", err=True)
        raise typer.Exit(2)
    configure_logging(settings)
    logger.info(
        "mcp_server_starting transport=%s host=%s port=%s api_origin=%s log_level=%s",
        selected,
        settings.host,
        settings.port,
        settings.exact_api_base,
        settings.log_level,
    )
    server = build_server(settings)
    try:
        server.run(transport=selected)  # type: ignore[arg-type]
    finally:
        logger.info("mcp_server_stopped transport=%s", selected)


if __name__ == "__main__":
    app()
