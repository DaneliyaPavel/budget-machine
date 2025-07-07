from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, AsyncGenerator

import json

from .. import vault


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

    #: machine-readable identifier
    name: str
    #: human friendly title
    display: str

    def __init__(self, user_id: str, token: TokenPair | None = None) -> None:
        self.user_id = user_id
        self.token = token.access_token if token else None
        self.refresh_token = token.refresh_token if token else None
        self.vault = vault.get_vault_client()

    async def _save_token(self, token: TokenPair) -> None:
        self.token = token.access_token
        self.refresh_token = token.refresh_token
        data = {"access_token": token.access_token}
        if token.refresh_token:
            data["refresh_token"] = token.refresh_token
        await self.vault.write(
            f"bank_tokens/{self.name}/{self.user_id}", json.dumps(data)
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
