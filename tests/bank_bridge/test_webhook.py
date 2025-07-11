import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

from services.bank_bridge.app import app, RAW_TOPIC
from services.bank_bridge import kafka, vault
from services.bank_bridge.connectors import TokenPair

USER_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
async def test_tinkoff_webhook(monkeypatch):
    captured = {}

    async def fake_publish(topic, user_id, bank_txn_id, data):
        captured.update(
            {
                "topic": topic,
                "user_id": user_id,
                "bank_txn_id": bank_txn_id,
                "data": data,
            }
        )

    monkeypatch.setattr(kafka, "publish", fake_publish)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            payload = {"event": "operation", "payload": {"id": 1, "amount": 10}}
            resp = await cl.post(f"/webhook/tinkoff/{USER_ID}", json=payload)
            assert resp.status_code == 200

    assert captured["topic"] == RAW_TOPIC
    assert captured["user_id"] == USER_ID
    assert captured["bank_txn_id"] == "1"
    assert captured["data"]["payload"]["amount"] == 10


@pytest.mark.asyncio
async def test_tinkoff_webhook_invalid(monkeypatch):
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            payload = {"event": ""}
            resp = await cl.post(f"/webhook/tinkoff/{USER_ID}", json=payload)
            assert resp.status_code == 422


class DummyConnector:
    name = "dummy"

    def __init__(self, user_id: str, token: TokenPair | None = None) -> None:
        pass

    async def fetch_accounts(self, token: TokenPair) -> list:
        return [1]


@pytest.mark.asyncio
async def test_status_disconnected(monkeypatch):
    async def fake_load(bank, user):
        return None

    monkeypatch.setattr("services.bank_bridge.app._load_token", fake_load)
    monkeypatch.setattr(
        "services.bank_bridge.app.get_connector", lambda b: DummyConnector
    )

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            resp = await cl.get(f"/status/tinkoff?user_id={USER_ID}")
            assert resp.status_code == 200
            assert resp.json() == {"status": "DISCONNECTED"}


@pytest.mark.asyncio
async def test_status_connected(monkeypatch):
    async def fake_load(bank, user):
        return TokenPair("at")

    class Conn(DummyConnector):
        async def fetch_accounts(self, token):
            return [1]

    monkeypatch.setattr("services.bank_bridge.app._load_token", fake_load)
    monkeypatch.setattr("services.bank_bridge.app.get_connector", lambda b: Conn)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            resp = await cl.get(f"/status/tinkoff?user_id={USER_ID}")
            assert resp.status_code == 200
            assert resp.json() == {"status": "CONNECTED"}


@pytest.mark.asyncio
async def test_status_error(monkeypatch):
    async def fake_load(bank, user):
        return TokenPair("at")

    class Conn(DummyConnector):
        async def fetch_accounts(self, token):
            raise RuntimeError("boom")

    monkeypatch.setattr("services.bank_bridge.app._load_token", fake_load)
    monkeypatch.setattr("services.bank_bridge.app.get_connector", lambda b: Conn)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            resp = await cl.get(f"/status/tinkoff?user_id={USER_ID}")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ERROR"}


@pytest.mark.asyncio
async def test_healthz_ok(monkeypatch):
    async def fake_get_producer():
        return object()

    class FakeVault:
        async def read(self, path):
            return ""

    monkeypatch.setattr(kafka, "get_producer", fake_get_producer)
    monkeypatch.setattr(vault, "get_vault_client", lambda: FakeVault())

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            resp = await cl.get("/healthz")
            assert resp.status_code == 200
            assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_healthz_error(monkeypatch):
    async def bad_producer():
        raise RuntimeError("kafka")

    class FakeVault:
        async def read(self, path):
            return ""

    monkeypatch.setattr(kafka, "get_producer", bad_producer)
    monkeypatch.setattr(vault, "get_vault_client", lambda: FakeVault())

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            resp = await cl.get("/healthz")
            assert resp.status_code == 200
            assert resp.json() == {"status": "degraded"}


@pytest.mark.asyncio
async def test_healthz_vault_error(monkeypatch):
    async def fake_get_producer():
        return object()

    class BadVault:
        async def read(self, path):
            raise RuntimeError("vault")

    monkeypatch.setattr(kafka, "get_producer", fake_get_producer)
    monkeypatch.setattr(vault, "get_vault_client", lambda: BadVault())

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            resp = await cl.get("/healthz")
            assert resp.status_code == 200
            assert resp.json() == {"status": "degraded"}


@pytest.mark.asyncio
async def test_duplicate_user_id(monkeypatch):
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            resp = await cl.get(
                f"/status/tinkoff?user_id={USER_ID}&user_id=00000000-0000-0000-0000-000000000002"
            )
            assert resp.status_code == 422
            assert isinstance(resp.json().get("detail"), list)
