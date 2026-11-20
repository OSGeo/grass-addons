import os

import pytest

import grass.script as gs
from grass.tools import Tools


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary project with a 20x20 region at 1 m resolution.

    before: constant 100 with one null cell at row 1, col 1
    after: constant 200 with the same null cell
    square_big: 1 inside rows 5-14 and cols 5-14, else 0
    square_small: 1 inside rows 8-11 and cols 8-11, else 0
    dem: elevation increasing with the row number (higher to the south)
    """
    tmp = tmp_path_factory.mktemp("ranimmorph")
    project = os.path.join(tmp, "morph")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        tools = Tools(session=session)
        tools.g_region(n=20, s=0, e=20, w=0, res=1)
        tools.r_mapcalc(
            expression="before = if(row() == 1 && col() == 1, null(), 100.0)"
        )
        tools.r_mapcalc(
            expression="after = if(row() == 1 && col() == 1, null(), 200.0)"
        )
        tools.r_mapcalc(
            expression=(
                "square_big = if(row() >= 5 && row() <= 14"
                " && col() >= 5 && col() <= 14, 1, 0)"
            )
        )
        tools.r_mapcalc(
            expression=(
                "square_small = if(row() >= 8 && row() <= 11"
                " && col() >= 8 && col() <= 11, 1, 0)"
            )
        )
        tools.r_mapcalc(expression="dem = row()")
        yield session
