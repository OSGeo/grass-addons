"""Fixtures for the r.stream.variables tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.tools import Tools


@pytest.fixture
def variables(tmp_path):
    """Fresh project with a variable raster in PERMANENT and extra mapsets.

    For each area, the project has a user mapset with a name starting like
    the temporary mapsets of the module (sub_streams, sub_watersheds) and
    a leftover temporary mapset of a previous run (sub_streamID5,
    sub_watershedID5). HOME points to a temporary directory because the
    module writes $HOME/.grass8/rc* files.
    """
    project = tmp_path / "project"
    gs.create_project(project)
    home = tmp_path / "home"
    (home / ".grass8").mkdir(parents=True)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=3, s=0, e=3, w=0, res=1)
            tools.r_mapcalc(expression="elevation = row() + col()")
            for mapset in ("sub_streams", "sub_watersheds"):
                tools.g_mapset(mapset=mapset, flags="c")
                tools.r_mapcalc(expression="user_map = 1")
            for mapset in ("sub_streamID5", "sub_watershedID5"):
                tools.g_mapset(mapset=mapset, flags="c")
            tools.g_mapset(mapset="PERMANENT")
        env = session.env.copy()
        env["HOME"] = str(home)
        yield SimpleNamespace(env=env, path=tmp_path, project=project)
