"""Fixtures for the r.centroids tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


@pytest.fixture(scope="module")
def clumps_session(tmp_path_factory):
    """Project with a raster of 4 separated same-valued blocks in PERMANENT.

    Region is 10x10 at resolution 1; the blocks sit in the four corners
    with background 0 between them, so each stays a single clump.
    """
    project = tmp_path_factory.mktemp("r_centroids") / "project"
    gs.create_project(project, epsg="4326")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=10, s=0, e=10, w=0, res=1)
            tools.r_mapcalc(
                expression=(
                    "clumps = if(row() <= 3 && col() <= 3, 1,"
                    " if(row() <= 3 && col() >= 8, 2,"
                    " if(row() >= 8 && col() <= 3, 3,"
                    " if(row() >= 8 && col() >= 8, 4, 0))))"
                )
            )
        yield session


@pytest.fixture
def clump_setup(clumps_session):
    """Isolated per-test mapset + Tools handle over the module-scoped clumps raster."""
    with TemporaryMapsetSession(env=clumps_session.env) as session:
        with Tools(session=session) as tools:
            # A new mapset starts with its own default region, so align it
            # with the raster built in PERMANENT.
            tools.g_region(raster="clumps")
            yield SimpleNamespace(tools=tools, input="clumps")
