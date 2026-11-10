"""Fixtures for the v.median tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools

# Distinct x's and y's so the per-axis median lands on one input point (odd
# count) or the average of the two middle points (even count).
ODD_POINTS = [(1, 10), (2, 20), (3, 30), (4, 40), (5, 50)]
EVEN_POINTS = [(1, 10), (2, 20), (3, 30), (4, 40)]


@pytest.fixture(scope="module")
def module_session(tmp_path_factory):
    """Build a project with odd- and even-count point maps once per module."""
    project = tmp_path_factory.mktemp("v_median") / "project"
    gs.create_project(project, epsg="4326")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            for name, points in (
                ("odd_points", ODD_POINTS),
                ("even_points", EVEN_POINTS),
            ):
                ascii_file = tmp_path_factory.mktemp(name) / "points.txt"
                ascii_file.write_text("\n".join(f"{x}|{y}" for x, y in points))
                tools.v_in_ascii(input=str(ascii_file), output=name, separator="pipe")
        yield session


@pytest.fixture
def median(module_session):
    """Isolated per-test mapset + Tools handle over the module-scoped base session."""
    with TemporaryMapsetSession(env=module_session.env) as session:
        with Tools(session=session) as tools:
            yield SimpleNamespace(tools=tools, env=session.env)
