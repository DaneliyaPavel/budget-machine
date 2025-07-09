import os
from functools import lru_cache

import httpx


class VaultClient:
    """Minimal async Vault client for KV engine."""

    def __init__(self, url: str | None = None, token: str | None = None) -> None:
        self.url = url or os.getenv("BANK_BRIDGE_VAULT_URL", "http://localhost:8200")
        self.token = token or os.getenv("BANK_BRIDGE_VAULT_TOKEN", "root")
        self.headers = {"X-Vault-Token": self.token}

    async def read(self, path: str) -> str | None:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.url}/v1/secret/{path}",
                    headers=self.headers,
                    timeout=5,
                )
            except httpx.HTTPError:
                return None
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("value")
            return None

    async def write(self, path: str, value: str) -> None:
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.url}/v1/secret/{path}",
                    headers=self.headers,
                    json={"value": value},
                    timeout=5,
                )
            except httpx.HTTPError:
                return

    async def delete(self, path: str) -> None:
        async with httpx.AsyncClient() as client:
            try:
                await client.delete(
                    f"{self.url}/v1/secret/{path}",
                    headers=self.headers,
                    timeout=5,
                )
            except httpx.HTTPError:
                return


@lru_cache
def get_vault_client() -> VaultClient:
    return VaultClient()
