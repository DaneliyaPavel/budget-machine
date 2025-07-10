from datetime import datetime
import asyncio
import aiohttp
from yarl import URL

import pytest
from aioresponses import aioresponses
import re

from services.bank_bridge.connectors.tinkoff import TinkoffConnector
from services.bank_bridge.connectors.base import TokenPair, Account

USER_ID = "00000000-0000-0000-0000-000000000001"
from services.bank_bridge.limits import get_bucket
import random
from services.bank_bridge.app import FETCH_LATENCY_MS, RATE_LIMITED


@pytest.fixture(autouse=True)
def env_setup(monkeypatch):
    monkeypatch.setenv("BANK_BRIDGE_TINKOFF_CLIENT_ID", "cid")
    monkeypatch.setenv("BANK_BRIDGE_TINKOFF_CLIENT_SECRET", "secret")
    monkeypatch.setenv("BANK_BRIDGE_TINKOFF_REDIRECT_URI", "https://app/callback")


def make_connector(token=None, refresh=None):
    pair = TokenPair(token, refresh) if token or refresh else None
    return TinkoffConnector(user_id=USER_ID, token=pair)


@pytest.mark.asyncio
async def test_auth(monkeypatch):
    saved = {}

    async def fake_save(self, token):
        saved["token"] = token.access_token

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)
    c = make_connector()
    with aioresponses() as rsx:
        rsx.post(
            c.TOKEN_URL,
            payload={"access_token": "at", "refresh_token": "rt"},
            status=200,
        )
        pair = await c.auth("code")
        req = rsx.requests[("POST", URL(c.TOKEN_URL))][0]
    assert pair.access_token == "at"
    assert pair.refresh_token == "rt"
    assert saved["token"] == "at"
    assert req.kwargs["headers"]["Authorization"].startswith("Basic")


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
    with aioresponses() as rsx:
        rsx.post(
            c.TOKEN_URL,
            payload={"access_token": "at", "refresh_token": "r2"},
            status=200,
        )
        pair = await c.refresh(TokenPair("", "r1"))
        req = rsx.requests[("POST", URL(c.TOKEN_URL))][0]
    assert pair.access_token == "at"
    assert pair.refresh_token == "r2"
    assert called.get("save")
    assert req.kwargs["headers"]["Authorization"].startswith("Basic")


@pytest.mark.asyncio
async def test_fetch_accounts(monkeypatch):
    c = make_connector()
    accounts = [{"id": 1}]
    with aioresponses() as rsx:
        rsx.get(
            c.BASE_URL + "accounts",
            payload={"payload": accounts},
            status=200,
        )
        result = await c.fetch_accounts(TokenPair("at"))
    assert result == [Account(id="1")]


@pytest.mark.asyncio
async def test_fetch_accounts_refresh(monkeypatch):
    c = make_connector()

    async def noop(self, token):
        pass

    monkeypatch.setattr(TinkoffConnector, "_save_token", noop, raising=False)
    with aioresponses() as rsx:
        rsx.post(c.TOKEN_URL, payload={"access_token": "at"}, status=200)
        rsx.get(c.BASE_URL + "accounts", payload={"payload": []}, status=200)
        await c.fetch_accounts(TokenPair("", "r1"))


@pytest.mark.asyncio
async def test_fetch_txns(monkeypatch):
    c = make_connector()
    txns = [{"id": 2}]
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with aioresponses() as rsx:
        rsx.get(
            re.compile(r"https://api\.tinkoff\.ru/v1/transactions.*"),
            payload={"payload": txns},
            status=200,
        )
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
    with aioresponses() as rsx:
        rsx.post(c.TOKEN_URL, payload={"access_token": "at"}, status=200)
        rsx.get(
            re.compile(r"https://api\.tinkoff\.ru/v1/transactions.*"),
            payload={"payload": []},
            status=200,
        )
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
    with aioresponses() as rsx:
        rsx.post(c.TOKEN_URL, status=400)
        with pytest.raises(Exception):
            await c.refresh(TokenPair("", "r1"))


@pytest.mark.asyncio
async def test_fetch_accounts_error(monkeypatch):
    c = make_connector()
    with aioresponses() as rsx:
        rsx.get(c.BASE_URL + "accounts", status=500)
        with pytest.raises(Exception):
            await c.fetch_accounts(TokenPair("at"))


@pytest.mark.asyncio
async def test_fetch_txns_error(monkeypatch):
    c = make_connector()
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)
    with aioresponses() as rsx:
        rsx.get(
            re.compile(r"https://api\.tinkoff\.ru/v1/transactions.*"),
            status=401,
        )
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
    with aioresponses() as rsx:
        rsx.get(url, status=429)
        with pytest.raises(aiohttp.ClientResponseError):
            await c._request("GET", url, auth=False)

    assert calls == [1]
    assert len(observed) == 1
    assert observed[0] >= 0


def test_leaky_bucket_store():
    b1 = get_bucket(USER_ID, "tinkoff")
    b2 = get_bucket(USER_ID, "tinkoff")
    b3 = get_bucket("00000000-0000-0000-0000-000000000002", "tinkoff")
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
    with aioresponses() as rsx:
        rsx.get(url, status=500)
        rsx.get(url, status=200)
        await c._request("GET", url, auth=False)

    assert sleeps == [pytest.approx(0.85)]
    assert args == [(0.85, 1.15)]
