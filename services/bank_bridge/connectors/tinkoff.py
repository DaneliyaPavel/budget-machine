from __future__ import annotations

import os
from datetime import datetime
from urllib.parse import urlencode
from typing import Any

import httpx

from .base import BaseConnector


class TinkoffConnector(BaseConnector):
    """Connector implementation for Tinkoff Open API sandbox."""

    name = "tinkoff"
    display = "Тинькофф"

    BASE_URL = "https://api.tinkoff.ru/v1/"
    AUTH_URL = "https://id.tinkoff.ru/auth/authorize"
    TOKEN_URL = "https://id.tinkoff.ru/auth/token"

    def __init__(self, token: str | None = None) -> None:
        super().__init__(token)
        self.client_id = os.getenv("TINKOFF_CLIENT_ID", "")
        self.client_secret = os.getenv("TINKOFF_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("TINKOFF_REDIRECT_URI", "")
        self.refresh_token: str | None = None

    async def auth(self) -> str:
        """Return OAuth authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile payments accounts",
        }
        return self.AUTH_URL + "?" + urlencode(params)

    async def refresh(self) -> str:
        """Refresh OAuth token using stored refresh token."""
        if not self.refresh_token:
            raise RuntimeError("missing refresh token")
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.TOKEN_URL, data=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        self.token = data.get("access_token")
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        if not self.token:
            raise RuntimeError("no access token")
        return self.token

    async def fetch_accounts(self) -> list[dict[str, Any]]:
        token = self.token or await self.refresh()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.BASE_URL + "accounts", headers=headers, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("payload", [])

    async def fetch_txns(
        self, account_id: str, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        token = self.token or await self.refresh()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "account": account_id,
            "from": int(start.timestamp() * 1000),
            "to": int(end.timestamp() * 1000),
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.BASE_URL + "transactions",
                params=params,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        return data.get("payload", [])
