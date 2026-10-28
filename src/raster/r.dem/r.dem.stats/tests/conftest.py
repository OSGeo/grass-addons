import os

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Temporary GRASS project with a synthetic fractal DEM."""
    tmp = tmp_path_factory.mktemp("rdemstats")
    project = os.path.join(tmp, "stats")
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project) as session:
        gs.run_command("g.region", n=100, s=0, e=100, w=0, res=1, env=session.env)
        gs.run_command("r.surf.fractal", output="dem", dimension=2.6, env=session.env)
        yield session
