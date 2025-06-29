"""Регистрация модулей маршрутов."""

from . import categories, transactions, goals, users, analytics, tinkoff, banks

__all__ = [
    "categories",
    "transactions",
    "goals",
    "users",
    "analytics",
    "tinkoff",
    "banks",
]
from . import categories, transactions, goals, users, analytics

__all__ = ["categories", "transactions", "goals", "users", "analytics"]
from . import categories, transactions, goals, users

__all__ = ["categories", "transactions", "goals", "users"]
