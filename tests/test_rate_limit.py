import pytest

from exact_mcp.rate_limit import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_waits_at_reserve_until_reset() -> None:
    waits: list[float] = []

    async def sleep(seconds: float) -> None:
        waits.append(seconds)

    limiter = RateLimiter(reserve=5, clock=lambda: 100.0, sleeper=sleep)
    limiter.update(
        123,
        {
            "X-RateLimit-Minutely-Remaining": "5",
            "X-RateLimit-Remaining": "4990",
            "X-RateLimit-Reset": "110",
        },
    )

    await limiter.before_request(123)

    assert waits == [10.0]


def test_retry_delay_honors_retry_after_and_caps_backoff() -> None:
    limiter = RateLimiter(reserve=5, random_source=lambda: 0.0, max_backoff=8.0)

    assert limiter.retry_delay(0, {"Retry-After": "3"}) == 3.0
    assert limiter.retry_delay(10, {}) == 8.0
