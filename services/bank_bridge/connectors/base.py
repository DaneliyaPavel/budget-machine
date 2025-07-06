from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import json

from .. import vault


class BaseConnector(ABC):
    """Abstract base class for bank connectors."""

    #: machine-readable identifier
    name: str
    #: human friendly title
    display: str

    def __init__(self, user_id: str, token: str | None = None) -> None:
        self.user_id = user_id
        self.token = token
        self.vault = vault.get_vault_client()

    async def _save_token(self) -> None:
        if self.token is None:
            return
        data = {"access_token": self.token}
        refresh_token = getattr(self, "refresh_token", None)
        if refresh_token:
            data["refresh_token"] = refresh_token
        await self.vault.write(
            f"bank_tokens/{self.name}/{self.user_id}", json.dumps(data)
        )

    @abstractmethod
    async def auth(self) -> str:
        """Start authentication flow and return URL for the user."""

    @abstractmethod
    async def refresh(self) -> str:
        """Refresh and return access token."""

    @abstractmethod
    async def fetch_accounts(self) -> list[dict[str, Any]]:
        """Fetch available accounts."""

    @abstractmethod
    async def fetch_txns(
        self, account_id: str, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """Fetch transactions for the given account and period."""
