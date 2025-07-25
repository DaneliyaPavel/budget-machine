import json
from pathlib import Path
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator

from services.bank_bridge import app as service_app, kafka
from services.bank_bridge.app import _full_sync, BankName
from typing import AsyncGenerator, Any
from datetime import date, timedelta
from services.bank_bridge.connectors.base import (
    BaseConnector,
    TokenPair,
    Account,
    RawTxn,
)

SCHEMA_PATH = (
    Path(service_app.__file__).resolve().parents[2]
    / "schemas/bank-bridge/bank.err/1.0.0/schema.json"
)
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    ERR_SCHEMA = json.load(f)
ERR_VALIDATOR = Draft202012Validator(ERR_SCHEMA)


class DummyAccountsError(BaseConnector):
    name = "dummy"
    display = "Dummy"

    async def auth(self, code: str | None, **kwargs):
        return TokenPair("t")

    async def refresh(self, token: TokenPair) -> TokenPair:
        return token

    async def fetch_accounts(self, token: TokenPair):
        raise RuntimeError("boom")

    async def fetch_txns(
        self, token: TokenPair, account: Account, date_from, date_to
    ) -> AsyncGenerator[RawTxn, None]:
        if False:
            yield


class DummyTxnsError(DummyAccountsError):
    async def fetch_accounts(self, token: TokenPair):
        return [Account(id="acc1")]

    async def fetch_txns(
        self, token: TokenPair, account: Account, date_from, date_to
    ) -> AsyncGenerator[RawTxn, None]:
        if False:  # pragma: no cover - to satisfy AsyncGenerator type
            yield
        raise RuntimeError("fail")


@pytest.mark.asyncio
async def test_full_sync_accounts_error(monkeypatch):
    captured = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        captured.update({"topic": topic, "data": data})

    async def fake_load(bank, user):
        return TokenPair("t")

    monkeypatch.setattr(service_app, "_load_token", fake_load)
    monkeypatch.setattr(service_app, "get_connector", lambda b: DummyAccountsError)
    monkeypatch.setattr(kafka, "publish", fake_publish)

    await _full_sync(BankName.TINKOFF, str(uuid4()))

    assert captured["topic"] == "bank.err"
    ERR_VALIDATOR.validate(captured["data"])
    assert captured["data"]["error_code"] == "CONNECTOR_ERROR"
    assert captured["data"]["stage"] == "connector"
    assert captured["data"]["bank_id"] == "tinkoff"


@pytest.mark.asyncio
async def test_full_sync_txns_error(monkeypatch):
    captured = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        captured.update({"topic": topic, "data": data})

    async def fake_load(bank, user):
        return TokenPair("t")

    monkeypatch.setattr(service_app, "_load_token", fake_load)
    monkeypatch.setattr(service_app, "get_connector", lambda b: DummyTxnsError)
    monkeypatch.setattr(kafka, "publish", fake_publish)

    await _full_sync(BankName.TINKOFF, str(uuid4()))

    assert captured["topic"] == "bank.err"
    ERR_VALIDATOR.validate(captured["data"])
    assert captured["data"]["error_code"] == "CONNECTOR_ERROR"
    assert captured["data"]["stage"] == "connector"
    assert captured["data"]["bank_id"] == "tinkoff"


@pytest.mark.asyncio
async def test_error_metric_increment(monkeypatch):
    async def fake_publish(*args, **kwargs):
        pass

    async def fake_load(bank, user):
        return TokenPair("t")

    monkeypatch.setattr(service_app, "_load_token", fake_load)
    monkeypatch.setattr(service_app, "get_connector", lambda b: DummyAccountsError)
    monkeypatch.setattr(kafka, "publish", fake_publish)

    labels: list[tuple[str, str]] = []
    inc_calls: list[int] = []

    class DummyCounter:
        def inc(self):
            inc_calls.append(1)

    def fake_labels(bank, stage):
        labels.append((bank, stage))
        return DummyCounter()

    monkeypatch.setattr(service_app.ERROR_TOTAL, "labels", fake_labels)

    await _full_sync(BankName.TINKOFF, str(uuid4()))

    assert labels == [(str(BankName.TINKOFF), "connector")]
    assert inc_calls == [1]


@pytest.mark.asyncio
async def test_full_sync_respects_sync_days(monkeypatch):
    captured: dict[str, Any] = {}

    class FakeDate(date):
        @classmethod
        def today(cls) -> "date":
            return date(2022, 1, 31)

    async def fake_load(bank, user):
        return TokenPair("t")

    class DummyConnector(BaseConnector):
        name = "dummy"
        display = "Dummy"

        async def auth(self, code: str | None, **kwargs):
            return TokenPair("t")

        async def refresh(self, token: TokenPair) -> TokenPair:
            return token

        async def fetch_accounts(self, token: TokenPair):
            return [Account(id="acc1")]

        async def fetch_txns(
            self, token: TokenPair, account: Account, date_from, date_to
        ) -> AsyncGenerator[RawTxn, None]:
            captured["date_from"] = date_from
            captured["date_to"] = date_to
            if False:  # pragma: no cover - to satisfy AsyncGenerator type
                yield

    monkeypatch.setattr(service_app, "_load_token", fake_load)
    monkeypatch.setattr(service_app, "get_connector", lambda b: DummyConnector)
    monkeypatch.setattr(kafka, "publish", lambda *a, **k: None)
    monkeypatch.setattr(service_app, "date", FakeDate)
    monkeypatch.setattr(service_app, "SYNC_DAYS", 10)

    await _full_sync(BankName.TINKOFF, str(uuid4()))

    assert captured["date_to"] == date(2022, 1, 31)
    assert captured["date_from"] == date(2022, 1, 31) - timedelta(days=10)
