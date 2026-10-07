"""Fixtures for the v.in.osm tests."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools

# One closed building way and one highway way near 48.055 N, 1.370 E.
OSM = Path(__file__).resolve().parent / "data_small.osm"


@pytest.fixture(scope="module")
def lambert93_session(tmp_path_factory):
    """Project in RGF93 / Lambert-93 (EPSG:2154), a CRS other than WGS84."""
    project = tmp_path_factory.mktemp("v_in_osm") / "project"
    gs.create_project(project, epsg="2154")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        yield session


@pytest.fixture
def osm_setup(lambert93_session):
    """Isolated per-test mapset with a Tools handle and the OSM test file."""
    with TemporaryMapsetSession(env=lambert93_session.env) as session:
        with Tools(session=session) as tools:
            yield SimpleNamespace(tools=tools, input=str(OSM))
