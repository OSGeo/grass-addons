import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """A temporary GRASS project with a small computational region and a
    synthetic DoD plus two uncertainty rasters.
    """
    tmp = tmp_path_factory.mktemp("rdemerrprop")
    project = os.path.join(tmp, "errprop")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        gs.run_command("g.region", n=30, s=0, e=30, w=0, res=1, env=session.env)
        # DoD: linearly varying elevation change from -2 to +2 metres.
        gs.run_command(
            "r.mapcalc",
            expression="dod = (row() - 15) * 0.2",
            env=session.env,
        )
        # Two uncertainty sources (constant 1 sigma surfaces).
        gs.run_command("r.mapcalc", expression="sigma_a = 0.3", env=session.env)
        gs.run_command("r.mapcalc", expression="sigma_b = 0.4", env=session.env)
        yield session
