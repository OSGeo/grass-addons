"""Fixtures for the r.clip tests.

Each fixture builds a throwaway project with a single input raster, so tests
can re-clip it under different computational regions and flags.
"""

from types import SimpleNamespace

import pytest

import grass.script as gs


def _clip_dataset(tmp_path, name, *, epsg, extent, res):
    """Create a project with one input raster and yield a handle to it.

    The input raster is a 10x10 grid where each cell value equals its column
    number, which makes clipped values easy to check. *extent* is passed to
    ``g.region`` as its ``n``/``s``/``e``/``w`` keyword arguments. Yields a
    namespace with the raster ``input`` name and its ``res`` (resolution).
    """
    gs.create_project(tmp_path, "test", epsg=epsg)
    with gs.setup.init(tmp_path / "test"):
        gs.run_command("g.region", res=res, **extent)
        gs.mapcalc(f"{name} = col()")
        yield SimpleNamespace(input=name, res=res)


@pytest.fixture
def clip_dataset(tmp_path_factory):
    """XY project: a 10x10 raster at resolution 10 covering 0..100."""
    yield from _clip_dataset(
        tmp_path_factory.mktemp("clip_xy"),
        "input_map",
        epsg=None,
        extent={"n": 100, "s": 0, "e": 100, "w": 0},
        res=10,
    )


@pytest.fixture
def clip_dataset_utm(tmp_path_factory):
    """Projected project: a 10x10 raster at resolution 100 covering 0..1000.

    Uses WGS84 / UTM zone 33N (EPSG:32633) so cell sizes are real metres, to
    check that r.clip behaves the same way in a projected CRS as in XY.
    """
    yield from _clip_dataset(
        tmp_path_factory.mktemp("clip_utm"),
        "input_utm",
        epsg="32633",
        extent={"n": 1000, "s": 0, "e": 1000, "w": 0},
        res=100,
    )
