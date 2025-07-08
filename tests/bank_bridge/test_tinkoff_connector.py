from datetime import datetime

import pytest
import respx

from services.bank_bridge.connectors.tinkoff import TinkoffConnector
from services.bank_bridge.connectors.base import TokenPair, Account


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("TINKOFF_CLIENT_ID", "cid")
    monkeypatch.setenv("TINKOFF_CLIENT_SECRET", "secret")
    monkeypatch.setenv("TINKOFF_REDIRECT_URI", "https://app/callback")


def make_connector(token=None, refresh=None):
    pair = TokenPair(token, refresh) if token or refresh else None
    return TinkoffConnector(user_id="u1", token=pair)


@pytest.mark.asyncio
async def test_auth(monkeypatch):
    saved = {}

    async def fake_save(self, token):
        saved["token"] = token.access_token

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)
    c = make_connector()
    with respx.mock(assert_all_called=True) as rsx:
        route = rsx.post(c.TOKEN_URL).respond(
            200, json={"access_token": "at", "refresh_token": "rt"}
        )
        pair = await c.auth("code")
    assert pair.access_token == "at"
    assert pair.refresh_token == "rt"
    assert saved["token"] == "at"
    assert route.calls.last.request.headers["Authorization"].startswith("Basic")


@pytest.mark.asyncio
async def test_refresh_no_token():
    c = make_connector()
    with pytest.raises(RuntimeError):
        await c.refresh(TokenPair(""))


@pytest.mark.asyncio
async def test_refresh_success(monkeypatch):
    c = make_connector()
    called = {}

    async def fake_save(self, token):
        called["save"] = True

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)
    with respx.mock(assert_all_called=True) as rsx:
        route = rsx.post(c.TOKEN_URL).respond(
            200, json={"access_token": "at", "refresh_token": "r2"}
        )
        pair = await c.refresh(TokenPair("", "r1"))
    assert pair.access_token == "at"
    assert pair.refresh_token == "r2"
    assert called.get("save")
    assert route.calls.last.request.headers["Authorization"].startswith("Basic")


@pytest.mark.asyncio
async def test_fetch_accounts(monkeypatch):
    c = make_connector()
    accounts = [{"id": 1}]
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "accounts").respond(200, json={"payload": accounts})
        result = await c.fetch_accounts(TokenPair("at"))
    assert result == [Account(id="1")]


@pytest.mark.asyncio
async def test_fetch_accounts_refresh(monkeypatch):
    c = make_connector()

    async def noop(self, token):
        pass

    monkeypatch.setattr(TinkoffConnector, "_save_token", noop, raising=False)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.post(c.TOKEN_URL).respond(200, json={"access_token": "at"})
        rsx.get(c.BASE_URL + "accounts").respond(200, json={"payload": []})
        await c.fetch_accounts(TokenPair("", "r1"))


@pytest.mark.asyncio
async def test_fetch_txns(monkeypatch):
    c = make_connector()
    txns = [{"id": 2}]
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "transactions").respond(200, json={"payload": txns})
        result = [
            t
            async for t in c.fetch_txns(
                TokenPair("t1"), Account(id="acc"), start.date(), end.date()
            )
        ]
    assert [tx.data for tx in result] == txns


@pytest.mark.asyncio
async def test_fetch_txns_refresh(monkeypatch):
    c = make_connector()

    async def noop(self, token):
        pass

    monkeypatch.setattr(TinkoffConnector, "_save_token", noop, raising=False)
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.post(c.TOKEN_URL).respond(200, json={"access_token": "at"})
        rsx.get(c.BASE_URL + "transactions").respond(200, json={"payload": []})
        result = [
            t
            async for t in c.fetch_txns(
                TokenPair("", "r1"), Account(id="acc"), start.date(), end.date()
            )
        ]
    assert result == []


@pytest.mark.asyncio
async def test_refresh_error(monkeypatch):
    c = make_connector()
    with respx.mock(assert_all_called=True) as rsx:
        rsx.post(c.TOKEN_URL).respond(400)
        with pytest.raises(Exception):
            await c.refresh(TokenPair("", "r1"))


@pytest.mark.asyncio
async def test_fetch_accounts_error(monkeypatch):
    c = make_connector()
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "accounts").respond(500)
        with pytest.raises(Exception):
            await c.fetch_accounts(TokenPair("at"))


@pytest.mark.asyncio
async def test_fetch_txns_error(monkeypatch):
    c = make_connector()
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "transactions").respond(401)
        with pytest.raises(Exception):
            [
                t
                async for t in c.fetch_txns(
                    TokenPair("at"), Account(id="acc"), start.date(), end.date()
                )
            ]
