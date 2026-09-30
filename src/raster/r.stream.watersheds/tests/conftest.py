"""Fixtures for the r.stream.watersheds tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.tools import Tools


@pytest.fixture
def watersheds(tmp_path):
    """Fresh project with drainage and stream rasters in PERMANENT.

    The module expects its input rasters in PERMANENT and changes the
    session's mapset, so every test gets its own project. HOME points to
    a temporary directory because the module writes $HOME/.grass8/rc* files.
    """
    project = tmp_path / "project"
    gs.create_project(project)
    home = tmp_path / "home"
    (home / ".grass8").mkdir(parents=True)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=3, s=0, e=3, w=0, res=1)
            tools.r_mapcalc(expression="drainage = 1")
            tools.r_mapcalc(
                expression="streams = if(row() == 2 && col() == 2, 1, null())"
            )
        env = session.env.copy()
        env["HOME"] = str(home)
        # messages without line wrapping, so the tests can match them
        env["GRASS_MESSAGE_FORMAT"] = "plain"
        yield SimpleNamespace(env=env, path=tmp_path)
