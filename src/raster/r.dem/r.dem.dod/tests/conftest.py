import os

import pytest

import grass.script as gs
from grass.tools import Tools

PLANE = "100.0 + 0.2 * x() + 0.1 * y()"
CURVE = "100.0 + 0.01 * (x() - 20) ^ 2 + 0.01 * (y() - 20) ^ 2"


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary GRASS project with a planar reference DEM, the same plane
    plus a +2 m block, and copies of the plane on a shifted grid and on a
    finer grid.
    """
    tmp = tmp_path_factory.mktemp("rdemdod")
    project = os.path.join(tmp, "dod")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        tools = Tools(session=session)
        tools.g_region(n=40, s=0, e=40, w=0, res=1)
        tools.r_mapcalc(expression=f"dem_pre = {PLANE}")
        tools.r_mapcalc(
            expression=(
                f"dem_post = {PLANE} "
                "+ if(row() >= 10 && row() <= 20 && col() >= 10 && col() <= 20,"
                " 2.0, 0.0)"
            )
        )
        tools.r_mapcalc(expression=f"curve_pre = {CURVE}")
        # The same surfaces on a grid offset by half a cell east and a quarter
        # cell north, the plane offset 5 micrometers and 1 mm east (below and
        # above the grid match tolerance), then on a grid twice as fine.
        tools.g_region(n=40.25, s=0.25, e=40.5, w=0.5, res=1)
        tools.r_mapcalc(expression=f"dem_shift = {PLANE}")
        tools.r_mapcalc(expression=f"curve_shift = {CURVE}")
        tools.g_region(n=40, s=0, e=40.000005, w=0.000005, res=1)
        tools.r_mapcalc(expression=f"dem_5um = {PLANE}")
        tools.g_region(n=40, s=0, e=40.001, w=0.001, res=1)
        tools.r_mapcalc(expression=f"dem_1mm = {PLANE}")
        tools.g_region(n=40, s=0, e=40, w=0, res=0.5)
        tools.r_mapcalc(expression=f"dem_fine = {PLANE}")
        tools.g_region(n=40, s=0, e=40, w=0, res=1)
        yield session


@pytest.fixture
def tools(session):
    # Capture stderr and always return a result so tests can check warnings.
    return Tools(session=session, capture_stderr=True, consistent_return_value=True)
