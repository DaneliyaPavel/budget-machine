from uuid import uuid4, UUID
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from services.bank_bridge import normalizer

SCHEMA_PATH = (
    Path(normalizer.BASE_DIR) / "schemas/bank-bridge/bank.norm/1.0.0/schema.json"
)
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    NORM_SCHEMA = json.load(f)
VALIDATOR = Draft202012Validator(NORM_SCHEMA)

ERR_SCHEMA_PATH = (
    Path(normalizer.BASE_DIR) / "schemas/bank-bridge/bank.err/1.0.0/schema.json"
)
with open(ERR_SCHEMA_PATH, "r", encoding="utf-8") as f:
    ERR_SCHEMA = json.load(f)
ERR_VALIDATOR = Draft202012Validator(ERR_SCHEMA)


def test_normalize_record_credit():
    aid = uuid4()
    raw = {
        "amount": 100,
        "date": "2024-01-01T12:00:00",
        "account_id": aid,
        "bank_txn_id": 1,
    }
    tx = normalizer.normalize_record(raw)
    assert tx["direction"] == "in"
    assert float(tx["amount"]["value"]) == 100
    assert tx["account_external"] == str(aid)
    assert tx["posted_at"] == "2024-01-01T12:00:00+00:00"


def test_normalize_record_debit_default_currency():
    aid = uuid4()
    raw = {
        "amount": -50,
        "date": "2024-01-02T00:00:00",
        "account_id": aid,
        "bank_txn_id": 2,
    }
    tx = normalizer.normalize_record(raw)
    assert tx["direction"] == "out"
    assert tx["amount"]["currency"] == "RUB"
    assert tx["account_external"] == str(aid)


def test_normalize_record_missing_field():
    raw = {"amount": 1, "date": "bad", "account_id": uuid4(), "bank_txn_id": 3}
    with pytest.raises(Exception):
        normalizer.normalize_record(raw)


@pytest.mark.asyncio
async def test_process_success(monkeypatch):
    sent = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        sent.update({"topic": topic, "uid": user_id, "bid": bank_txn_id, "data": data})

    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    payload = {
        "amount": 10,
        "date": "2024-01-03T00:00:00",
        "account_id": uuid4(),
    }
    raw = {"user_id": str(uuid4()), "bank_txn_id": "5", "payload": payload}
    await normalizer.process(raw)
    assert sent["topic"] == "bank.norm"
    assert sent["uid"] == str(raw["user_id"])
    assert sent["bid"] == "5"
    data = sent["data"]
    VALIDATOR.validate(data)
    assert data["external_id"] == "5"
    assert data["raw"] == payload
    UUID(data["txn_id"])  # validate UUID format


@pytest.mark.asyncio
async def test_process_error(monkeypatch):
    def bad_norm(raw):
        raise ValueError("boom")

    sent = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        sent.update({"topic": topic, "data": data})

    monkeypatch.setattr(normalizer, "normalize_record", bad_norm)
    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    raw = {"user_id": str(uuid4()), "bank_txn_id": "9", "payload": {}}
    await normalizer.process(raw)
    assert sent["topic"] == "bank.err"
    ERR_VALIDATOR.validate(sent["data"])
    assert sent["data"]["error_code"] == "INVALID_DATA"
    assert sent["data"]["stage"] == "normalize"


@pytest.mark.asyncio
async def test_process_invalid_schema(monkeypatch):
    sent = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        sent.update({"topic": topic, "data": data})

    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    raw = {"user_id": str(uuid4()), "bank_txn_id": "1"}
    await normalizer.process(raw)
    assert sent["topic"] == "bank.err"
    ERR_VALIDATOR.validate(sent["data"])


def test_normalize_record_payee_and_note():
    aid = uuid4()
    raw = {
        "amount": 20,
        "date": "2024-01-04T00:00:00",
        "account_id": aid,
        "bank_txn_id": 4,
        "payee": "Shop",
        "description": "note",
    }
    tx = normalizer.normalize_record(raw)
    assert tx["description"] in {"note", "Shop"}


def test_normalize_record_timezone_and_bad_mcc():
    aid = uuid4()
    tz_date = datetime(2024, 1, 4, 12, tzinfo=timezone(timedelta(hours=3)))
    raw = {
        "amount": 20,
        "date": tz_date.isoformat(),
        "account_id": aid,
        "bank_txn_id": 12,
        "mcc": "bad",
    }
    tx = normalizer.normalize_record(raw)
    assert tx["posted_at"].endswith("+00:00")
    assert "mcc" not in tx


@pytest.mark.asyncio
async def test_process_external_id(monkeypatch):
    sent = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        sent.update(data)

    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    payload = {
        "amount": 5,
        "date": "2024-01-05T00:00:00",
        "account_id": uuid4(),
    }
    raw = {"user_id": str(uuid4()), "bank_txn_id": "7", "payload": payload}
    await normalizer.process(raw)
    assert sent["external_id"] == "7"


@pytest.mark.asyncio
async def test_process_error_contains_raw(monkeypatch):
    def bad_norm(raw):
        raise ValueError("fail")

    captured = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        captured.update(data)

    monkeypatch.setattr(normalizer, "normalize_record", bad_norm)
    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    raw = {"user_id": str(uuid4()), "bank_txn_id": "8", "payload": {"foo": "bar"}}
    await normalizer.process(raw)
    assert captured["payload"]["foo"] == "bar"
    assert captured["payload"]["bank_txn_id"] == "8"


@pytest.mark.asyncio
async def test_process_called_once(monkeypatch):
    count = 0

    async def fake_publish(*args, **kwargs):
        nonlocal count
        count += 1

    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    payload = {
        "amount": 1,
        "date": "2024-01-06T00:00:00",
        "account_id": uuid4(),
    }
    raw = {"user_id": str(uuid4()), "bank_txn_id": "10", "payload": payload}
    await normalizer.process(raw)
    assert count == 1


@pytest.mark.asyncio
async def test_process_calls_normalize(monkeypatch):
    called = False

    def fake_norm(raw):
        nonlocal called
        called = True
        return normalizer.normalize_record(
            {
                "amount": 1,
                "date": "2024-01-07T00:00:00",
                "account_id": uuid4(),
                "bank_txn_id": 11,
            }
        )

    async def fake_publish(*args, **kwargs):
        pass

    monkeypatch.setattr(normalizer, "normalize_record", fake_norm)
    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    await normalizer.process(
        {"user_id": str(uuid4()), "bank_txn_id": "11", "payload": {}}
    )
    assert called
