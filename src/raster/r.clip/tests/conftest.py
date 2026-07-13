"""Fixtures for the r.clip tests.

Creates a temporary XY project holding a single input raster and a known
computational region, so individual tests can re-clip it under different
regions and flags without rebuilding data each time.
"""

from types import SimpleNamespace

import pytest

import grass.script as gs


@pytest.fixture
def clip_dataset(tmp_path_factory):
    """Set up a temporary project with one input raster.

    ``input_map`` is a 10x10 grid at resolution 10 covering 0..100 in both
    directions, where each cell value equals its column number (1..10). The
    fixed resolution and alignment make it straightforward to check that
    r.clip preserves (or, with ``-r``, changes) the cell size and that
    clipped values match the source.
    """
    tmp_path = tmp_path_factory.mktemp("clip_project")
    location = "test"
    gs.core._create_location_xy(tmp_path, location)  # pylint: disable=protected-access
    with gs.setup.init(tmp_path / location):
        # Full extent of the input raster: resolution 10 -> 10x10 cells.
        gs.run_command("g.region", n=100, s=0, e=100, w=0, res=10)
        input_map = "input_map"
        gs.mapcalc(f"{input_map} = col()")

        yield SimpleNamespace(
            input=input_map,
            res=10,
            north=100,
            south=0,
            east=100,
            west=0,
        )


@pytest.fixture
def clip_dataset_utm(tmp_path_factory):
    """Set up a temporary projected (metre) project with one input raster.

    Uses WGS84 / UTM zone 33N (EPSG:32633) so cell sizes are real metres, to
    check that r.clip behaves the same way in a projected CRS as in XY.
    ``input_utm`` is a 10x10 grid at resolution 100 covering 0..1000.
    """
    tmp_path = tmp_path_factory.mktemp("clip_utm")
    location = "utm"
    gs.create_project(tmp_path, location, epsg="32633")
    with gs.setup.init(tmp_path / location):
        gs.run_command("g.region", n=1000, s=0, e=1000, w=0, res=100)
        input_map = "input_utm"
        gs.mapcalc(f"{input_map} = col()")

        yield SimpleNamespace(input=input_map, res=100)
