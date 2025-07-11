import pytest
from typing import AsyncGenerator

from services.bank_bridge.connectors.base import (
    BaseConnector,
    TokenPair,
    Account,
    RawTxn,
)


class DummyConnector(BaseConnector):
    name = "dummy"
    display = "Dummy"

    async def auth(self, code: str | None, **kwargs):
        return TokenPair("t")

    async def refresh(self, token: TokenPair) -> TokenPair:
        return token

    async def fetch_accounts(self, token: TokenPair):
        return []

    async def fetch_txns(
        self, token: TokenPair, account: Account, date_from, date_to
    ) -> AsyncGenerator[RawTxn, None]:
        if False:
            yield


@pytest.mark.asyncio
async def test_session_reuse(monkeypatch):
    class DummyResp:
        def __init__(self) -> None:
            self.status = 200

        async def json(self):
            return {}

        async def release(self):
            pass

        def raise_for_status(self):
            pass

    class DummySession:
        def __init__(self) -> None:
            self.calls = 0
            self.closed = False

        async def request(self, *a, **k):
            self.calls += 1
            return DummyResp()

        async def close(self) -> None:
            self.closed = True

    session = DummySession()
    monkeypatch.setattr(
        "services.bank_bridge.connectors.base.aiohttp.ClientSession",
        lambda: session,
    )

    c = DummyConnector("user")
    await c._request("GET", "https://example.com", auth=False)
    await c._request("GET", "https://example.com", auth=False)

    assert session.calls == 2
    assert not session.closed

    await c.close()
    assert session.closed
