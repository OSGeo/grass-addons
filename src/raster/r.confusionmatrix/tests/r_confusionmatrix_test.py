"""Tests for the computational region handling of r.confusionmatrix.

To rasterize a vector reference, r.confusionmatrix sets the region to the
classification map. These tests check that the user's region is not affected
by that, neither after a successful run nor after a failing one.
"""

import os

import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError
from grass.tools import Tools

USER_REGION = {"n": 100, "s": 0, "e": 100, "w": 0, "res": 10}


@pytest.fixture
def session(tmp_path):
    """Project with a classification raster and a reference vector.

    The classification map is created in a region which is deliberately
    different from the one left active, so that a region change made by the
    module is easy to detect.
    """
    project = tmp_path / "project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=20, s=0, e=20, w=0, res=1)
            tools.r_mapcalc(expression="classification = if(col() <= 10, 1, 2)")
            tools.v_mkgrid(map="reference", grid=[1, 2])
            tools.g_region(**USER_REGION)
        yield session


def test_region_kept_after_successful_run(session):
    """The user's region is the same after a run with a vector reference"""
    tools = Tools(session=session)
    before = gs.region(env=session.env)
    tools.r_confusionmatrix(
        classification="classification", vector_reference="reference", column="cat"
    )
    assert gs.region(env=session.env) == before


def test_region_kept_when_rasterization_fails(session):
    """The user's region is the same after v.to.rast fails on a wrong column"""
    tools = Tools(session=session)
    before = gs.region(env=session.env)
    with pytest.raises(CalledModuleError):
        tools.r_confusionmatrix(
            classification="classification",
            vector_reference="reference",
            column="does_not_exist",
        )
    assert gs.region(env=session.env) == before


def test_no_region_left_behind_when_rasterization_fails(session):
    """No saved region remains in the mapset after v.to.rast fails"""
    tools = Tools(session=session)
    with pytest.raises(CalledModuleError):
        tools.r_confusionmatrix(
            classification="classification",
            vector_reference="reference",
            column="does_not_exist",
        )
    assert gs.read_command("g.list", type="region", env=session.env) == ""
