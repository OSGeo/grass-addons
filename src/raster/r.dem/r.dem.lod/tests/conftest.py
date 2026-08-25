import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary GRASS project with a reference DEM, a post-event DEM that
    differs by Gaussian noise on stable ground plus a real change patch, and a
    stable mask.
    """
    tmp = tmp_path_factory.mktemp("rdemlod")
    project = os.path.join(tmp, "lod")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        env = session.env
        gs.run_command("g.region", n=100, s=0, e=100, w=0, res=1, env=env)
        gs.run_command("r.surf.fractal", output="dem_pre", env=env)
        # Post-event = pre + small noise everywhere + a localized 3 m change.
        gs.run_command("r.surf.gauss", output="noise", mean=0, sigma=0.2, env=env)
        gs.run_command(
            "r.mapcalc",
            expression=(
                "dem_post = dem_pre + noise "
                "+ if(row() >= 40 && row() <= 60 && col() >= 40 && col() <= 60,"
                " 3.0, 0.0)"
            ),
            env=env,
        )
        # Stable terrain excludes the change patch.
        gs.run_command(
            "r.mapcalc",
            expression=(
                "stable = if(row() >= 40 && row() <= 60 && "
                "col() >= 40 && col() <= 60, null(), 1)"
            ),
            env=env,
        )
        # Precomputed difference for the dod= input path, built here so no
        # test depends on a map left behind by another test.
        gs.run_command("r.mapcalc", expression="dod_pre = dem_post - dem_pre", env=env)
        yield session
