import logging
from collections.abc import Iterator

import httpx
import pytest

from exact_mcp.client import ExactClient
from exact_mcp.endpoints import EndpointSpec
from exact_mcp.errors import ExactAPIError
from exact_mcp.rate_limit import RateLimiter


class Auth:
    async def access_token(self) -> str:
        return "access-secret"


def responses(*items: httpx.Response) -> httpx.MockTransport:
    iterator: Iterator[httpx.Response] = iter(items)

    async def handler(request: httpx.Request) -> httpx.Response:
        response = next(iterator)
        response.request = request
        return response

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_current_user_discovers_and_sets_division() -> None:
    transport = responses(
        httpx.Response(200, json={"d": {"CurrentDivision": 123, "FullName": "User"}})
    )
    http = httpx.AsyncClient(transport=transport)
    client = ExactClient("https://start.exactonline.nl/api/v1", Auth(), http=http)

    user = await client.current_user()

    assert user["CurrentDivision"] == 123
    assert client.division == 123
    assert http.headers.get("Authorization") is None


@pytest.mark.asyncio
async def test_division_scoped_request_injects_bearer() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"d": {"results": []}})

    client = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    client.set_division(123)

    await client.list("crm/Accounts", params={"$top": "20"})

    assert seen[0].url.path == "/api/v1/123/crm/Accounts"
    assert seen[0].headers["Authorization"] == "Bearer access-secret"


@pytest.mark.asyncio
async def test_client_debug_logs_full_curl_command(caplog: pytest.LogCaptureFixture) -> None:
    client = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(
            transport=responses(httpx.Response(200, json={"d": {"results": []}}))
        ),
    )
    client.set_division(123)
    caplog.set_level(logging.DEBUG, logger="exact_mcp.client")

    await client.request(
        "POST",
        "crm/Accounts",
        params={"$filter": "Name eq 'Ada'"},
        json={"Name": "Ada Lovelace"},
    )

    assert "exact_curl curl -X POST" in caplog.text
    assert "Authorization: Bearer access-secret" in caplog.text
    assert "%24filter=Name+eq+%27Ada%27" in caplog.text
    assert '{"Name":"Ada Lovelace"}' in caplog.text


@pytest.mark.asyncio
async def test_registered_request_renders_normal_and_beta_templates() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"d": {"results": []}})

    client = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    client.set_division(123)
    normal = EndpointSpec(
        id="crm/addresses",
        service="CRM",
        resource="Addresses",
        uri_template="/api/v1/{division}/crm/Addresses",
        methods=("GET",),
    )
    beta = EndpointSpec(
        id="budget/budgetscenarios",
        service="Budget",
        resource="BudgetScenarios",
        uri_template="/api/v1/beta/{division}/budget/BudgetScenarios",
        methods=("GET",),
    )

    await client.request_endpoint("GET", normal, key_suffix="(guid'abc')")
    await client.request_endpoint("GET", beta)

    assert seen[0].url.path == "/api/v1/123/crm/Addresses(guid'abc')"
    assert seen[1].url.path == "/api/v1/beta/123/budget/BudgetScenarios"


@pytest.mark.asyncio
async def test_list_follows_exact_continuation_with_record_budget(
    caplog: pytest.LogCaptureFixture,
) -> None:
    first = httpx.Response(
        200,
        json={
            "d": {
                "results": [{"ID": "1"}],
                "__next": "https://start.exactonline.nl/api/v1/123/crm/Accounts?$skiptoken=abc",
            }
        },
    )
    second = httpx.Response(200, json={"d": {"results": [{"ID": "2"}]}})
    client = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(transport=responses(first, second)),
        max_pages=2,
        max_records=2,
    )
    client.set_division(123)
    caplog.set_level(logging.DEBUG, logger="exact_mcp.client")

    assert await client.list("crm/Accounts") == [{"ID": "1"}, {"ID": "2"}]
    output = caplog.text
    assert "exact_request_started method=GET path=crm/Accounts division=123 attempt=1" in output
    assert (
        "exact_response_received method=GET path=crm/Accounts division=123 attempt=1 status=200"
        in output
    )
    assert (
        "exact_page_received path=crm/Accounts page=1 records=1 total=1 continuation=True" in output
    )
    assert "exact_page_received" in output
    assert "page=2 records=1 total=2 continuation=False" in output
    assert "exact_list_completed path=crm/Accounts pages=2 records=2" in output
    assert "exact_curl" in output
    assert "access-secret" not in "\n".join(
        line for line in output.splitlines() if "exact_curl" not in line
    )


@pytest.mark.asyncio
async def test_list_rejects_continuation_to_another_origin() -> None:
    response = httpx.Response(
        200,
        json={"d": {"results": [], "__next": "https://evil.example/steal"}},
    )
    client = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(transport=responses(response)),
    )
    client.set_division(123)

    with pytest.raises(ExactAPIError, match="continuation"):
        await client.list("crm/Accounts")


@pytest.mark.asyncio
async def test_client_retries_429_but_not_ordinary_400() -> None:
    waits: list[float] = []

    async def sleep(seconds: float) -> None:
        waits.append(seconds)

    limiter = RateLimiter(reserve=5, sleeper=sleep, random_source=lambda: 0.0)
    client = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(
            transport=responses(
                httpx.Response(429, headers={"Retry-After": "1"}),
                httpx.Response(200, json={"d": {"results": []}}),
            )
        ),
        limiter=limiter,
    )
    client.set_division(123)

    assert await client.list("crm/Accounts") == []
    assert waits == [1.0]

    bad = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(transport=responses(httpx.Response(400, text="access-secret"))),
    )
    bad.set_division(123)
    with pytest.raises(ExactAPIError) as captured:
        await bad.list("crm/Accounts")
    assert "access-secret" not in str(captured.value)


@pytest.mark.asyncio
async def test_client_logs_retry_and_terminal_exact_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def sleep(seconds: float) -> None:
        del seconds

    caplog.set_level(logging.DEBUG, logger="exact_mcp.client")
    retrying = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(
            transport=responses(
                httpx.Response(503, text="temporary"),
                httpx.Response(200, json={"d": {"results": []}}),
            )
        ),
        limiter=RateLimiter(reserve=5, sleeper=sleep, random_source=lambda: 0.0),
    )
    retrying.set_division(123)

    await retrying.list("crm/Accounts", params={"$filter": "Name eq 'Acme'"})

    assert (
        "exact_request_retrying method=GET path=crm/Accounts division=123 attempt=1" in caplog.text
    )
    assert "status=503" in caplog.text
    assert "delay_seconds=0.50" in caplog.text

    failing = ExactClient(
        "https://start.exactonline.nl/api/v1",
        Auth(),
        http=httpx.AsyncClient(
            transport=responses(
                httpx.Response(
                    403,
                    headers={"X-Request-ID": "request-403"},
                    text="access-secret",
                )
            )
        ),
    )
    failing.set_division(123)
    with pytest.raises(ExactAPIError):
        await failing.list("crm/Accounts")

    assert "exact_request_failed method=GET path=crm/Accounts division=123" in caplog.text
    assert "status=403" in caplog.text
    assert "request_id=request-403" in caplog.text
    assert "access-secret" not in "\n".join(
        line for line in caplog.text.splitlines() if "exact_curl" not in line
    )
