"""Коннекторы к различным банкам."""

from .base import BankConnector
from .tinkoff import TinkoffConnector
from .sber import SberConnector
from .gazprom import GazpromConnector


def get_connector(name: str, token: str) -> BankConnector:
    """Получить коннектор по названию банка."""
    name = name.lower()
    if name in ("tinkoff", "тинькофф"):
        return TinkoffConnector(token)
    if name in ("sber", "sberbank", "сбер", "сбербанк"):
        return SberConnector(token)
    if name in ("gazprom", "gazprombank", "газпром", "газпромбанк"):
        return GazpromConnector(token)
    raise ValueError("Неизвестный банк")
