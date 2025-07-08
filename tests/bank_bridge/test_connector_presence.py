import tomllib

from importlib import import_module

from services.bank_bridge.connectors.base import BaseConnector


def _load_connector(module_name: str, class_name: str) -> type[BaseConnector]:
    module = import_module(module_name)
    cls = getattr(module, class_name)
    assert issubclass(cls, BaseConnector)
    return cls


def test_alfa_connector_available():
    _load_connector("services.bank_bridge.connectors.alfa", "AlfaConnector")


def test_vtb_connector_available():
    _load_connector("services.bank_bridge.connectors.vtb", "VTBConnector")


def test_pyproject_registration():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    connectors = data["project"]["entry-points"]["bank_bridge.connectors"]
    assert connectors["alfa"].endswith("AlfaConnector")
    assert connectors["vtb"].endswith("VTBConnector")
