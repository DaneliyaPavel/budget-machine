from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, AsyncGenerator

import asyncio
import time
import json
import random

import httpx

from .. import vault
from ..limits import LeakyBucket, CircuitBreaker, get_bucket


@dataclass
class TokenPair:
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str | None = None


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


class BaseConnector(ABC):
    """Abstract base class for bank connectors."""

    #: shared rate limiter for all connectors
    rate_limiter: LeakyBucket

    #: machine-readable identifier
    name: str
    #: human friendly title
    display: str

    def __init__(self, user_id: str, token: TokenPair | None = None) -> None:
        self.user_id = user_id
        self.token = token.access_token if token else None
        self.refresh_token = token.refresh_token if token else None
        self.vault = vault.get_vault_client()
        self.rate_limiter = get_bucket(user_id, self.name)
        self.circuit_breaker = CircuitBreaker(failures=10, reset_timeout=900)

    async def _save_token(self, token: TokenPair) -> None:
        self.token = token.access_token
        self.refresh_token = token.refresh_token
        data = {"access_token": token.access_token}
        if token.refresh_token:
            data["refresh_token"] = token.refresh_token
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
    ) -> httpx.Response:
        """Perform HTTP request with retry, refresh and circuit breaker."""
        from ..app import FETCH_LATENCY_MS, RATE_LIMITED

        start = time.monotonic()
        await self.rate_limiter.acquire()
        await self.circuit_breaker.before_request()

        hdrs = dict(headers or {})
        if auth and self.token:
            hdrs.setdefault("Authorization", f"Bearer {self.token}")

        refreshed = False
        try:
            for attempt in range(5):
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.request(
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
                    if resp.status_code == 429:
                        RATE_LIMITED.inc()
                    if (
                        resp.status_code == 401
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
                        continue

                    if resp.status_code >= 500:
                        await self.circuit_breaker.failure()
                        if attempt == 4:
                            resp.raise_for_status()
                        # prepare for retry
                    else:
                        resp.raise_for_status()
                        await self.circuit_breaker.success()
                        return resp

                if attempt == 4:
                    raise RuntimeError("max retries exceeded")
                delay = min(512, 2**attempt)
                jitter = delay * 0.15
                delay = random.uniform(delay - jitter, delay + jitter)
                await asyncio.sleep(delay)

        finally:
            FETCH_LATENCY_MS.observe((time.monotonic() - start) * 1000)

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
