"""Test r.local.relief in a latitude-longitude project"""

import os

import pytest

import grass.script as gs
from grass.tools import Tools


@pytest.fixture
def latlon_session(tmp_path):
    """Latitude-longitude project with a synthetic wavy elevation raster"""
    project = tmp_path / "project"
    gs.create_project(project, epsg="4326")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        tools = Tools(session=session)
        tools.g_region(n=36, s=35.95, w=-79, e=-78.95, res="0:00:03")
        tools.r_mapcalc(
            expression=(
                "elevation = 100 + 20 * sin(row() * 12) * cos(col() * 9)"
                " + 3 * sin(row() * 47 + col() * 31)"
            )
        )
        yield session


def test_bspline_latlon(latlon_session):
    """Check that -v gives a full local relief raster when map units are degrees"""
    tools = Tools(session=latlon_session)
    tools.r_local_relief(
        input="elevation", output="local_relief", neighborhood_size=5, flags="v"
    )
    stats = tools.r_univar(map="local_relief", format="json")
    assert stats["null_cells"] == 0
    assert stats["min"] < 0 < stats["max"]
