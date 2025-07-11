import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from typing import AsyncGenerator

from services.bank_bridge import app as service_app, kafka, vault
from services.bank_bridge.app import _refresh_tokens_once
from services.bank_bridge.connectors.base import (
    BaseConnector,
    TokenPair,
    Account,
    RawTxn,
    AuthError,
)

SCHEMA_PATH = (
    Path(service_app.__file__).resolve().parents[2]
    / "schemas/bank-bridge/bank.err/1.0.0/schema.json"
)
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    ERR_SCHEMA = json.load(f)
ERR_VALIDATOR = Draft202012Validator(ERR_SCHEMA)


class DummyRefreshError(BaseConnector):
    name = "dummy"
    display = "Dummy"

    async def auth(self, code: str | None, **kwargs):
        return TokenPair("t")

    async def refresh(self, token: TokenPair) -> TokenPair:
        raise AuthError("fail")

    async def fetch_accounts(self, token: TokenPair):
        return []

    async def fetch_txns(
        self, token: TokenPair, account: Account, date_from, date_to
    ) -> AsyncGenerator[RawTxn, None]:
        if False:
            yield


@pytest.mark.asyncio
async def test_refresh_tokens_auth_error(monkeypatch):
    deleted: list[str] = []
    captured: dict[str, object] = {}

    class FakeVault:
        async def delete(self, path: str):
            deleted.append(path)

    async def fake_load(bank, user):
        return TokenPair("at", "rt")

    async def fake_publish(topic, user_id, bank_txn_id, data):
        captured.update({"topic": topic, "data": data})

    monkeypatch.setattr(service_app, "CONNECTORS", {"tinkoff": DummyRefreshError})
    monkeypatch.setattr(service_app, "get_connector", lambda b: DummyRefreshError)
    monkeypatch.setattr(service_app, "_load_token", fake_load)
    monkeypatch.setattr(vault, "get_vault_client", lambda: FakeVault())
    monkeypatch.setattr(kafka, "publish", fake_publish)

    await _refresh_tokens_once("user1")

    assert deleted == ["bank_tokens/tinkoff/user1"]
    assert captured["topic"] == "bank.err"
    ERR_VALIDATOR.validate(captured["data"])
    assert captured["data"]["error_code"] == "AUTH_ERROR"
    assert captured["data"]["stage"] == "auth"
    assert captured["data"]["bank_id"] == "tinkoff"


@pytest.mark.asyncio
async def test_get_user_ids(monkeypatch):
    class FakeVault:
        async def list(self, path: str):
            if path == "bank_tokens/tinkoff":
                return ["u1", "u2"]
            return []

    monkeypatch.setattr(vault, "get_vault_client", lambda: FakeVault())
    ids = await service_app._get_user_ids()
    assert set(ids) == {"u1", "u2"}


@pytest.mark.asyncio
async def test_refresh_tokens_loop(monkeypatch):
    calls: list[str] = []

    async def fake_get_user_ids():
        return ["u1", "u2"]

    async def fake_refresh(uid="default"):
        calls.append(uid)

    async def fake_sleep(seconds):
        raise RuntimeError("stop")

    monkeypatch.setattr(service_app, "_get_user_ids", fake_get_user_ids)
    monkeypatch.setattr(service_app, "_refresh_tokens_once", fake_refresh)
    monkeypatch.setattr(service_app.asyncio, "sleep", fake_sleep)

    with pytest.raises(RuntimeError):
        await service_app._refresh_tokens_loop()

    assert calls == ["u1", "u2"]
