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

# Stub grass modules only when they haven't been imported already (i.e. we are
# NOT running inside a real GRASS session).
if "grass" not in sys.modules:
    sys.modules["grass"] = MagicMock()
    sys.modules["grass.script"] = _gs_stub
    sys.modules["grass.exceptions"] = MagicMock()
    sys.modules["grass.tools"] = MagicMock()
    sys.modules["grass.script.setup"] = MagicMock()
    sys.modules["requests"] = MagicMock()


@pytest.fixture(scope="session")
def ssurgo_module():
    """Import and return the r.in.ssurgo module with GRASS stubs in place."""
    # Re-wire the module-level objects that run at import time.
    import importlib

    # Patch module-level code that touches GRASS at import time.
    _gs_stub.message = MagicMock()
    _gs_stub.warning = MagicMock()
    _gs_stub.fatal = MagicMock(side_effect=SystemExit)
    _gs_stub.debug = MagicMock()

    # Provide a fake Tools that returns a fake session string
    tools_mock = MagicMock()
    tools_mock.g_gisenv.return_value.text = "/tmp/grassdb/location/PERMANENT"
    sys.modules["grass.tools"].Tools.return_value = tools_mock

    # Now import (or reload) the module
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
