import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """A temporary GRASS project in a projected metric CRS."""
    project = tmp_path_factory.mktemp("grassdata") / "nk_project"
    gs.create_project(project, epsg="6346")
    with gs.setup.init(project) as session:
        gs.run_command("g.region", n=200, s=0, e=200, w=0, res=1, env=session.env)
        yield session
