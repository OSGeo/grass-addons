import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary GRASS project with a reference DEM, a post-event DEM carrying
    a localized deposition block plus an isolated single-cell spike, and a
    uniform LoD raster.
    """
    tmp = tmp_path_factory.mktemp("rdemchange")
    project = os.path.join(tmp, "change")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        env = session.env
        gs.run_command("g.region", n=40, s=0, e=40, w=0, res=1, env=env)
        gs.run_command("r.mapcalc", expression="dem_pre = 100.0", env=env)
        # +2 m deposition block in a contiguous patch, plus one isolated spike.
        gs.run_command(
            "r.mapcalc",
            expression=(
                "dem_post = 100.0 "
                "+ if(row() >= 10 && row() <= 20 && col() >= 10 && col() <= 20,"
                " 2.0, 0.0) "
                "+ if(row() == 30 && col() == 30, 5.0, 0.0)"
            ),
            env=env,
        )
        gs.run_command("r.mapcalc", expression="lod = 1.0", env=env)
        yield session
