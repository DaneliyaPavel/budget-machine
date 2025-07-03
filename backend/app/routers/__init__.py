"""Регистрация модулей маршрутов."""

from . import (
    analytics,
    banks,
    goals,
    tinkoff,
    recurring,
    tokens,
    jobs,
    oauth,
    push,
)

__all__ = [
    "goals",
    "analytics",
    "tinkoff",
    "banks",
    "recurring",
    "tokens",
    "jobs",
    "oauth",
    "push",
]
