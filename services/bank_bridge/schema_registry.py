import json
import os
import logging
from pathlib import Path

import httpx

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
GROUP = os.getenv("SCHEMA_REGISTRY_GROUP", "bank-bridge")

BASE_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = BASE_DIR / "schemas" / "bank-bridge"

logger = logging.getLogger(__name__)


async def _register(name: str, version: str, schema: dict) -> None:
    artifact_id = f"{name}-{version}"
    url = f"{SCHEMA_REGISTRY_URL}/apis/registry/v2/groups/{GROUP}/artifacts"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={"X-Registry-ArtifactId": artifact_id},
            json=schema,
        )
        if resp.status_code not in (200, 204, 409):
            resp.raise_for_status()


async def register_all() -> None:
    for path in SCHEMA_DIR.rglob("schema.json"):
        name = path.parent.parent.name
        version = path.parent.name
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        try:
            await _register(name, version, schema)
        except Exception as exc:  # pragma: no cover - network issues
            logger.warning("failed to register schema: %s", exc)
