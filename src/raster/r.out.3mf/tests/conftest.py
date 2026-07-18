"""Setup a synthetic DEM session for r.out.3mf tests."""

from types import SimpleNamespace

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def dem_session(tmp_path_factory):
    """Create a session with a small synthetic elevation raster."""
    project = tmp_path_factory.mktemp("r_out_3mf") / "test"
    gs.create_project(project)
    with gs.setup.init(project) as session:
        gs.run_command(
            "g.region", n=30, s=0, e=30, w=0, res=1, flags="a", env=session.env
        )
        # A tilted plane gives non-trivial relief to mesh.
        gs.mapcalc("elevation = 100 + row() * 1.5 + col() * 2.0", env=session.env)
        yield SimpleNamespace(session=session, name="elevation")
