"""Tests for the r.clip addon."""

import pytest

import grass.script as gs


def assert_grid(info, *, res, north, south, east, west):
    """Assert an output raster has the given resolution and extent."""
    assert info["nsres"] == res
    assert info["ewres"] == res
    assert info["north"] == north
    assert info["south"] == south
    assert info["east"] == east
    assert info["west"] == west


def test_default_clips_to_region_and_preserves_resolution(clip_ll):
    """Default run clips to the region but keeps the input cell size."""
    env = clip_ll.env
    gs.run_command("g.region", n=5, s=0, e=5, w=0, res=0.5, env=env)
    gs.run_command("r.clip", input=clip_ll.input, output="clip_default", env=env)

    # Resolution stays that of the input, not the finer region.
    assert_grid(
        gs.raster_info("clip_default", env=env),
        res=clip_ll.res,
        north=5,
        south=0,
        east=5,
        west=0,
    )


def test_r_flag_resamples_to_region_resolution(clip_ll):
    """With -r the output takes the current region resolution."""
    env = clip_ll.env
    gs.run_command("g.region", n=5, s=0, e=5, w=0, res=0.5, env=env)
    gs.run_command(
        "r.clip", input=clip_ll.input, output="clip_resample", flags="r", env=env
    )

    info = gs.raster_info("clip_resample", env=env)
    assert info["nsres"] == 0.5
    assert info["ewres"] == 0.5


def test_clipped_values_match_input(clip_ll):
    """Clipped cells equal the source values."""
    env = clip_ll.env
    gs.run_command("g.region", n=5, s=0, e=5, w=0, res=clip_ll.res, env=env)
    gs.run_command("r.clip", input=clip_ll.input, output="clip_values", env=env)

    gs.mapcalc(f"clip_diff = {clip_ll.input} - clip_values", env=env)
    stats = gs.parse_command("r.univar", map="clip_diff", flags="g", env=env)
    assert float(stats["min"]) == 0
    assert float(stats["max"]) == 0


def test_overwrite_protection(clip_ll):
    """Reusing an output name without --overwrite fails."""
    env = clip_ll.env
    gs.run_command("g.region", n=10, s=0, e=10, w=0, res=clip_ll.res, env=env)
    gs.run_command("r.clip", input=clip_ll.input, output="clip_overwrite", env=env)
    with pytest.raises(gs.CalledModuleError):
        gs.run_command("r.clip", input=clip_ll.input, output="clip_overwrite", env=env)


def test_region_larger_than_input_produces_nulls_outside(clip_ll):
    """A region larger than the input has data only where the input exists."""
    env = clip_ll.env
    gs.run_command("g.region", n=15, s=-5, e=15, w=-5, res=clip_ll.res, env=env)
    gs.run_command("r.clip", input=clip_ll.input, output="clip_larger", env=env)

    # Only the 100 input cells carry data; the rest are null.
    stats = gs.parse_command("r.univar", map="clip_larger", flags="g", env=env)
    assert int(stats["n"]) == 100


def test_default_grows_misaligned_region_to_input_grid(clip_ll):
    """Default run snaps a misaligned region out to the input grid."""
    env = clip_ll.env
    # Edges 0.5 and 4.5 are off the input's 1 degree grid, so they snap to 0 and 5.
    gs.run_command("g.region", n=4.5, s=0.5, e=4.5, w=0.5, res=0.5, env=env)
    gs.run_command("r.clip", input=clip_ll.input, output="clip_misaligned", env=env)

    assert_grid(
        gs.raster_info("clip_misaligned", env=env),
        res=clip_ll.res,
        north=5,
        south=0,
        east=5,
        west=0,
    )


def test_projected_crs_clip_preserves_resolution(clip_utm):
    """r.clip preserves cell size in a projected (metre) CRS."""
    env = clip_utm.env
    gs.run_command("g.region", n=500, s=0, e=500, w=0, res=50, env=env)
    gs.run_command("r.clip", input=clip_utm.input, output="clip_utm_out", env=env)

    assert_grid(
        gs.raster_info("clip_utm_out", env=env),
        res=clip_utm.res,
        north=500,
        south=0,
        east=500,
        west=0,
    )
