from datetime import datetime
from uuid import uuid4

import pytest

from services.bank_bridge import normalizer


def test_normalize_record_credit():
    raw = {
        "amount": 100,
        "date": "2024-01-01T12:00:00",
        "account_id": uuid4(),
        "bank_txn_id": 1,
    }
    tx = normalizer.normalize_record(raw)
    assert tx.postings[0].side == "credit"
    assert tx.postings[0].amount == 100
    assert tx.posted_at == datetime.fromisoformat("2024-01-01T12:00:00+00:00")


def test_normalize_record_debit_default_currency():
    aid = uuid4()
    raw = {
        "amount": -50,
        "date": "2024-01-02T00:00:00",
        "account_id": aid,
        "bank_txn_id": 2,
    }
    tx = normalizer.normalize_record(raw)
    p = tx.postings[0]
    assert p.side == "debit"
    assert p.currency_code == "RUB"
    assert p.account_id == aid


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
    raw = {
        "amount": 10,
        "date": "2024-01-03T00:00:00",
        "account_id": uuid4(),
        "bank_txn_id": 5,
        "user_id": uuid4(),
    }
    await normalizer.process(raw)
    assert sent["topic"] == "bank.norm"
    assert sent["uid"] == str(raw["user_id"])
    assert sent["bid"] == "5"
    assert sent["data"]["postings"][0]["amount"] == 10


@pytest.mark.asyncio
async def test_process_error(monkeypatch):
    def bad_norm(raw):
        raise ValueError("boom")

    sent = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        sent.update({"topic": topic, "data": data})

    monkeypatch.setattr(normalizer, "normalize_record", bad_norm)
    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    raw = {"user_id": uuid4(), "bank_txn_id": 9}
    await normalizer.process(raw)
    assert sent["topic"] == "bank.err"
    assert sent["data"]["error"] == "boom"


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
    assert tx.payee == "Shop"
    assert tx.note == "note"


@pytest.mark.asyncio
async def test_process_external_id(monkeypatch):
    sent = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        sent.update(data)

    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    raw = {
        "amount": 5,
        "date": "2024-01-05T00:00:00",
        "account_id": uuid4(),
        "bank_txn_id": 7,
        "user_id": uuid4(),
    }
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
    raw = {"user_id": uuid4(), "bank_txn_id": 8, "foo": "bar"}
    await normalizer.process(raw)
    assert captured["data"]["foo"] == "bar"


@pytest.mark.asyncio
async def test_process_called_once(monkeypatch):
    count = 0

    async def fake_publish(*args, **kwargs):
        nonlocal count
        count += 1

    monkeypatch.setattr(normalizer.kafka, "publish", fake_publish)
    raw = {
        "amount": 1,
        "date": "2024-01-06T00:00:00",
        "account_id": uuid4(),
        "bank_txn_id": 10,
        "user_id": uuid4(),
    }
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
    await normalizer.process({"user_id": uuid4(), "bank_txn_id": 11})
    assert called
