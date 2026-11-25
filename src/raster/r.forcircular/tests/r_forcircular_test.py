import os

import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError


@pytest.fixture
def session(tmp_path):
    """A session whose region is coarser than the 10 m the tool sets."""
    project = tmp_path / "forcircular"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        env = session.env
        gs.run_command("g.region", n=100, s=0, e=100, w=0, res=20, env=env)
        gs.run_command("r.mapcalc", expression="dtm = row() + col()", env=env)
        gs.run_command("v.in.region", output="area", env=env)
        yield session


def test_region_restored_after_error(session):
    """A run that stops with an error leaves the user's region as it was.

    The area has no attribute table, so the tool fails right after setting
    its own region, when it rasterizes the incr_ha column.
    """
    env = session.env
    before = gs.region(env=env)
    with pytest.raises(CalledModuleError):
        gs.run_command(
            "r.forcircular",
            forest="area",
            boundaries="area",
            dtm="dtm",
            tracks="area",
            hf_slope="cable crane - high power",
            c_slope="cable crane - high power",
            hf_noslope="forwarder",
            c_noslope="forwarder",
            ind1="ind1",
            ind2="ind2",
            ind3="ind3",
            ind4="ind4",
            ind5="ind5",
            ind6="ind6",
            ind7="ind7",
            quiet=True,
            env=env,
        )
    assert gs.region(env=env) == before
