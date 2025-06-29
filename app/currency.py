"""Получение курсов валют через ЦБ РФ."""

from datetime import datetime
from typing import Dict

import httpx
from httpx import HTTPError

_CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
_rates: Dict[str, float] = {"RUB": 1.0}
_last_update: datetime | None = None

async def get_rate(code: str) -> float:
    """Вернуть курс валюты к рублю."""
    global _rates, _last_update
    now = datetime.utcnow()
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
