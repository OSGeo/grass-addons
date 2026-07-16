"""Shared pytest fixtures for r.in.ssurgo tests."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Ensure the addon module directory is importable
# ---------------------------------------------------------------------------
MODULE_DIR = str(Path(__file__).resolve().parent.parent)
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# ---------------------------------------------------------------------------
# Stub heavy external dependencies that are NOT available in a test-only
# environment (grass.script, grass.tools, etc.) so we can import the module's
# pure-Python helpers without a running GRASS session.
# ---------------------------------------------------------------------------

# Minimal grass.script stub
_gs_stub = MagicMock()
_gs_stub.parser.return_value = ({}, {})
_gs_stub.region.return_value = {
    "w": -79.0,
    "s": 35.0,
    "e": -78.0,
    "n": 36.0,
    "nsres": 30,
    "ewres": 30,
}

# The stubs below are installed in sys.modules only while the addon module is
# imported (see the ssurgo_module fixture) and removed immediately after, so
# they cannot leak into other addons' tests that share the same process (e.g. a
# repo-wide pytest run).


@pytest.fixture(scope="session")
def ssurgo_module():
    """Import and return the r.in.ssurgo module with GRASS stubs in place.

    These are unit tests of the module's pure-Python helpers, so the import
    always runs against stubs rather than a real GRASS session. The stubs are
    present in sys.modules only for the duration of the import; the imported
    module keeps its own references, so the originals are restored right after
    to avoid leaking into other test suites that share the process.
    """
    import importlib

    # Configure the grass.script stub used during import.
    _gs_stub.message = MagicMock()
    _gs_stub.warning = MagicMock()
    _gs_stub.fatal = MagicMock(side_effect=SystemExit)
    _gs_stub.debug = MagicMock()

    # Provide a fake Tools that returns a fake session string.
    tools_mock = MagicMock()
    tools_mock.g_gisenv.return_value.text = "/tmp/grassdb/location/PERMANENT"

    stubs = {
        "grass": MagicMock(),
        "grass.script": _gs_stub,
        "grass.exceptions": MagicMock(),
        "grass.tools": MagicMock(),
        "grass.script.setup": MagicMock(),
        "requests": MagicMock(),
    }
    stubs["grass.tools"].Tools.return_value = tools_mock

    saved = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    try:
        if "r.in.ssurgo" in sys.modules:
            mod = importlib.reload(sys.modules["r.in.ssurgo"])
        else:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "r.in.ssurgo",
                Path(__file__).resolve().parent.parent / "r.in.ssurgo.py",
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules["r.in.ssurgo"] = mod
            spec.loader.exec_module(mod)
    finally:
        for name, original in saved.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original
    return mod


# ---------------------------------------------------------------------------
# Convenient re-exports of the most commonly needed classes / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def SDAClient(ssurgo_module):
    """Return the SDAClient class."""
    return ssurgo_module.SDAClient


@pytest.fixture
def SoilAggMethod(ssurgo_module):
    """Return the SoilAggMethod enum."""
    return ssurgo_module.SoilAggMethod
