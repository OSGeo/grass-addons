"""Synthetic test data for v.surf.rst.cv tests"""

from types import SimpleNamespace

import pytest

import grass.script as gs

NPOINTS = 200

# npmin/segmax chosen so v.surf.rst skips segmentation cleanly for NPOINTS
NPMIN = 150
SEGMAX = 300


@pytest.fixture(scope="module")
def session(tmp_path_factory):
    """Session with an analytic surface sampled at three noise levels.

    The base surface is smooth and low-frequency; noise maps add seeded
    uniform noise of increasing amplitude. Each point map samples one of
    the noisy surfaces at the same seeded random locations.
    """
    tmp_path = tmp_path_factory.mktemp("v_surf_rst_cv")
    project = tmp_path / "test"
    gs.create_project(project)
    with gs.setup.init(project):
        gs.run_command("g.region", n=1000, s=0, e=1000, w=0, res=10)
        gs.mapcalc("base = 100.0 + 50.0 * sin(x() * 0.36) * cos(y() * 0.36)")
        point_maps = {}
        for name, amplitude in (("clean", 0), ("noisy", 15), ("very_noisy", 50)):
            surface = f"surface_{name}"
            if amplitude:
                gs.mapcalc(
                    f"{surface} = base + rand(-{amplitude}.0, {amplitude}.0)",
                    seed=42,
                )
            else:
                gs.mapcalc(f"{surface} = base")
            points = f"points_{name}"
            gs.run_command(
                "r.random",
                input=surface,
                npoints=NPOINTS,
                seed=1,
                vector=points,
                flags="z",
                quiet=True,
            )
            point_maps[name] = points
        yield SimpleNamespace(
            points=point_maps["noisy"],
            points_by_noise=point_maps,
            npoints=NPOINTS,
            npmin=NPMIN,
            segmax=SEGMAX,
        )
