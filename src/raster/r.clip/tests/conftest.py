"""Fixtures for the r.clip tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


def base_session(tmp_path_factory, name, *, epsg, extent, res):
    """Build a project with input raster ``name`` once per module.

    The raster is a 10x10 grid of ``col()`` values in PERMANENT.
    """
    project = tmp_path_factory.mktemp("r_clip") / "project"
    gs.create_project(project, epsg=epsg)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(res=res, **extent)
            tools.r_mapcalc(expression=f"{name} = col()")
        yield session


@pytest.fixture(scope="module")
def ll_session(tmp_path_factory):
    """WGS84 lat/lon project (EPSG:4326), 10x10 raster at 1 degree over 0..10."""
    yield from base_session(
        tmp_path_factory,
        "input_map",
        epsg="4326",
        extent={"n": 10, "s": 0, "e": 10, "w": 0},
        res=1,
    )


@pytest.fixture(scope="module")
def utm_session(tmp_path_factory):
    """UTM 33N project (EPSG:32633), 10x10 raster at resolution 100 over 0..1000."""
    yield from base_session(
        tmp_path_factory,
        "input_utm",
        epsg="32633",
        extent={"n": 1000, "s": 0, "e": 1000, "w": 0},
        res=100,
    )


def clip_fixture(module_session, name, res):
    """Isolated per-test mapset + Tools handle over a module-scoped base session."""
    with TemporaryMapsetSession(env=module_session.env) as session:
        with Tools(session=session) as tools:
            yield SimpleNamespace(tools=tools, input=name, res=res)


@pytest.fixture
def clip_ll(ll_session):
    yield from clip_fixture(ll_session, "input_map", res=1)


@pytest.fixture
def clip_utm(utm_session):
    yield from clip_fixture(utm_session, "input_utm", res=100)
