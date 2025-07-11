from __future__ import annotations

from importlib.metadata import entry_points
from typing import Type

from .base import BaseConnector, TokenPair, AuthError


def _load_connectors() -> dict[str, Type[BaseConnector]]:
    """Load available connectors.

    When the package is installed, connectors are discovered via entry points.
    However, in development and CI the project is often used without
    installation and thus no entry points are registered.  In this case fall
    back to importing built-in connectors directly.
    """

    mapping: dict[str, Type[BaseConnector]] = {}

    try:
        eps = entry_points(group="bank_bridge.connectors")
    except Exception:  # pragma: no cover - environment issues
        eps = []

    for ep in eps:
        try:
            cls = ep.load()
        except Exception:  # pragma: no cover - broken entry
            continue
        if not issubclass(cls, BaseConnector):
            continue
        mapping[ep.name] = cls

    if not mapping:
        from .tinkoff import TinkoffConnector
        from .sber import SberConnector
        from .gazprom import GazpromConnector
        from .alfa import AlfaConnector
        from .vtb import VTBConnector

        mapping.update(
            {
                "tinkoff": TinkoffConnector,
                "sber": SberConnector,
                "gazprom": GazpromConnector,
                "alfa": AlfaConnector,
                "vtb": VTBConnector,
            }
        )

    return mapping


CONNECTORS: dict[str, Type[BaseConnector]] = _load_connectors()


def get_connector(name: str) -> Type[BaseConnector]:
    try:
        return CONNECTORS[name]
    except KeyError:
        raise ValueError(f"Unknown connector: {name}")


__all__ = ["BaseConnector", "TokenPair", "AuthError", "get_connector", "CONNECTORS"]
