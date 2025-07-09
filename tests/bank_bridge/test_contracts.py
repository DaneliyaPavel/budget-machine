import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from services.bank_bridge.app import app

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


@schema.parametrize()
def test_openapi_contract(case):
    response = case.call_asgi()
    case.validate_response(response)
