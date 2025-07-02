import importlib
import sys

_backend_app = importlib.import_module("backend.app")
sys.modules[__name__] = _backend_app
