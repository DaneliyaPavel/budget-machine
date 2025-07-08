from datetime import datetime
import asyncio
import httpx

import pytest
import respx

from services.bank_bridge.connectors.tinkoff import TinkoffConnector
from services.bank_bridge.connectors.base import TokenPair, Account
from services.bank_bridge.limits import get_bucket
import random
from services.bank_bridge.app import FETCH_LATENCY_MS, RATE_LIMITED


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


@pytest.mark.asyncio
async def test_request_metrics(monkeypatch):
    c = make_connector("t1")

    observed: list[float] = []
    monkeypatch.setattr(FETCH_LATENCY_MS, "observe", lambda v: observed.append(v))

    calls: list[int] = []
    monkeypatch.setattr(RATE_LIMITED, "inc", lambda: calls.append(1))

    async def fake_sleep(_):
        pass

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    url = "https://example.com/r"  # any URL
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(url).respond(429)
        with pytest.raises(httpx.HTTPStatusError):
            await c._request("GET", url, auth=False)

    assert calls == [1]
    assert len(observed) == 1
    assert observed[0] >= 0


def test_leaky_bucket_store():
    b1 = get_bucket("u1", "tinkoff")
    b2 = get_bucket("u1", "tinkoff")
    b3 = get_bucket("u2", "tinkoff")
    assert b1 is b2
    assert b1 is not b3


def test_circuit_breaker_params():
    c = make_connector()
    assert c.circuit_breaker.failures == 10
    assert c.circuit_breaker.reset_timeout == 900


@pytest.mark.asyncio
async def test_request_backoff(monkeypatch):
    c = make_connector("t1")
    sleeps: list[float] = []

    async def fake_sleep(d):
        sleeps.append(d)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    args: list[tuple[float, float]] = []

    def fake_uniform(a, b):
        args.append((a, b))
        return a

    monkeypatch.setattr(random, "uniform", fake_uniform)

    url = "https://example.com/backoff"
    with respx.mock(assert_all_called=True) as rsx:
        rsx.get(url).mock(side_effect=[httpx.Response(500), httpx.Response(200)])
        await c._request("GET", url, auth=False)

    assert sleeps == [pytest.approx(0.85)]
    assert args == [(0.85, 1.15)]
