"""Resilient asynchronous Exact Online REST/OData client."""

import logging
import time
from collections.abc import Mapping
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

import httpx

from exact_mcp.endpoints import EndpointSpec
from exact_mcp.errors import ExactAPIError, ValidationFailedError
from exact_mcp.logging import curl_command, redact
from exact_mcp.rate_limit import RateLimiter

logger = logging.getLogger(__name__)


class AccessTokenProvider(Protocol):
    async def access_token(self) -> str: ...


class ExactClient:
    def __init__(
        self,
        api_base: str,
        auth: AccessTokenProvider,
        *,
        http: httpx.AsyncClient,
        limiter: RateLimiter | None = None,
        max_retries: int = 4,
        max_pages: int = 20,
        max_records: int = 1000,
    ) -> None:
        self._api_base = api_base.rstrip("/")
        self._auth = auth
        self._http = http
        self._limiter = limiter or RateLimiter(reserve=5)
        self._max_retries = max_retries
        self._max_pages = max_pages
        self._max_records = max_records
        self._division: int | None = None

    @property
    def division(self) -> int | None:
        return self._division

    def set_division(self, division: int) -> None:
        if division <= 0:
            raise ValidationFailedError("division must be a positive integer")
        self._division = division
        logger.info("exact_division_selected division=%s", division)

    async def current_user(self) -> dict[str, Any]:
        logger.info("exact_current_user_discovery_started")
        result = await self.request("GET", "current/Me", division_scoped=False)
        if not isinstance(result, dict):
            raise ExactAPIError("Exact returned an invalid current-user response")
        division = result.get("CurrentDivision")
        if isinstance(division, int):
            self.set_division(division)
        logger.info(
            "exact_current_user_discovery_completed division=%s division_found=%s",
            self._division,
            isinstance(division, int),
        )
        return result

    async def administrations(self) -> list[dict[str, Any]]:
        if self._division is None:
            await self.current_user()
        return await self.list("system/Divisions")

    async def list(
        self,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        next_path: str | None = path
        next_params = params
        pages = 0
        logger.info(
            "exact_list_started path=%s max_pages=%s max_records=%s",
            redact(path),
            self._max_pages,
            self._max_records,
        )
        while next_path and pages < self._max_pages and len(records) < self._max_records:
            payload = await self.request("GET", next_path, params=next_params)
            next_params = None
            pages += 1
            if isinstance(payload, dict) and isinstance(payload.get("results"), list):
                page = payload["results"]
                next_path = payload.get("__next")
            elif isinstance(payload, list):
                page = payload
                next_path = None
            else:
                raise ExactAPIError("Exact returned an invalid list response")
            records.extend(item for item in page if isinstance(item, dict))
            logger.info(
                "exact_page_received path=%s page=%s records=%s total=%s continuation=%s",
                redact(path),
                pages,
                len(page),
                len(records),
                bool(next_path),
            )
            if next_path:
                self._validate_continuation(next_path)
        result = records[: self._max_records]
        logger.info(
            "exact_list_completed path=%s pages=%s records=%s page_budget_reached=%s "
            "record_budget_reached=%s",
            redact(path),
            pages,
            len(result),
            bool(next_path and pages >= self._max_pages),
            len(records) >= self._max_records,
        )
        return result

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        division_scoped: bool = True,
    ) -> Any:
        division = self._division
        if division_scoped and division is None:
            await self.current_user()
            division = self._division
        if division_scoped and division is None:
            raise ValidationFailedError("no active Exact division is available")
        url = self._url(path, division if division_scoped else None)
        token = await self._auth.access_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if division is not None:
            await self._limiter.before_request(division)

        for attempt in range(self._max_retries + 1):
            attempt_number = attempt + 1
            started = time.perf_counter()
            safe_path = redact(path, sensitive_values=(token,))
            logger.info(
                "exact_request_started method=%s path=%s division=%s attempt=%s",
                method,
                safe_path,
                division,
                attempt_number,
            )
            logger.debug(
                "exact_request_payload method=%s path=%s params=%r body=%r",
                method,
                safe_path,
                redact(params, sensitive_values=(token,)),
                redact(json, sensitive_values=(token,)),
            )
            logger.debug(
                "exact_curl %s",
                curl_command(
                    method,
                    str(httpx.URL(url, params=params)),
                    headers,
                    json_body=json,
                ),
            )
            try:
                response = await self._http.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=headers,
                )
            except httpx.HTTPError as exc:
                duration_ms = (time.perf_counter() - started) * 1000
                logger.warning(
                    "exact_request_network_error method=%s path=%s division=%s attempt=%s "
                    "duration_ms=%.2f error_type=%s retryable=%s",
                    method,
                    safe_path,
                    division,
                    attempt_number,
                    duration_ms,
                    type(exc).__name__,
                    method == "GET" and attempt < self._max_retries,
                )
                if method != "GET" or attempt >= self._max_retries:
                    raise ExactAPIError("Exact API is unavailable", retryable=True) from exc
                delay = self._limiter.retry_delay(attempt, {})
                logger.info(
                    "exact_request_retrying method=%s path=%s division=%s attempt=%s "
                    "status=network_error delay_seconds=%.2f",
                    method,
                    safe_path,
                    division,
                    attempt_number,
                    delay,
                )
                await self._limiter.sleep(delay)
                continue
            duration_ms = (time.perf_counter() - started) * 1000
            if division is not None:
                self._limiter.update(division, response.headers)
            request_id = response.headers.get("X-Request-ID")
            logger.info(
                "exact_response_received method=%s path=%s division=%s attempt=%s status=%s "
                "duration_ms=%.2f request_id=%s minutely_remaining=%s daily_remaining=%s",
                method,
                safe_path,
                division,
                attempt_number,
                response.status_code,
                duration_ms,
                request_id,
                response.headers.get("X-RateLimit-Minutely-Remaining"),
                response.headers.get("X-RateLimit-Remaining"),
            )
            logger.debug(
                "exact_response_payload method=%s path=%s status=%s body=%r",
                method,
                safe_path,
                response.status_code,
                redact(_response_body(response), sensitive_values=(token,)),
            )
            retryable_status = response.status_code == 429 or response.status_code >= 500
            if retryable_status and method == "GET" and attempt < self._max_retries:
                delay = self._limiter.retry_delay(attempt, response.headers)
                logger.info(
                    "exact_request_retrying method=%s path=%s division=%s attempt=%s "
                    "status=%s delay_seconds=%.2f",
                    method,
                    safe_path,
                    division,
                    attempt_number,
                    response.status_code,
                    delay,
                )
                await self._limiter.sleep(delay)
                continue
            if response.status_code >= 400:
                logger.error(
                    "exact_request_failed method=%s path=%s division=%s attempt=%s "
                    "status=%s request_id=%s retryable=%s",
                    method,
                    safe_path,
                    division,
                    attempt_number,
                    response.status_code,
                    request_id,
                    retryable_status,
                )
                raise ExactAPIError(
                    f"Exact API request failed with status {response.status_code}",
                    status_code=response.status_code,
                    request_id=request_id,
                    retryable=retryable_status,
                )
            if response.status_code == 204 or not response.content:
                return None
            try:
                payload = response.json()
            except ValueError as exc:
                logger.error(
                    "exact_response_invalid_json method=%s path=%s division=%s status=%s",
                    method,
                    safe_path,
                    division,
                    response.status_code,
                )
                raise ExactAPIError("Exact returned invalid JSON") from exc
            if isinstance(payload, dict) and "d" in payload:
                return payload["d"]
            return payload
        raise ExactAPIError("Exact API retry budget exhausted", retryable=True)

    async def request_endpoint(
        self,
        method: str,
        endpoint: EndpointSpec,
        *,
        key_suffix: str = "",
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:
        """Call a pre-validated registry endpoint without accepting a caller URL."""
        if method not in endpoint.methods:
            raise ValidationFailedError(f"{method} is not supported for endpoint {endpoint.id}")
        if self._division is None:
            await self.current_user()
        if self._division is None:
            raise ValidationFailedError("no active Exact division is available")
        if key_suffix and not (key_suffix.startswith("(") and key_suffix.endswith(")")):
            raise ValidationFailedError("invalid endpoint key suffix")
        rendered = endpoint.uri_template.replace("{division}", str(self._division)) + key_suffix
        base = urlsplit(self._api_base)
        marker = "/api/v1"
        if not base.path.endswith(marker):
            raise ValidationFailedError("Exact API base must end with /api/v1")
        prefix = base.path[: -len(marker)]
        url = urlunsplit((base.scheme, base.netloc, prefix + rendered, "", ""))
        return await self.request(method, url, params=params, json=json)

    def _url(self, path: str, division: int | None) -> str:
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc:
            self._validate_continuation(path)
            return path
        clean = path.lstrip("/")
        if division is None:
            return f"{self._api_base}/{clean}"
        return f"{self._api_base}/{division}/{clean}"

    def _validate_continuation(self, url: str) -> None:
        expected = urlsplit(self._api_base)
        actual = urlsplit(url)
        if (
            actual.scheme != expected.scheme
            or actual.netloc != expected.netloc
            or not actual.path.startswith(expected.path.rstrip("/") + "/")
        ):
            logger.error("exact_continuation_rejected url=%s", redact(url))
            raise ExactAPIError("Exact continuation URL is outside the configured API origin")
        logger.debug("exact_continuation_accepted url=%s", redact(url))

    async def close(self) -> None:
        logger.info("exact_http_client_close_started")
        await self._http.aclose()
        logger.info("exact_http_client_close_completed")


def _response_body(response: httpx.Response) -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text
