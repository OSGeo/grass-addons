"""Fixtures for the v.gsflow.grid tests."""

import os

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools

# Square basin from (100, 100) to (200, 200), in the standard vector ASCII format
BASIN = """\
B 5
 100 100
 100 200
 200 200
 200 100
 100 100
C 1 1
 150 150
1 1
"""


@pytest.fixture(scope="module")
def module_session(tmp_path_factory):
    """Build an empty UTM project once per module."""
    project = tmp_path_factory.mktemp("v_gsflow_grid") / "project"
    gs.create_project(project, epsg="32633")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        yield session


@pytest.fixture
def grid_tools(module_session, tmp_path):
    """Tools in a fresh mapset with the basin and pour point, but no DEM yet.

    The region covers 0..300 with 10 m cells. The pour point is inside the
    basin, just above its southern edge. The tool changes the pour point map,
    so everything is created in the per-test mapset.
    """
    with TemporaryMapsetSession(env=module_session.env) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=300, s=0, e=300, w=0, res=10)
            basin_file = tmp_path / "basin.txt"
            basin_file.write_text(BASIN)
            tools.v_in_ascii(
                input=str(basin_file), output="basin", format="standard", flags="n"
            )
            pour_point_file = tmp_path / "pour_point.txt"
            pour_point_file.write_text("155|105\n")
            tools.v_in_ascii(input=str(pour_point_file), output="pp", separator="pipe")
            yield tools
