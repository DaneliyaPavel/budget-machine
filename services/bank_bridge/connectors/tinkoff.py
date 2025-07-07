from __future__ import annotations

import os
from datetime import date, datetime
from urllib.parse import urlencode
from typing import Any, AsyncGenerator

import httpx

from .base import Account, BaseConnector, RawTxn, TokenPair


class TinkoffConnector(BaseConnector):
    """Connector implementation for Tinkoff Open API sandbox."""

    name = "tinkoff"
    display = "Тинькофф"

    BASE_URL = "https://api.tinkoff.ru/v1/"
    AUTH_URL = "https://id.tinkoff.ru/auth/authorize"
    TOKEN_URL = "https://id.tinkoff.ru/auth/token"

    def __init__(self, user_id: str, token: TokenPair | None = None) -> None:
        super().__init__(user_id, token)
        self.client_id = os.getenv("TINKOFF_CLIENT_ID", "")
        self.client_secret = os.getenv("TINKOFF_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv("TINKOFF_REDIRECT_URI", "")

    async def auth(self, code: str | None, **kwargs: Any) -> TokenPair:
        """Return OAuth token pair using provided authorization code."""
        if code is None:
            url = self.AUTH_URL + "?" + urlencode(
                {
                    "response_type": "code",
                    "client_id": self.client_id,
                    "redirect_uri": self.redirect_uri,
                    "scope": "openid profile payments accounts",
                }
            )
            return TokenPair(access_token=url)

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.TOKEN_URL, data=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        pair = TokenPair(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token"),
        )
        await self._save_token(pair)
        return pair

    async def refresh(self, token: TokenPair) -> TokenPair:
        """Refresh OAuth token using provided refresh token."""
        if not token.refresh_token:
            raise RuntimeError("missing refresh token")
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": token.refresh_token,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.TOKEN_URL, data=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        pair = TokenPair(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", token.refresh_token),
        )
        if not pair.access_token:
            raise RuntimeError("no access token")
        await self._save_token(pair)
        return pair

    async def fetch_accounts(self, token: TokenPair) -> list[Account]:
        current = token.access_token
        if not current and token.refresh_token:
            token = await self.refresh(token)
            current = token.access_token
        headers = {"Authorization": f"Bearer {current}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self.BASE_URL + "accounts", headers=headers, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
        return [Account(id=str(a.get("id"))) for a in data.get("payload", [])]

    async def fetch_txns(
        self,
        token: TokenPair,
        account: Account,
        date_from: date,
        date_to: date,
    ) -> AsyncGenerator[RawTxn, None]:
        current = token.access_token
        if not current and token.refresh_token:
            token = await self.refresh(token)
            current = token.access_token
        headers = {"Authorization": f"Bearer {current}"}
        params = {
            "account": account.id,
            "from": int(datetime.combine(date_from, datetime.min.time()).timestamp() * 1000),
            "to": int(datetime.combine(date_to, datetime.min.time()).timestamp() * 1000),
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
        for item in data.get("payload", []):
            yield RawTxn(data=item)
