"""Fixtures for the i.image.bathymetry tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


@pytest.fixture(scope="module")
def xy_session(tmp_path_factory):
    """XY project with a 3x3 band raster in PERMANENT."""
    project = tmp_path_factory.mktemp("i_image_bathymetry") / "project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=3, s=0, e=3, w=0, res=1)
            tools.r_mapcalc(expression="band = row() + col()")
        yield session


@pytest.fixture
def user_data(xy_session):
    """Isolated per-test mapset with user data having "tmp" in the names."""
    with TemporaryMapsetSession(env=xy_session.env) as session:
        with Tools(session=session) as tools:
            tools.r_mapcalc(expression="tmp_slope = 1")
            tools.v_random(output="tmp_points", npoints=3, seed=1, column="depth")
            tools.g_region(save="tmp_extent")
            tools.i_group(group="s2_tmp", input="band@PERMANENT")
        yield SimpleNamespace(env=session.env)
