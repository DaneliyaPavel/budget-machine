from datetime import datetime
import asyncio
import random
import logging
from yarl import URL

import pytest
from aioresponses import aioresponses
import re

from services.bank_bridge.app import FETCH_LATENCY_MS, RATE_LIMITED
from services.bank_bridge.connectors.tinkoff import TinkoffConnector
from services.bank_bridge.connectors.base import TokenPair, Account
from services.bank_bridge.limits import get_bucket, get_limits

USER_ID = "00000000-0000-0000-0000-000000000001"


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
        saved["expiry"] = token.expiry

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)
    c = make_connector()
    with aioresponses() as rsx:
        rsx.post(
            c.TOKEN_URL,
            payload={"access_token": "at", "refresh_token": "rt", "expires_in": 3600},
            status=200,
        )
        pair = await c.auth("code")
        req = rsx.requests[("POST", URL(c.TOKEN_URL))][0]
    assert pair.access_token == "at"
    assert pair.refresh_token == "rt"
    assert saved["token"] == "at"
    assert saved["expiry"] is not None
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
            payload={"access_token": "at", "refresh_token": "r2", "expires_in": 7200},
            status=200,
        )
        pair = await c.refresh(TokenPair("", "r1"))
        req = rsx.requests[("POST", URL(c.TOKEN_URL))][0]
    assert pair.access_token == "at"
    assert pair.refresh_token == "r2"
    assert pair.expiry is not None
    assert called.get("save")
    assert req.kwargs["headers"]["Authorization"].startswith("Basic")


@pytest.mark.asyncio
async def test_auth_redirect(monkeypatch):
    c = make_connector()
    pair = await c.auth(None)
    assert pair.access_token.startswith(c.AUTH_URL)


@pytest.mark.asyncio
async def test_auth_bad_expiry(monkeypatch):
    c = make_connector()

    async def fake_save(self, token):
        pass

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)

    with aioresponses() as rsx:
        rsx.post(
            c.TOKEN_URL,
            payload={"access_token": "at", "refresh_token": "rt", "expires_in": "x"},
            status=200,
        )
        pair = await c.auth("code")
    assert pair.expiry is None


@pytest.mark.asyncio
async def test_refresh_missing_access(monkeypatch):
    c = make_connector()

    async def fake_save(self, token):
        pass

    monkeypatch.setattr(TinkoffConnector, "_save_token", fake_save, raising=False)
    with aioresponses() as rsx:
        rsx.post(
            c.TOKEN_URL,
            payload={"refresh_token": "r2"},
            status=200,
        )
        with pytest.raises(RuntimeError):
            await c.refresh(TokenPair("t", "r1"))


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
async def test_fetch_txns_pagination(monkeypatch):
    c = make_connector()

    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 2)

    with aioresponses() as rsx:
        url_re = re.compile(r"https://api\.tinkoff\.ru/v1/transactions.*")
        rsx.get(url_re, payload={"payload": [{"id": 1}], "next": "c1"}, status=200)
        rsx.get(url_re, payload={"payload": [{"id": 2}]}, status=200)

        result = [
            t
            async for t in c.fetch_txns(
                TokenPair("t1"), Account(id="acc"), start.date(), end.date()
            )
        ]
        urls = [str(u[1]) for u in rsx.requests.keys()]

    assert [tx.data for tx in result] == [{"id": 1}, {"id": 2}]
    assert len(rsx.requests) == 2
    assert any("cursor=c1" in url for url in urls)


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
    hist_labels: list[str] = []

    class DummyHist:
        def observe(self, v):
            observed.append(v)

    def hist_label(bank):
        hist_labels.append(bank)
        return DummyHist()

    monkeypatch.setattr(FETCH_LATENCY_MS, "labels", hist_label)

    calls: list[int] = []
    counter_labels: list[str] = []

    class DummyCounter:
        def inc(self):
            calls.append(1)

    def rate_label(bank):
        counter_labels.append(bank)
        return DummyCounter()

    monkeypatch.setattr(RATE_LIMITED, "labels", rate_label)

    async def fake_sleep(_):
        pass

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    url = "https://example.com/r"  # any URL
    with aioresponses() as rsx:
        rsx.get(url, status=429)
        rsx.get(url, payload={}, status=200)
        await c._request("GET", url, auth=False)

    assert calls == [1]
    assert hist_labels == ["tinkoff"]
    assert counter_labels == ["tinkoff"]
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


def test_limits_from_env(monkeypatch):
    monkeypatch.setenv("BANK_BRIDGE_TINKOFF_RATE", "2")
    monkeypatch.setenv("BANK_BRIDGE_TINKOFF_CAPACITY", "9")
    rate, capacity = get_limits("tinkoff")
    assert rate == 2.0
    assert capacity == 9


def test_limits_defaults(monkeypatch):
    monkeypatch.delenv("BANK_BRIDGE_TINKOFF_RATE", raising=False)
    monkeypatch.delenv("BANK_BRIDGE_TINKOFF_CAPACITY", raising=False)
    rate, capacity = get_limits("tinkoff")
    assert rate == 20.0
    assert capacity == 20


def test_connector_uses_env_limits(monkeypatch):
    uid = "00000000-0000-0000-0000-000000000099"
    monkeypatch.setenv("BANK_BRIDGE_TINKOFF_RATE", "3")
    monkeypatch.setenv("BANK_BRIDGE_TINKOFF_CAPACITY", "7")
    c = TinkoffConnector(user_id=uid, token=None)
    assert c.rate_limiter.rate == 3.0
    assert c.rate_limiter.capacity == 7


def test_connector_uses_default_limits(monkeypatch):
    uid = "00000000-0000-0000-0000-000000000099"
    monkeypatch.delenv("BANK_BRIDGE_TINKOFF_RATE", raising=False)
    monkeypatch.delenv("BANK_BRIDGE_TINKOFF_CAPACITY", raising=False)
    c = TinkoffConnector(user_id=uid, token=None)
    assert c.rate_limiter.rate == 20.0
    assert c.rate_limiter.capacity == 20


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

    assert sleeps == [pytest.approx(3.4)]
    assert args == [(3.4, 4.6)]


@pytest.mark.asyncio
async def test_request_backoff_rate_limit(monkeypatch):
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

    calls: list[int] = []
    labels: list[str] = []

    class DummyCounter:
        def inc(self):
            calls.append(1)

    def label(bank):
        labels.append(bank)
        return DummyCounter()

    monkeypatch.setattr(RATE_LIMITED, "labels", label)

    url = "https://example.com/backoff429"
    with aioresponses() as rsx:
        rsx.get(url, status=429)
        rsx.get(url, payload={}, status=200)
        await c._request("GET", url, auth=False)

    assert sleeps == [pytest.approx(3.4)]
    assert args == [(3.4, 4.6)]
    assert labels == ["tinkoff"]
    assert calls == [1]


@pytest.mark.asyncio
async def test_request_backoff_max(monkeypatch):
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

    url = "https://example.com/backoff-max"
    with aioresponses() as rsx:
        for _ in range(8):
            rsx.get(url, status=500)
        rsx.get(url, payload={}, status=200)
        await c._request("GET", url, auth=False)

    steps = [4, 8, 16, 32, 64, 128, 256, 512]
    expected_sleeps = [s * 0.85 for s in steps]
    assert sleeps == [pytest.approx(v) for v in expected_sleeps]
    expected_args = [(s * 0.85, s * 1.15) for s in steps]
    assert args == expected_args


@pytest.mark.asyncio
async def test_request_logs_rate_limit(monkeypatch, caplog):
    c = make_connector("t1")

    class DummyCounter:
        def inc(self):
            pass

    monkeypatch.setattr(RATE_LIMITED, "labels", lambda bank: DummyCounter())

    async def fake_sleep(_):
        pass

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    caplog.set_level(logging.WARNING, logger="bank_bridge")
    logger = logging.getLogger("bank_bridge")
    logger.addHandler(caplog.handler)
    url = "https://example.com/log429"
    with aioresponses() as rsx:
        rsx.get(url, status=429)
        rsx.get(url, payload={}, status=200)
        await c._request("GET", url, auth=False)
    logger.removeHandler(caplog.handler)

    assert ("http 429", "tinkoff") in [
        (r.message, getattr(r, "bank", None)) for r in caplog.records
    ]
