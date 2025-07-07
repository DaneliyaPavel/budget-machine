import json
import subprocess
from types import SimpleNamespace

import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from aiokafka import AIOKafkaConsumer

from services.bank_bridge.app import app
from services.bank_bridge.connectors.tinkoff import TinkoffConnector
from services.bank_bridge.connectors.base import Account, RawTxn, TokenPair

COMPOSE_FILE = "tests/bank_bridge/docker-compose.yml"

@pytest.fixture(scope="module", autouse=True)
def compose_env():
    subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, "up", "-d"], check=False)
    yield
    subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"], check=False)

@pytest.fixture(scope="module")
async def client(monkeypatch):
    monkeypatch.setenv("KAFKA_BROKER_URL", "localhost:9092")

    async def fake_load(bank: str, user_id: str) -> TokenPair:
        return TokenPair(access_token="x")

    monkeypatch.setattr("services.bank_bridge.app._load_token", fake_load)

    async def fetch_accounts(self, token):
        return [Account(id="acc1")]

    async def fetch_txns(self, token, account, start, end):
        yield RawTxn({
            "id": 1,
            "amount": 100,
            "date": "2024-01-01T00:00:00",
            "account_id": account.id,
        })

    monkeypatch.setattr(TinkoffConnector, "fetch_accounts", fetch_accounts)
    monkeypatch.setattr(TinkoffConnector, "fetch_txns", fetch_txns)

    async def spawn(coro):
        await coro

    app.scheduler = SimpleNamespace(spawn=spawn)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            yield cl

@pytest.mark.asyncio
async def test_sync_cycle(client):
    consumer = AIOKafkaConsumer(
        "bank.norm",
        bootstrap_servers="localhost:9092",
        group_id="test-group",
        enable_auto_commit=True,
    )
    await consumer.start()
    try:
        resp = await client.post("/sync/tinkoff")
        assert resp.status_code == 200
        msg = await consumer.getone()
        data = json.loads(msg.value.decode())
        assert data["postings"][0]["amount"] == 100
        assert data["external_id"] == "1"
    finally:
        await consumer.stop()
