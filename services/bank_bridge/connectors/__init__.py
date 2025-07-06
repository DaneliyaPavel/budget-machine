from __future__ import annotations

from importlib.metadata import entry_points
from typing import Type

from .base import BaseConnector


def _load_connectors() -> dict[str, Type[BaseConnector]]:
    eps = entry_points(group="bank_bridge.connectors")
    mapping: dict[str, Type[BaseConnector]] = {}
    for ep in eps:
        try:
            cls = ep.load()
        except Exception:  # pragma: no cover - broken entry
            continue
        if not issubclass(cls, BaseConnector):
            continue
        mapping[ep.name] = cls
    return mapping


CONNECTORS: dict[str, Type[BaseConnector]] = _load_connectors()


def get_connector(name: str) -> Type[BaseConnector]:
    try:
        return CONNECTORS[name]
    except KeyError:
        raise ValueError(f"Unknown connector: {name}")


__all__ = ["BaseConnector", "get_connector", "CONNECTORS"]
