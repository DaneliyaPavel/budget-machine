from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseConnector(ABC):
    """Abstract base class for bank connectors."""

    #: machine-readable identifier
    name: str
    #: human friendly title
    display: str

    def __init__(self, token: str | None = None) -> None:
        self.token = token

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
