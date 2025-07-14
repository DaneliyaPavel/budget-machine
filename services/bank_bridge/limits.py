from __future__ import annotations

import os

import asyncio
import time
from prometheus_client import Gauge


class LeakyBucket:
    """Simple async leaky bucket rate limiter."""

    def __init__(self, rate: float, capacity: int) -> None:
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                leaked = (now - self._updated) * self.rate
                self._updated = now
                self._tokens = min(self.capacity, self._tokens + leaked)
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                delay = (1 - self._tokens) / self.rate
            await asyncio.sleep(delay)


#
# Bucket storage -------------------------------------------------------------
#

_BUCKETS: dict[tuple[str, str], "LeakyBucket"] = {}

# Default rate limits for built-in connectors.
# Values are expressed as ``(rate, capacity)`` where ``rate`` is requests per
# second and ``capacity`` is the bucket size.
DEFAULT_LIMITS: dict[str, tuple[float, int]] = {
    "tinkoff": (20.0, 20),
    "sber": (10.0, 10),
    "gazprom": (20.0, 20),
    "alfa": (20.0, 20),
    "vtb": (20.0, 20),
}


def _load_limits(bank: str, rate: float, capacity: int) -> tuple[float, int]:
    """Return rate limiter parameters from environment."""
    prefix = f"BANK_BRIDGE_{bank.upper()}_"
    env_rate = os.getenv(prefix + "RATE")
    env_capacity = os.getenv(prefix + "CAPACITY")
    if env_rate is not None:
        try:
            rate = float(env_rate)
        except ValueError:
            pass
    if env_capacity is not None:
        try:
            capacity = int(env_capacity)
        except ValueError:
            pass
    return rate, capacity


def get_limits(bank: str, *, rate: float = 1.0, capacity: int = 5) -> tuple[float, int]:
    """Return rate limiter params for the connector."""
    default_rate, default_capacity = DEFAULT_LIMITS.get(bank, (rate, capacity))
    return _load_limits(bank, default_rate, default_capacity)


def get_bucket(
    user_id: str, bank: str, *, rate: float = 1.0, capacity: int = 5
) -> "LeakyBucket":
    """Return shared bucket for ``user_id``/``bank`` pair."""
    key = (user_id, bank)
    bucket = _BUCKETS.get(key)
    if bucket is None:
        bucket = LeakyBucket(rate=rate, capacity=capacity)
        _BUCKETS[key] = bucket
    else:
        # Bucket for this ``user_id``/``bank`` already exists. Environment
        # variables may have changed between calls, so update rate and
        # capacity to ensure new settings take effect.  Tokens are capped by
        # the new capacity to avoid unlimited bursts.
        if bucket.rate != rate or bucket.capacity != capacity:
            bucket.rate = rate
            bucket.capacity = capacity
            bucket._tokens = min(bucket._tokens, float(capacity))
    return bucket


class CircuitBreaker:
    """Minimal circuit breaker implementation."""

    def __init__(
        self,
        failures: int = 3,
        reset_timeout: float = 30.0,
        *,
        bank: str | None = None,
        gauge: "Gauge" | None = None,
    ) -> None:
        self.failures = failures
        self.reset_timeout = reset_timeout
        self._count = 0
        self._opened = 0.0
        self._lock = asyncio.Lock()
        self._metric = gauge.labels(bank) if gauge and bank else None

    async def before_request(self) -> None:
        async with self._lock:
            if self._opened:
                if time.monotonic() - self._opened < self.reset_timeout:
                    raise RuntimeError("circuit open")
                self._opened = 0.0
                self._count = 0
                if self._metric:
                    self._metric.set(0)

    async def success(self) -> None:
        async with self._lock:
            self._count = 0
            self._opened = 0.0
            if self._metric:
                self._metric.set(0)

    async def failure(self) -> None:
        async with self._lock:
            self._count += 1
            if self._count >= self.failures:
                self._opened = time.monotonic()
                if self._metric:
                    self._metric.set(1)


__all__ = [
    "LeakyBucket",
    "CircuitBreaker",
    "get_bucket",
    "get_limits",
    "DEFAULT_LIMITS",
]
