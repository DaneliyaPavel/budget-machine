"""Регистрация модулей маршрутов."""

from . import analytics, banks, categories, goals, tinkoff, transactions, users, recurring, accounts

__all__ = [
    "categories",
    "transactions",
    "goals",
    "users",
    "analytics",
    "tinkoff",
    "banks",
    "recurring",
    "accounts",
]
