import importlib

import mindtwin

SUBPACKAGES = ["core", "data", "knowledge", "cognition", "agent", "api"]


def test_version():
    assert mindtwin.__version__ == "0.0.1"


def test_subpackages_import():
    for name in SUBPACKAGES:
        assert importlib.import_module(f"mindtwin.{name}") is not None
