from urllib.parse import urlencode
import os
import httpx

CLIENT_ID = os.getenv("BANK_BRIDGE_TINKOFF_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("BANK_BRIDGE_TINKOFF_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("BANK_BRIDGE_TINKOFF_REDIRECT_URI", "")

AUTH_URL = "https://id.tinkoff.ru/auth/authorize"
TOKEN_URL = "https://id.tinkoff.ru/auth/token"


def build_auth_url() -> str:
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email",
    }
    return AUTH_URL + "?" + urlencode(params)


async def exchange_code(code: str) -> str:
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(TOKEN_URL, data=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    email = data.get("email") or data.get("username")
    if not email:
        raise RuntimeError("No email in response")
    return email
