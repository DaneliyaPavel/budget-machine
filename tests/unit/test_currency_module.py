import pytest
from datetime import datetime, timedelta, timezone
import httpx

from backend.app import currency


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class DummyClient:
    def __init__(self, data):
        self._data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url, timeout=10):
        return DummyResponse(self._data)


@pytest.mark.asyncio
async def test_get_rate_refresh(monkeypatch):
    data = {"Valute": {"USD": {"Value": 60.0}}}
    monkeypatch.setattr(httpx, "AsyncClient", lambda: DummyClient(data))

    currency._last_update = datetime.now(timezone.utc) - timedelta(days=1)
    currency._rates = {"RUB": 1.0, "USD": 50.0}

    rate = await currency.get_rate("USD")
    assert rate == 60.0
    assert currency._rates["USD"] == 60.0
