import json
from pathlib import Path
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator

from services.bank_bridge import app as service_app, kafka
from services.bank_bridge.app import _full_sync, BankName
from typing import AsyncGenerator
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
