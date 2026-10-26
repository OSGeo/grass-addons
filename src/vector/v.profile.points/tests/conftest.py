"""Fixtures for the v.profile.points tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools

# The profile line runs along the x axis from (0, 0) to (100, 0), so a point's
# x is its distance along the line and its y is its offset from the line.
LINE_START = (0, 0)
LINE_END = (100, 0)
LINE_LENGTH = 100

# (x, y, z) points: three on the line, three slightly off it, and two far away
# (one to the side, one beyond the end of the line). The offset of 2.4 lies
# between 2.5% of the line length (2.5) and 2.5% of its azimuth (2.25), which
# tells the default width apart from a buffer computed from the azimuth.
POINTS = [
    (10, 0, 5),
    (50, 0, 10),
    (90, 0, 15),
    (50, 2, 20),
    (50, 2.4, 22),
    (50, 3, 21),
    (50, 50, 30),
    (120, 0, 7),
]


@pytest.fixture(scope="module")
def module_session(tmp_path_factory):
    """Build a project with the point map and the profile line once per module."""
    project = tmp_path_factory.mktemp("v_profile_points") / "project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            points_file = tmp_path_factory.mktemp("points") / "points.txt"
            points_file.write_text("\n".join(f"{x}|{y}|{z}" for x, y, z in POINTS))
            tools.v_in_ascii(
                input=str(points_file),
                output="points",
                separator="pipe",
                z=3,
                flags="z",
            )
            line_file = tmp_path_factory.mktemp("line") / "line.txt"
            line_file.write_text(
                "L 2 1\n{} {}\n{} {}\n\n1 1\n".format(*LINE_START, *LINE_END)
            )
            tools.v_in_ascii(
                input=str(line_file), output="line", format="standard", flags="n"
            )
        yield session


@pytest.fixture
def profile(module_session):
    """Isolated per-test mapset + Tools handle over the module-scoped base session."""
    with TemporaryMapsetSession(env=module_session.env) as session:
        with Tools(session=session) as tools:
            yield SimpleNamespace(
                tools=tools,
                env=session.env,
                coordinates=(*LINE_START, *LINE_END),
                line_length=LINE_LENGTH,
            )
