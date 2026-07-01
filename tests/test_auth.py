import asyncio
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from exact_mcp.auth import OAuthManager
from exact_mcp.errors import AuthenticationRequiredError
from exact_mcp.tokens import MemoryTokenStore, OAuthTokens


def manager(
    handler: httpx.MockTransport,
    store: MemoryTokenStore,
    *,
    now: float = 1000,
) -> OAuthManager:
    return OAuthManager(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="https://example.test/callback",
        authorize_url="https://start.exactonline.nl/api/oauth2/auth",
        token_url="https://start.exactonline.nl/api/oauth2/token",
        store=store,
        http=httpx.AsyncClient(transport=handler),
        clock=lambda: now,
    )


def test_authorization_url_contains_random_state_and_oauth_fields() -> None:
    oauth = manager(httpx.MockTransport(lambda request: httpx.Response(500)), MemoryTokenStore())

    url, state = oauth.authorization_url()
    params = parse_qs(urlparse(url).query)

    assert len(state) >= 32
    assert params["client_id"] == ["client-id"]
    assert params["redirect_uri"] == ["https://example.test/callback"]
    assert params["response_type"] == ["code"]
    assert params["state"] == [state]


@pytest.mark.asyncio
async def test_exchange_code_persists_tokens() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        assert "grant_type=authorization_code" in body
        assert "code=auth-code" in body
        return httpx.Response(
            200,
            json={"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 600},
        )

    store = MemoryTokenStore()
    oauth = manager(httpx.MockTransport(handler), store)

    tokens = await oauth.exchange_code("auth-code")

    assert tokens.access_token == "new-access"
    assert tokens.refresh_token == "new-refresh"
    assert tokens.expires_at == 1600
    assert await store.load() == tokens


@pytest.mark.asyncio
async def test_access_token_reuses_valid_token() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    store = MemoryTokenStore(
        OAuthTokens(
            access_token="still-valid",
            refresh_token="refresh",
            expires_at=1400,
            obtained_at=800,
        )
    )
    oauth = manager(httpx.MockTransport(handler), store)

    assert await oauth.access_token() == "still-valid"
    assert calls == 0


@pytest.mark.asyncio
async def test_concurrent_access_serializes_single_refresh() -> None:
    calls = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        assert b"grant_type=refresh_token" in request.content
        return httpx.Response(
            200,
            json={"access_token": "fresh", "refresh_token": "rotated", "expires_in": 600},
        )

    store = MemoryTokenStore(
        OAuthTokens(
            access_token="old",
            refresh_token="refresh",
            expires_at=1001,
            obtained_at=400,
        )
    )
    oauth = manager(httpx.MockTransport(handler), store)

    results = await asyncio.gather(oauth.access_token(), oauth.access_token())

    assert results == ["fresh", "fresh"]
    assert calls == 1
    assert (await store.load()).refresh_token == "rotated"  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_missing_tokens_raise_actionable_error() -> None:
    oauth = manager(httpx.MockTransport(lambda request: httpx.Response(500)), MemoryTokenStore())

    with pytest.raises(AuthenticationRequiredError, match="authorization"):
        await oauth.access_token()


@pytest.mark.asyncio
async def test_token_endpoint_error_does_not_expose_response_or_secret() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="client-secret refresh-secret")

    store = MemoryTokenStore(
        OAuthTokens(
            access_token="old",
            refresh_token="refresh-secret",
            expires_at=1001,
            obtained_at=400,
        )
    )
    oauth = manager(httpx.MockTransport(handler), store)

    with pytest.raises(AuthenticationRequiredError) as captured:
        await oauth.access_token()

    assert "client-secret" not in str(captured.value)
    assert "refresh-secret" not in str(captured.value)

