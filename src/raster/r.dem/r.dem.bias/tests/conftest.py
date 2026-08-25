import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary GRASS project with a synthetic DEM, a slope predictor, a
    forest mask with a constant elevation bump, and a stable mask with a
    slope-correlated DoD.
    """
    tmp = tmp_path_factory.mktemp("rdembias")
    project = os.path.join(tmp, "bias")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        env = session.env
        gs.run_command("g.region", n=50, s=0, e=50, w=0, res=1, env=env)
        gs.run_command("r.surf.fractal", output="dem", dimension=2.6, env=env)
        gs.run_command("r.slope.aspect", elevation="dem", slope="slope", env=env)

        # Forest mask on the western half, with a constant +2 m canopy bump.
        gs.run_command(
            "r.mapcalc",
            expression="forest = if(col() <= 25, 1, null())",
            env=env,
        )
        gs.run_command(
            "r.mapcalc",
            expression="dod_forest = if(col() <= 25, 2.0, 0.05 * row())",
            env=env,
        )

        # Stable mask on the southern half, with a slope-correlated DoD.
        gs.run_command(
            "r.mapcalc",
            expression="stable = if(row() <= 25, 1, null())",
            env=env,
        )
        gs.run_command(
            "r.mapcalc",
            expression="dod_reg = 0.2 * slope",
            env=env,
        )

        # Synthetic monotone predictors, built here so no test depends on a
        # map left behind by another test.
        gs.run_command("r.mapcalc", expression="rowpred = row()", env=env)
        gs.run_command("r.mapcalc", expression="colpred = col()", env=env)
        yield session
