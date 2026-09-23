"""Fixtures for the r.surf.volcano tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


@pytest.fixture(scope="module")
def volcano_session(tmp_path_factory):
    """Project setup for r.surf.volcano tests."""
    project = tmp_path_factory.mktemp("r_surf_volcano") / "project"

    gs.create_project(project, epsg="3358")

    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=5120, s=0, w=0, e=5120, res=10)
        yield session


@pytest.fixture
def volcano(volcano_session):
    """Isolated per-test mapset + Tools handle."""
    with TemporaryMapsetSession(env=volcano_session.env) as session:
        with Tools(session=session) as tools:
            # Align region
            tools.g_region(n=5120, s=0, w=0, e=5120, res=10)
            yield SimpleNamespace(tools=tools, env=session.env)
