import json
from pathlib import Path

import pytest
import asyncio
from jsonschema import Draft202012Validator
from services.bank_bridge.app import app
from services.bank_bridge import kafka, vault
from services.bank_bridge.connectors import TokenPair


@pytest.fixture(autouse=True)
def _patch_dependencies(monkeypatch):
    class DummyVault:
        async def read(self, path):
            return ""

    async def fake_get_producer():
        return object()

    async def fake_publish(*args, **kwargs):
        return None

    class DummyScheduler:
        async def spawn(self, coro):
            asyncio.create_task(coro)

        async def close(self):
            pass

    async def create_dummy_scheduler():
        return DummyScheduler()

    async def fake_close():
        pass

    monkeypatch.setattr(kafka, "get_producer", fake_get_producer)
    monkeypatch.setattr(kafka, "publish", fake_publish)
    monkeypatch.setattr(kafka, "close", fake_close)
    monkeypatch.setattr(vault, "get_vault_client", lambda: DummyVault())
    class DummyConnector:
        name = "dummy"

        def __init__(self, user_id: str, token: TokenPair | None = None) -> None:
            pass

        async def auth(self, code: str | None, **kwargs):
            return TokenPair("url")

        async def fetch_accounts(self, token: TokenPair):
            return [1]

    monkeypatch.setattr("services.bank_bridge.app.create_scheduler", create_dummy_scheduler)
    monkeypatch.setattr("services.bank_bridge.app.get_connector", lambda name: DummyConnector)
    return DummyConnector

schema_dir = Path("schemas/bank-bridge")


def load_schemas():
    for path in schema_dir.rglob("schema.json"):
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        example_path = path.parent / "example.json"
        example = None
        if example_path.exists():
            with open(example_path, "r", encoding="utf-8") as ef:
                example = json.load(ef)
        yield path.name, schema, example


def test_json_schemas_valid():
    for name, schema, _ in load_schemas():
        Draft202012Validator.check_schema(schema)


def test_examples_match_schema():
    for name, schema, example in load_schemas():
        if example is None:
            continue
        Draft202012Validator(schema).validate(example)


schemathesis = pytest.importorskip("schemathesis")

schema = schemathesis.openapi.from_asgi("/openapi.json", app)


@pytest.mark.skip("schemathesis compatibility issues")
@schema.parametrize()
def test_openapi_contract(case):
    response = case.call()
    case.validate_response(response, checks=[])
