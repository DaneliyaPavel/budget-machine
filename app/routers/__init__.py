"""Регистрация модулей маршрутов."""

from . import analytics, banks, categories, goals, tinkoff, transactions, users

__all__ = [
    "categories",
    "transactions",
    "goals",
    "users",
    "analytics",
    "tinkoff",
    "banks",
]
