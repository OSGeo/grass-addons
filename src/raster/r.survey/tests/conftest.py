"""Fixtures for the r.survey tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


@pytest.fixture(scope="module")
def projected_session(tmp_path_factory):
    """Projected project (EPSG:3358) with a flat DEM and observer points."""
    project = tmp_path_factory.mktemp("r_survey") / "project"
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=100, s=0, e=100, w=0, res=10)
            tools.r_mapcalc(expression="dem = 100")
            tools.v_random(output="observers", npoints=2, seed=1)
        yield session


@pytest.fixture
def user_data(projected_session):
    """Isolated per-test mapset with user maps named like the temporary maps."""
    with TemporaryMapsetSession(env=projected_session.env) as session:
        with Tools(session=session) as tools:
            tools.r_mapcalc(expression="xx_roads = 1")
            tools.r_mapcalc(expression="zz_landuse = 1")
            tools.v_random(output="zzpnt_wells", npoints=2, seed=2)
        yield SimpleNamespace(env=session.env)
