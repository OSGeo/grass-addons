import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary GRASS project with a significant-change DoD on the western
    half, spectral vegetation loss on the northern half, and an infrastructure
    point vector inside the change zone.
    """
    tmp = tmp_path_factory.mktemp("rdemscreen")
    project = os.path.join(tmp, "screen")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        env = session.env
        gs.run_command("g.region", n=50, s=0, e=50, w=0, res=1, env=env)
        # Topographic change (2 m) on the western half.
        gs.run_command(
            "r.mapcalc",
            expression="dod = if(col() <= 25, 2.0, 0.0)",
            env=env,
        )
        # Spectral vegetation loss (-0.3) on the northern half.
        gs.run_command(
            "r.mapcalc",
            expression="ndvi_change = if(row() <= 25, -0.3, 0.0)",
            env=env,
        )
        # Infrastructure points inside the topographic-change zone.
        gs.write_command(
            "v.in.ascii",
            input="-",
            output="infra",
            separator=",",
            stdin="10,10\n10,40\n",
            env=env,
        )
        yield session
