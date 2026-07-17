"""Exact Online OAuth authorization-code and refresh lifecycle."""

import asyncio
import html
import logging
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx

from exact_mcp.errors import AuthenticationRequiredError
from exact_mcp.logging import curl_command
from exact_mcp.tokens import OAuthTokens, TokenStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RefreshResult:
    """Non-secret outcome of a conditional refresh attempt."""

    status: Literal["refreshed", "too_young", "not_due"]
    tokens: OAuthTokens = field(repr=False)
    age_seconds: float


def authorization_code_from_callback(callback_url: str) -> str:
    """Extract and decode one authorization code from an absolute callback URL."""
    parsed = urlsplit(callback_url.strip())
    codes = parse_qs(parsed.query, keep_blank_values=True).get("code", [])
    if not parsed.scheme or not parsed.netloc or len(codes) != 1 or not codes[0].strip():
        raise AuthenticationRequiredError(
            "the OAuth callback URL must contain exactly one authorization code"
        )
    return html.unescape(codes[0])


class OAuthManager:
    """Own Exact credentials and serialize rotation of short-lived tokens."""

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorize_url: str,
        token_url: str,
        store: TokenStore,
        http: httpx.AsyncClient,
        clock: Callable[[], float] = time.time,
        refresh_skew_seconds: int = 60,
        minimum_refresh_age_seconds: int = 570,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._authorize_url = authorize_url
        self._token_url = token_url
        self._store = store
        self._http = http
        self._clock = clock
        self._refresh_skew = refresh_skew_seconds
        self._minimum_refresh_age = minimum_refresh_age_seconds
        self._refresh_token_lifetime = 30 * 24 * 60 * 60
        self._refresh_lock = asyncio.Lock()

    def authorization_url(self) -> tuple[str, str]:
        state = secrets.token_urlsafe(32)
        query = urlencode(
            {
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "response_type": "code",
                "state": state,
            }
        )
        return f"{self._authorize_url}?{query}", state

    async def exchange_code(self, code: str) -> OAuthTokens:
        if not code.strip():
            raise AuthenticationRequiredError("an OAuth authorization code is required")
        return await self._token_request(
            {
                "code": code,
                "redirect_uri": self._redirect_uri,
                "grant_type": "authorization_code",
            }
        )

    async def refresh_if_due(self) -> RefreshResult:
        """Refresh stored tokens only when Exact permits it and access expiry is near."""
        tokens = await self._store.load()
        if tokens is None:
            raise AuthenticationRequiredError(
                "Exact Online authorization is required; run the auth command"
            )

        async with self._refresh_lock:
            tokens = await self._store.load()
            if tokens is None:
                raise AuthenticationRequiredError(
                    "Exact Online authorization is required; run the auth command"
                )
            age = max(0.0, self._clock() - tokens.obtained_at)
            if age < self._minimum_refresh_age:
                return RefreshResult(status="too_young", tokens=tokens, age_seconds=age)
            if not self._refresh_due(tokens):
                return RefreshResult(status="not_due", tokens=tokens, age_seconds=age)
            refresh_token_obtained_at = (
                tokens.refresh_token_obtained_at
                if tokens.refresh_token_obtained_at is not None
                else tokens.obtained_at
            )
            if self._clock() - refresh_token_obtained_at >= self._refresh_token_lifetime:
                raise AuthenticationRequiredError(
                    "the Exact refresh token is at least 30 days old; run the auth command"
                )
            refreshed = await self._token_request(
                {"refresh_token": tokens.refresh_token, "grant_type": "refresh_token"},
                previous_refresh_token=tokens.refresh_token,
                previous_refresh_token_obtained_at=refresh_token_obtained_at,
            )
            return RefreshResult(status="refreshed", tokens=refreshed, age_seconds=age)

    async def access_token(self) -> str:
        tokens = await self._store.load()
        if tokens is None:
            raise AuthenticationRequiredError(
                "Exact Online authorization is required; "
                "run the auth-url and exchange-code commands"
            )
        if not self._refresh_due(tokens):
            return tokens.access_token

        async with self._refresh_lock:
            tokens = await self._store.load()
            if tokens is None:
                raise AuthenticationRequiredError("Exact Online authorization is required")
            if not self._refresh_due(tokens):
                return tokens.access_token
            age = self._clock() - tokens.obtained_at
            if age < self._minimum_refresh_age:
                if self._clock() < tokens.expires_at:
                    return tokens.access_token
                raise AuthenticationRequiredError(
                    "Exact access token expired before refresh became eligible",
                    retryable=True,
                )
            refreshed = await self._token_request(
                {"refresh_token": tokens.refresh_token, "grant_type": "refresh_token"},
                previous_refresh_token=tokens.refresh_token,
                previous_refresh_token_obtained_at=(
                    tokens.refresh_token_obtained_at
                    if tokens.refresh_token_obtained_at is not None
                    else tokens.obtained_at
                ),
            )
            return refreshed.access_token

    def _refresh_due(self, tokens: OAuthTokens) -> bool:
        return self._clock() >= tokens.expires_at - self._refresh_skew

    async def _token_request(
        self,
        grant: dict[str, str],
        *,
        previous_refresh_token: str | None = None,
        previous_refresh_token_obtained_at: float | None = None,
    ) -> OAuthTokens:
        data = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            **grant,
        }
        try:
            logger.debug(
                "exact_curl %s",
                curl_command(
                    "POST",
                    self._token_url,
                    {"Accept": "application/json"},
                    form_body=data,
                ),
            )
            response = await self._http.post(self._token_url, data=data)
        except httpx.HTTPError as exc:
            raise AuthenticationRequiredError(
                "Exact OAuth endpoint is unavailable",
                retryable=True,
            ) from exc
        if response.status_code >= 400:
            raise AuthenticationRequiredError(
                f"Exact OAuth request failed with status {response.status_code}",
                retryable=response.status_code >= 500 or response.status_code == 429,
            )
        try:
            payload: dict[str, Any] = response.json()
            now = self._clock()
            access_token = str(payload["access_token"])
            rotated_refresh_token = payload.get("refresh_token")
            refresh_token = str(rotated_refresh_token or previous_refresh_token or "")
            refresh_token_obtained_at = (
                now if rotated_refresh_token else previous_refresh_token_obtained_at or now
            )
            expires_in = float(payload.get("expires_in", 600))
            tokens = OAuthTokens(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=now + expires_in,
                obtained_at=now,
                refresh_token_obtained_at=refresh_token_obtained_at,
                token_type=str(payload.get("token_type", "Bearer")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthenticationRequiredError(
                "Exact OAuth returned an invalid token response"
            ) from exc
        await self._store.save(tokens)
        return tokens
