"""Setup a synthetic DEM session for r.out.3mf tests."""

from types import SimpleNamespace

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def dem_session(tmp_path_factory):
    """Create a session with a small synthetic elevation raster."""
    tmp_path = tmp_path_factory.mktemp("r_out_3mf")
    location = "test"
    gs.core._create_location_xy(tmp_path, location)  # pylint: disable=protected-access
    with gs.setup.init(tmp_path / location) as session:
        gs.run_command("g.region", n=30, s=0, e=30, w=0, res=1, flags="a")
        # A tilted plane plus a bump gives non-trivial relief to mesh.
        gs.mapcalc("elevation = 100 + row() * 1.5 + col() * 2.0")
        yield SimpleNamespace(session=session, name="elevation")
