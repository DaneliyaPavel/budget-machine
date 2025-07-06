import os
from datetime import datetime
from uuid import uuid4

import pytest
import respx
from httpx import Response

from services.bank_bridge.connectors.tinkoff import TinkoffConnector


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("TINKOFF_CLIENT_ID", "cid")
    monkeypatch.setenv("TINKOFF_CLIENT_SECRET", "secret")
    monkeypatch.setenv("TINKOFF_REDIRECT_URI", "https://app/callback")


def make_connector(token=None):
    return TinkoffConnector(user_id="u1", token=token)


@pytest.mark.asyncio
async def test_auth_url(monkeypatch):
    saved = {}

    async def fake_save(self):
        saved["token"] = self.token

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)
    c = make_connector(token="tok")
    url = await c.auth()
    assert "response_type=code" in url
    assert "client_id=cid" in url
    assert saved["token"] == "tok"


@pytest.mark.asyncio
async def test_refresh_no_token():
    c = make_connector()
    with pytest.raises(RuntimeError):
        await c.refresh()


@pytest.mark.asyncio
async def test_refresh_success(monkeypatch):
    c = make_connector()
    c.refresh_token = "r1"
    called = {}

    async def fake_save(self):
        called["save"] = True

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.post(c.TOKEN_URL).respond(200, json={"access_token": "at", "refresh_token": "r2"})
        token = await c.refresh()
    assert token == "at"
    assert c.token == "at"
    assert c.refresh_token == "r2"
    assert called.get("save")


@pytest.mark.asyncio
async def test_fetch_accounts(monkeypatch):
    c = make_connector(token="at")
    accounts = [{"id": 1}]
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "accounts").respond(200, json={"payload": accounts})
        result = await c.fetch_accounts()
    assert result == accounts


@pytest.mark.asyncio
async def test_fetch_accounts_refresh(monkeypatch):
    c = make_connector()
    c.refresh_token = "r1"
    async def noop(self):
        pass

    monkeypatch.setattr(TinkoffConnector, "_save_token", noop, raising=False)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.post(c.TOKEN_URL).respond(200, json={"access_token": "at"})
        rsx.get(c.BASE_URL + "accounts").respond(200, json={"payload": []})
        await c.fetch_accounts()


@pytest.mark.asyncio
async def test_fetch_txns(monkeypatch):
    c = make_connector(token="t1")
    txns = [{"id": 2}]
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "transactions").respond(200, json={"payload": txns})
        result = await c.fetch_txns("acc", start, end)
    assert result == txns


@pytest.mark.asyncio
async def test_fetch_txns_refresh(monkeypatch):
    c = make_connector()
    c.refresh_token = "r1"
    async def noop(self):
        pass

    monkeypatch.setattr(TinkoffConnector, "_save_token", noop, raising=False)
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.post(c.TOKEN_URL).respond(200, json={"access_token": "at"})
        rsx.get(c.BASE_URL + "transactions").respond(200, json={"payload": []})
        await c.fetch_txns("acc", start, end)


@pytest.mark.asyncio
async def test_refresh_error(monkeypatch):
    c = make_connector()
    c.refresh_token = "r1"
    with respx.mock(assert_all_called=True) as rsx:
        rsx.post(c.TOKEN_URL).respond(400)
        with pytest.raises(Exception):
            await c.refresh()


@pytest.mark.asyncio
async def test_fetch_accounts_error(monkeypatch):
    c = make_connector(token="at")
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "accounts").respond(500)
        with pytest.raises(Exception):
            await c.fetch_accounts()


@pytest.mark.asyncio
async def test_fetch_txns_error(monkeypatch):
    c = make_connector(token="at")
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(c.BASE_URL + "transactions").respond(401)
        with pytest.raises(Exception):
            await c.fetch_txns("acc", start, end)
