from __future__ import annotations

import asyncio
import time


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


class CircuitBreaker:
    """Minimal circuit breaker implementation."""

    def __init__(self, failures: int = 3, reset_timeout: float = 30.0) -> None:
        self.failures = failures
        self.reset_timeout = reset_timeout
        self._count = 0
        self._opened = 0.0
        self._lock = asyncio.Lock()

    async def before_request(self) -> None:
        async with self._lock:
            if self._opened:
                if time.monotonic() - self._opened < self.reset_timeout:
                    raise RuntimeError("circuit open")
                self._opened = 0.0
                self._count = 0

    async def success(self) -> None:
        async with self._lock:
            self._count = 0
            self._opened = 0.0

    async def failure(self) -> None:
        async with self._lock:
            self._count += 1
            if self._count >= self.failures:
                self._opened = time.monotonic()


__all__ = ["LeakyBucket", "CircuitBreaker"]
