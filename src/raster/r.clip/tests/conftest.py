"""Fixtures for the r.clip tests."""

from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession


def dataset_session(tmp_path, name, *, epsg, extent, res):
    """Create a project with input raster ``name`` and yield a handle to it.

    The raster is a 10x10 grid of ``col()`` values in PERMANENT; each test runs
    in its own temporary mapset, reached through the yielded ``env``.
    """
    project = tmp_path / "project"
    gs.create_project(project, epsg=epsg)
    with gs.setup.init(project):
        gs.run_command("g.region", res=res, **extent)
        gs.mapcalc(f"{name} = col()")
        with TemporaryMapsetSession() as session:
            yield SimpleNamespace(env=session.env, input=name, res=res)


@pytest.fixture
def clip_ll(tmp_path):
    """WGS84 lat/lon project (EPSG:4326), 10x10 raster at 1 degree over 0..10."""
    yield from dataset_session(
        tmp_path,
        "input_map",
        epsg="4326",
        extent={"n": 10, "s": 0, "e": 10, "w": 0},
        res=1,
    )


@pytest.fixture
def clip_utm(tmp_path):
    """UTM 33N project (EPSG:32633), 10x10 raster at resolution 100 over 0..1000."""
    yield from dataset_session(
        tmp_path,
        "input_utm",
        epsg="32633",
        extent={"n": 1000, "s": 0, "e": 1000, "w": 0},
        res=100,
    )
