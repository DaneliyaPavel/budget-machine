"""Получение курсов валют через ЦБ РФ."""

from datetime import datetime, timezone
from typing import Dict

import httpx
from httpx import HTTPError

_CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
_rates: Dict[str, float] = {"RUB": 1.0}
_last_update: datetime | None = None


async def get_rate(code: str) -> float:
    """Вернуть курс валюты к рублю."""
    global _rates, _last_update
    now = datetime.now(timezone.utc)
    if not _last_update or (now - _last_update).seconds > 3600:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(_CBR_URL, timeout=10)
                resp.raise_for_status()
                data = resp.json()
        except HTTPError:
            # при ошибке используем закешированные значения
            data = None
        if data:
            _rates = {"RUB": 1.0}
            for k, v in data["Valute"].items():
                _rates[k] = float(v["Value"])
            _last_update = now
    return _rates.get(code, 1.0)


async def get_rates(base: str = "RUB") -> Dict[str, float]:
    """Вернуть словарь курсов относительно выбранной валюты."""
    base = base.upper()
    await get_rate("RUB")
    base_rate = _rates.get(base, 1.0)
    return {c: r / base_rate for c, r in _rates.items()}


async def convert(amount: float, source: str, target: str) -> float:
    """Перевести сумму из одной валюты в другую."""
    rate_from = await get_rate(source.upper())
    rate_to = await get_rate(target.upper())
    return amount * rate_from / rate_to
