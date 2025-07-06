import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

schema_dir = Path("schemas/bank-bridge")


def load_schemas():
    for path in schema_dir.rglob("schema.json"):
        with open(path, "r", encoding="utf-8") as f:
            yield path.name, json.load(f)


def test_json_schemas_valid():
    for name, schema in load_schemas():
        Draft202012Validator.check_schema(schema)


@pytest.mark.asyncio
async def test_openapi_contract():
    schemathesis = pytest.importorskip("schemathesis")
    from asgi_lifespan import LifespanManager
    from httpx import AsyncClient, ASGITransport

    try:
        from backend.app.main import app
    except ModuleNotFoundError as exc:
        pytest.skip(str(exc))

    async with LifespanManager(app):
        schema = schemathesis.from_asgi("/openapi.json", app, base_url="http://test")

        @schema.parametrize()
        async def run(case):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await case.call_asgi()
            case.validate_response(response)

        await run()
