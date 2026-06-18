"""Tests for r.dem.nk transform save/apply round trip."""

import os

from grass.tools import Tools


def _make_surfaces(tools):
    """A steep, varied reference and an SfM copy shifted ~1 cell east + 0.5 m."""
    tools.g_region(n=200, s=0, e=200, w=0, res=1)
    tools.r_mapcalc(
        expression="lidar = 5.0 * sin(col() * 18.0) + 5.0 * cos(row() * 18.0)",
        overwrite=True,
    )
    tools.r_mapcalc(expression="sfm = lidar[0,-1] + 0.5", overwrite=True)
    tools.r_mapcalc(expression="mask = 1", overwrite=True)


def _read_transform(path):
    vals = {}
    with open(path) as f:
        for line in f:
            if line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            vals[key.strip()] = float(value)
    return vals


def test_solve_recovers_known_offsets(session, tmp_path):
    tools = Tools(session=session)
    _make_surfaces(tools)
    xform = os.fspath(tmp_path / "nk.txt")
    tools.r_dem_nk(
        sfm="sfm",
        lidar="lidar",
        stable_mask="mask",
        output="out_solve",
        transform_output=xform,
        overwrite=True,
    )
    vals = _read_transform(xform)
    assert abs(vals["dz"] - 0.5) < 0.05
    assert abs(vals["dx"] - 1.0) < 0.1
    assert abs(vals["dy"]) < 0.1


def test_apply_reproduces_solve(session, tmp_path):
    tools = Tools(session=session)
    _make_surfaces(tools)
    xform = os.fspath(tmp_path / "nk.txt")
    tools.r_dem_nk(
        sfm="sfm",
        lidar="lidar",
        stable_mask="mask",
        output="out_solve",
        transform_output=xform,
        overwrite=True,
    )
    tools.r_dem_nk(
        sfm="sfm",
        lidar="lidar",
        stable_mask="mask",
        output="out_apply",
        apply_transform=xform,
        overwrite=True,
    )
    tools.r_mapcalc(expression="diff = abs(out_solve - out_apply)", overwrite=True)
    stats = tools.r_univar(map="diff", format="json").json
    assert stats["max"] < 1e-6
