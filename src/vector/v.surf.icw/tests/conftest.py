"""Fixtures for the v.surf.icw tests."""

import os
from types import SimpleNamespace
import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


@pytest.fixture(scope="module")
def icw_session(tmp_path_factory):
    """Build a project with a cost raster and vector points in PERMANENT."""
    project = tmp_path_factory.mktemp("v_surf_icw") / "project"
    gs.create_project(project, epsg="3358")  # Metric NAD83 / North Carolina

    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            # Set a 10x10 cell region (100m x 100m, 10m resolution)
            tools.g_region(s=0, n=100, w=0, e=100, res=10)

            # Create a uniform cost raster map (all cells = 1)
            tools.r_mapcalc(expression="cost_raster = 1")

            # Create two seed points: (25, 25) with value 10.0, and (75, 75) with value 100.0
            # Formatted as: Easting | Northing | Value
            ascii_file = tmp_path_factory.mktemp("data") / "points.txt"
            ascii_file.write_text("25|25|10.0\n75|75|100.0\n")

            # Import ascii points and populate the attribute table
            tools.v_in_ascii(
                input=str(ascii_file),
                output="seed_points",
                separator="pipe",
                columns="x double, y double, val double",
            )
        yield session


@pytest.fixture
def icw(icw_session):
    """Isolated per-test mapset + Tools handle."""
    with TemporaryMapsetSession(env=icw_session.env) as session:
        with Tools(session=session) as tools:
            # Re-align region for the temporary session
            tools.g_region(s=0, n=100, w=0, e=100, res=10)
            yield SimpleNamespace(tools=tools, env=session.env)
