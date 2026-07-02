"""Per-division Exact Online rate-limit coordination."""

import asyncio
import random
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass


@dataclass
class RateState:
    minutely_remaining: int | None = None
    daily_remaining: int | None = None
    reset_at: float | None = None


class RateLimiter:
    def __init__(
        self,
        *,
        reserve: int,
        clock: Callable[[], float] = time.time,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
        random_source: Callable[[], float] = random.random,
        base_backoff: float = 0.5,
        max_backoff: float = 30.0,
    ) -> None:
        self._reserve = reserve
        self._clock = clock
        self._sleep = sleeper
        self._random = random_source
        self._base_backoff = base_backoff
        self._max_backoff = max_backoff
        self._states: dict[int, RateState] = {}

    def update(self, division: int, headers: Mapping[str, str]) -> None:
        values = {key.lower(): value for key, value in headers.items()}
        state = self._states.setdefault(division, RateState())
        state.minutely_remaining = _integer(values.get("x-ratelimit-minutely-remaining"))
        state.daily_remaining = _integer(values.get("x-ratelimit-remaining"))
        state.reset_at = _number(values.get("x-ratelimit-reset"))

    async def before_request(self, division: int) -> None:
        state = self._states.get(division)
        if state is None or state.minutely_remaining is None:
            return
        if state.minutely_remaining > self._reserve or state.reset_at is None:
            return
        delay = max(0.0, state.reset_at - self._clock())
        if delay:
            await self._sleep(delay)
        state.minutely_remaining = None

    def retry_delay(self, attempt: int, headers: Mapping[str, str]) -> float:
        values = {key.lower(): value for key, value in headers.items()}
        retry_after = _number(values.get("retry-after"))
        if retry_after is not None:
            return max(0.0, retry_after)
        reset = _number(values.get("x-ratelimit-reset"))
        if reset is not None and reset > self._clock():
            return min(self._max_backoff, reset - self._clock())
        exponential = self._base_backoff * float(2**attempt)
        jitter = self._random() * self._base_backoff
        return min(self._max_backoff, exponential + jitter)

    async def sleep(self, seconds: float) -> None:
        await self._sleep(seconds)


def _integer(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def _number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None
