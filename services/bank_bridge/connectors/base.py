from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, AsyncGenerator

import asyncio
import time
import json
import random

import aiohttp

from .. import vault
from ..limits import LeakyBucket, CircuitBreaker, get_bucket, get_limits


@dataclass
class TokenPair:
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str | None = None
    expiry: datetime | None = None


@dataclass
class Account:
    """Minimal account representation."""

    id: str
    name: str | None = None
    currency: str | None = None


@dataclass
class RawTxn:
    """Raw transaction payload returned by bank APIs."""

    data: dict[str, Any]


class AuthError(RuntimeError):
    """Authentication failed after token refresh."""


class BaseConnector(ABC):
    """Abstract base class for bank connectors."""

    #: shared rate limiter for all connectors
    rate_limiter: LeakyBucket

    #: machine-readable identifier
    name: str
    #: human friendly title
    display: str

    _instances: set["BaseConnector"] = set()

    def __init__(self, user_id: str, token: TokenPair | None = None) -> None:
        self.user_id = user_id
        self.token = token.access_token if token else None
        self.refresh_token = token.refresh_token if token else None
        self.vault = vault.get_vault_client()
        rate, capacity = get_limits(self.name)
        self.rate_limiter = get_bucket(user_id, self.name, rate=rate, capacity=capacity)
        self.circuit_breaker = CircuitBreaker(failures=10, reset_timeout=900)
        self._session: aiohttp.ClientSession | None = None
        BaseConnector._instances.add(self)

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        BaseConnector._instances.discard(self)

    def __del__(self) -> None:
        if not getattr(self, "_session", None):
            return
        if self._session is not None and not self._session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._session.close())
            except Exception:
                pass

    @classmethod
    async def close_all(cls) -> None:
        for inst in list(cls._instances):
            await inst.close()

    async def _save_token(self, token: TokenPair) -> None:
        self.token = token.access_token
        self.refresh_token = token.refresh_token
        data = {"access_token": token.access_token}
        if token.refresh_token:
            data["refresh_token"] = token.refresh_token
        if token.expiry:
            data["expiry"] = token.expiry.isoformat()
        await self.vault.write(
            f"bank_tokens/{self.name}/{self.user_id}", json.dumps(data)
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float = 10,
        auth: bool = True,
    ) -> dict[str, Any]:
        """Perform HTTP request with retry, refresh and circuit breaker."""
        from ..app import FETCH_LATENCY_MS, RATE_LIMITED, logger

        start = time.monotonic()
        await self.rate_limiter.acquire()
        await self.circuit_breaker.before_request()

        hdrs = dict(headers or {})
        if auth and self.token:
            hdrs.setdefault("Authorization", f"Bearer {self.token}")

        refreshed = False
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
            session = self._session
            for attempt in range(5):
                try:
                    resp = await session.request(
                        method,
                        url,
                        headers=hdrs,
                        params=params,
                        json=json,
                        data=data,
                        timeout=timeout,
                    )
                except Exception:  # pragma: no cover - network errors
                    await self.circuit_breaker.failure()
                    if attempt == 4:
                        raise
                else:
                    if resp.status == 429:
                        logger.warning("http 429", extra={"bank": self.name})
                        RATE_LIMITED.labels(self.name).inc()
                        await resp.release()
                        if attempt == 4:
                            resp.raise_for_status()
                        delay = min(512, 4 * 2**attempt)
                        jitter = delay * 0.15
                        delay = random.uniform(delay - jitter, delay + jitter)
                        await asyncio.sleep(delay)
                        continue
                    if (
                        resp.status == 401
                        and auth
                        and self.refresh_token
                        and not refreshed
                    ):
                        try:
                            pair = await self.refresh(
                                TokenPair(self.token or "", self.refresh_token)
                            )
                        except Exception:
                            await self.circuit_breaker.failure()
                            raise
                        await self._save_token(pair)
                        hdrs["Authorization"] = f"Bearer {pair.access_token}"
                        refreshed = True
                        await resp.release()
                        continue

                    if resp.status == 401 and auth and refreshed:
                        await resp.release()
                        raise AuthError("unauthorized")

                    if resp.status >= 500:
                        await self.circuit_breaker.failure()
                        if attempt == 4:
                            await resp.release()
                            resp.raise_for_status()
                    else:
                        resp.raise_for_status()
                        await self.circuit_breaker.success()
                        data_resp = await resp.json()
                        return data_resp

                if attempt == 4:
                    raise RuntimeError("max retries exceeded")
                delay = min(512, 4 * 2**attempt)
                jitter = delay * 0.15
                delay = random.uniform(delay - jitter, delay + jitter)
                await asyncio.sleep(delay)

        finally:
            FETCH_LATENCY_MS.labels(self.name).observe(
                (time.monotonic() - start) * 1000
            )

    @abstractmethod
    async def auth(self, code: str | None, **kwargs: Any) -> TokenPair:
        """Perform authentication and return token pair."""

    @abstractmethod
    async def refresh(self, token: TokenPair) -> TokenPair:
        """Refresh and return new token pair."""

    @abstractmethod
    async def fetch_accounts(self, token: TokenPair) -> list[Account]:
        """Fetch available accounts."""

    @abstractmethod
    async def fetch_txns(
        self,
        token: TokenPair,
        account: Account,
        date_from: date,
        date_to: date,
    ) -> AsyncGenerator[RawTxn, None]:
        """Yield transactions for the given account and period."""
