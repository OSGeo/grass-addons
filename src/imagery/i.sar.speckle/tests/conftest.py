"""Fixtures for the i.sar.speckle tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


@pytest.fixture(scope="module")
def xy_session(tmp_path_factory):
    """XY project with a 10x10 random image in PERMANENT."""
    project = tmp_path_factory.mktemp("i_sar_speckle") / "project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=10, s=0, e=10, w=0, res=1)
            tools.r_mapcalc(expression="sar = rand(1.0, 10.0)", seed=1)
        yield session


@pytest.fixture
def user_data(xy_session):
    """Isolated per-test mapset with user rasters whose names start with "tmp"."""
    with TemporaryMapsetSession(env=xy_session.env) as session:
        with Tools(session=session) as tools:
            tools.r_mapcalc(expression="tmp_slope = 1")
            tools.r_mapcalc(expression="tmpdem = 2")
            yield SimpleNamespace(tools=tools, env=session.env)
