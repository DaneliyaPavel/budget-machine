import json
import subprocess
import socket
import time
from types import SimpleNamespace
import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from aiokafka import AIOKafkaConsumer
from jsonschema import Draft202012Validator

from services.bank_bridge.app import app, RAW_TOPIC, NORM_TOPIC, ERR_TOPIC
from services.bank_bridge import normalizer
from services.bank_bridge.connectors.tinkoff import TinkoffConnector

USER_ID = "00000000-0000-0000-0000-000000000001"

COMPOSE_FILE = "tests/bank_bridge/docker-compose.yml"

# Skip tests if Docker is not available or the daemon isn't running. This allows
# the suite to run in environments where Docker isn't installed or accessible.
docker_available = shutil.which("docker") is not None
if docker_available:
    try:
        docker_available = (
            subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode
            == 0
        )
    except Exception:
        docker_available = False

pytestmark = pytest.mark.skipif(
    not docker_available, reason="Docker is not available or not running"
)


@pytest.fixture(scope="module", autouse=True)
def compose_env():
    if not docker_available:
        pytest.skip("Docker is not available or not running")

    result = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d"], check=False
    )
    if result.returncode != 0:
        pytest.skip("Failed to start docker compose services")

    for port in (9092, 8081, 8200):
        for _ in range(30):
            sock = socket.socket()
            try:
                sock.settimeout(1)
                sock.connect(("localhost", port))
                sock.close()
                break
            except OSError:
                time.sleep(1)
        else:
            subprocess.run(
                ["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"], check=False
            )
            pytest.skip(f"Service on port {port} did not become available")

    yield

    subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, "down", "-v"], check=False)


@pytest_asyncio.fixture()
async def client(monkeypatch):
    monkeypatch.setenv("KAFKA_BROKER_URL", "localhost:9092")
    monkeypatch.setenv("BANK_BRIDGE_VAULT_URL", "http://localhost:8200")
    monkeypatch.setenv("BANK_BRIDGE_VAULT_TOKEN", "root")
    monkeypatch.setenv("BANK_NORM_TOPIC", NORM_TOPIC)
    monkeypatch.setenv("BANK_ERR_TOPIC", ERR_TOPIC)
    monkeypatch.setattr(TinkoffConnector, "BASE_URL", "http://localhost:8081/")

    async def spawn(coro):
        await coro

    app.scheduler = SimpleNamespace(spawn=spawn)

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cl:
            yield cl


@pytest.mark.asyncio
async def test_sync_cycle(client):
    raw_consumer = AIOKafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers="localhost:9092",
        group_id="test-group-raw",
        enable_auto_commit=True,
    )
    norm_consumer = AIOKafkaConsumer(
        NORM_TOPIC,
        bootstrap_servers="localhost:9092",
        group_id="test-group-norm",
        enable_auto_commit=True,
    )
    try:
        await raw_consumer.start()
        await norm_consumer.start()
    except Exception:
        pytest.skip("Kafka is not available")
    try:
        resp = await client.post(f"/sync/tinkoff?user_id={USER_ID}")
        assert resp.status_code == 200
        raw_msg = await raw_consumer.getone()
        raw_data = json.loads(raw_msg.value.decode())
        assert raw_data["bank_id"] == "tinkoff"
        await normalizer.process(raw_data)
        msg = await norm_consumer.getone()
        data = json.loads(msg.value.decode())
        schema_path = (
            Path(normalizer.BASE_DIR)
            / "schemas/bank-bridge/bank.norm/1.0.0/schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        Draft202012Validator(schema).validate(data)
        assert data["bank_id"] == "tinkoff"
        assert float(data["amount"]["value"]) == 100
        assert data["external_id"] == "1"
    finally:
        await raw_consumer.stop()
        await norm_consumer.stop()
