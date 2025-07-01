"""Коннекторы к различным банкам."""

from .base import BankConnector
from .tinkoff import TinkoffConnector
from .sber import SberConnector
from .gazprom import GazpromConnector


def get_connector(name: str, user_id: int, token: str | None = None) -> BankConnector:
    """Получить коннектор по названию банка."""
    name = name.lower()
    if name in ("tinkoff", "тинькофф"):
        return TinkoffConnector(user_id, token)
    if name in ("sber", "sberbank", "сбер", "сбербанк"):
        return SberConnector(user_id, token)
    if name in ("gazprom", "gazprombank", "газпром", "газпромбанк"):
        return GazpromConnector(user_id, token)
    raise ValueError("Неизвестный банк")
