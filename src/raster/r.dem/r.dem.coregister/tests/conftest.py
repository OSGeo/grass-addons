import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary GRASS project with a reference DEM, a post-event DSM offset by
    a known +0.5 m vertical bias, and a road centerline vector for PGCP
    sampling.
    """
    tmp = tmp_path_factory.mktemp("rdemcoreg")
    project = os.path.join(tmp, "coreg")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        env = session.env
        gs.run_command("g.region", n=50, s=0, e=50, w=0, res=1, env=env)
        # Smooth cone surface: slope is moderate (~17 deg, inside the N&K
        # [slope_min, slope_max] window) and aspect varies in all directions, so
        # the Nuth & Kaeaeb regression has ample valid stable pixels.
        gs.run_command(
            "r.mapcalc",
            expression="reference = 0.3 * sqrt(col()^2 + row()^2)",
            env=env,
        )
        # Post-event DSM carries a uniform +0.5 m bias.
        gs.run_command("r.mapcalc", expression="dsm = reference + 0.5", env=env)
        # Road centerline as a horizontal line vector across the region.
        gs.run_command(
            "r.mapcalc",
            expression="road_r = if(row() == 25, 1, null())",
            env=env,
        )
        gs.run_command(
            "r.to.vect",
            input="road_r",
            output="roads",
            type="line",
            env=env,
        )
        # Stable mask of sloped, unchanged terrain for the N&K / ICP stages.
        gs.run_command(
            "r.slope.aspect", elevation="reference", slope="ref_slope", env=env
        )
        gs.run_command(
            "r.mapcalc",
            expression="stable = if(ref_slope >= 2.0, 1, null())",
            env=env,
        )
        yield session
