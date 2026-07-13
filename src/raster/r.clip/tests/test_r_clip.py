"""Tests for the r.clip addon.

Coverage
--------
- Default run: clips to the current region and preserves the input cell size
- ``-r`` flag: resamples the output to the current region resolution
- Value fidelity: clipped cells equal the source raster values
- Overwrite protection: reusing an output name without --overwrite fails
- Larger region: cells outside the input extent become null
- Misaligned region: default run grows/snaps to the input grid
- Projected CRS: r.clip behaves the same in a metre (UTM) project
"""

import pytest

import grass.script as gs


def _assert_grid(info, *, res, north, south, east, west):
    """Assert an output raster has the given resolution and extent."""
    assert info["nsres"] == res
    assert info["ewres"] == res
    assert info["north"] == north
    assert info["south"] == south
    assert info["east"] == east
    assert info["west"] == west


def test_default_clips_to_region_and_preserves_resolution(clip_dataset):
    """Default run clips to the current region but keeps the input cell size."""
    # Current region: a quarter of the input, at a finer resolution.
    gs.run_command("g.region", n=50, s=0, e=50, w=0, res=5)
    gs.run_command("r.clip", input=clip_dataset.input, output="clip_default")

    # Resolution comes from the input, not the region; extent is the overlap.
    _assert_grid(
        gs.raster_info("clip_default"),
        res=clip_dataset.res,
        north=50,
        south=0,
        east=50,
        west=0,
    )


def test_r_flag_resamples_to_region_resolution(clip_dataset):
    """With -r the output is resampled to the current region resolution."""
    gs.run_command("g.region", n=50, s=0, e=50, w=0, res=5)
    gs.run_command(
        "r.clip", input=clip_dataset.input, output="clip_resample", flags="r"
    )

    info = gs.raster_info("clip_resample")
    assert info["nsres"] == 5
    assert info["ewres"] == 5


def test_clipped_values_match_input(clip_dataset):
    """Values inside the clipped area equal the source raster values."""
    gs.run_command("g.region", n=50, s=0, e=50, w=0, res=clip_dataset.res)
    gs.run_command("r.clip", input=clip_dataset.input, output="clip_values")

    # The source-minus-clip difference must be exactly zero everywhere.
    gs.mapcalc(f"clip_diff = {clip_dataset.input} - clip_values")
    stats = gs.parse_command("r.univar", map="clip_diff", flags="g")
    assert float(stats["min"]) == 0
    assert float(stats["max"]) == 0


def test_overwrite_protection(clip_dataset):
    """Reusing an existing output name without --overwrite fails."""
    gs.run_command("g.region", n=100, s=0, e=100, w=0, res=clip_dataset.res)
    gs.run_command("r.clip", input=clip_dataset.input, output="clip_overwrite")
    with pytest.raises(gs.CalledModuleError):
        gs.run_command("r.clip", input=clip_dataset.input, output="clip_overwrite")


def test_region_larger_than_input_produces_nulls_outside(clip_dataset):
    """A region larger than the input yields data only where the input exists."""
    gs.run_command("g.region", n=150, s=-50, e=150, w=-50, res=clip_dataset.res)
    gs.run_command("r.clip", input=clip_dataset.input, output="clip_larger")

    # Only the original 10x10 = 100 input cells carry data; the rest are null.
    stats = gs.parse_command("r.univar", map="clip_larger", flags="g")
    assert int(stats["n"]) == 100


def test_default_grows_misaligned_region_to_input_grid(clip_dataset):
    """Default run snaps a misaligned region outward to the input grid."""
    # Region edges (5, 45) are off the input's 10-unit grid, at a different res.
    gs.run_command("g.region", n=45, s=5, e=45, w=5, res=7)
    gs.run_command("r.clip", input=clip_dataset.input, output="clip_misaligned")

    # Resolution is reset to the input's, and the extent grows to the grid.
    _assert_grid(
        gs.raster_info("clip_misaligned"),
        res=clip_dataset.res,
        north=50,
        south=0,
        east=50,
        west=0,
    )


def test_projected_crs_clip_preserves_resolution(clip_dataset_utm):
    """r.clip works in a projected (metre) CRS and preserves the cell size."""
    gs.run_command("g.region", n=500, s=0, e=500, w=0, res=50)
    gs.run_command("r.clip", input=clip_dataset_utm.input, output="clip_utm_out")

    _assert_grid(
        gs.raster_info("clip_utm_out"),
        res=clip_dataset_utm.res,
        north=500,
        south=0,
        east=500,
        west=0,
    )
