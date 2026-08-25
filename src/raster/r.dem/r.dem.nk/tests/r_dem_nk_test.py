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


def _make_surfaces_ns(tools):
    """A steep, varied reference and an SfM copy shifted ~1 cell north + 0.5 m."""
    tools.g_region(n=200, s=0, e=200, w=0, res=1)
    tools.r_mapcalc(
        expression="lidar = 5.0 * sin(col() * 18.0) + 5.0 * cos(row() * 18.0)",
        overwrite=True,
    )
    tools.r_mapcalc(expression="sfm = lidar[1,0] + 0.5", overwrite=True)
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


def test_solve_recovers_north_offset(session, tmp_path):
    """Guard the dy sign: an SfM shifted one cell north must solve dy ~ +1."""
    tools = Tools(session=session)
    _make_surfaces_ns(tools)
    xform = os.fspath(tmp_path / "nk_ns.txt")
    tools.r_dem_nk(
        sfm="sfm",
        lidar="lidar",
        stable_mask="mask",
        output="out_solve_ns",
        transform_output=xform,
        overwrite=True,
    )
    vals = _read_transform(xform)
    assert abs(vals["dz"] - 0.5) < 0.05
    assert abs(vals["dx"]) < 0.1
    assert abs(vals["dy"] - 1.0) < 0.1


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


def _make_subpixel_surfaces(tools, dx=3.2, dy=-1.7, dz=5.0):
    """A reference with relief and an SfM copy shifted a fractional cell.

    SfM(x, y) = lidar(x - dx, y - dy) + dz, built by sampling lidar on a
    grid shifted by (-dx, -dy) and relocating that grid onto the base
    region with r.region.
    """
    tools.g_region(n=1000, s=0, e=1000, w=0, res=10)
    tools.r_mapcalc(
        expression=(
            "lidar = 100 + 0.7 * col() + 0.4 * row()"
            " + 5.0 * sin(col() * 18.0) + 4.0 * cos(row() * 23.0)"
        ),
        overwrite=True,
    )
    tools.r_mapcalc(
        expression=(
            "mask = if(row() > 1 && row() < nrows()"
            " && col() > 1 && col() < ncols(), 1, null())"
        ),
        overwrite=True,
    )
    tools.g_region(n=1000 - dy, s=0 - dy, e=1000 - dx, w=0 - dx, res=10)
    tools.r_resamp_interp(
        input="lidar", output="lidar_shift", method="bilinear", overwrite=True
    )
    tools.r_region(map="lidar_shift", n=1000, s=0, e=1000, w=0)
    tools.g_region(n=1000, s=0, e=1000, w=0, res=10)
    tools.r_mapcalc(expression=f"sfm = lidar_shift + {dz}", overwrite=True)


def test_residual_improves_subpixel(session):
    """A fractional-cell shift plus dz must leave near-zero residuals."""
    tools = Tools(session=session)
    _make_subpixel_surfaces(tools)
    tools.r_mapcalc(expression="resid0 = if(mask, sfm - lidar, null())", overwrite=True)
    stats0 = tools.r_univar(map="resid0", format="json").json
    tools.r_dem_nk(
        sfm="sfm",
        lidar="lidar",
        stable_mask="mask",
        output="out_sub",
        interp="bilinear",
        slope_min=0.0,
        slope_max=89.0,
        iters=1,
        sigma=2.5,
        overwrite=True,
    )
    stats1 = tools.r_univar(map="out_sub_resid", format="json").json
    assert abs(stats0["mean"]) > 1.0
    assert stats0["stddev"] > 0.2
    assert abs(stats1["mean"]) < 0.5
    assert stats1["stddev"] < 0.5
    assert abs(stats1["mean"]) < abs(stats0["mean"])
    assert stats1["stddev"] < stats0["stddev"]


def test_keep_intermediates(session):
    """-k should write slope/aspect/mask helper rasters."""
    tools = Tools(session=session)
    _make_subpixel_surfaces(tools)
    tools.r_dem_nk(
        flags="k",
        sfm="sfm",
        lidar="lidar",
        stable_mask="mask",
        output="outk",
        interp="nearest",
        slope_min=0.0,
        slope_max=89.0,
        iters=0,
        sigma=2.5,
        overwrite=True,
    )
    for suffix in ("", "_resid", "_slope", "_aspect", "_mask"):
        tools.r_info(map=f"outk{suffix}")
