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


def test_default_clips_to_region_and_preserves_resolution(clip_dataset):
    """Default run clips to the current region but keeps the input cell size."""
    # Current region: a quarter of the input, at a finer resolution.
    gs.run_command("g.region", n=50, s=0, e=50, w=0, res=5)
    output = "clip_default"
    gs.run_command("r.clip", input=clip_dataset.input, output=output)

    info = gs.raster_info(output)
    # Resolution comes from the input, NOT from the current region.
    assert info["nsres"] == clip_dataset.res
    assert info["ewres"] == clip_dataset.res
    # Output covers only the overlapping part of the input.
    assert info["north"] == 50
    assert info["south"] == 0
    assert info["east"] == 50
    assert info["west"] == 0


def test_r_flag_resamples_to_region_resolution(clip_dataset):
    """With -r the output is resampled to the current region resolution."""
    gs.run_command("g.region", n=50, s=0, e=50, w=0, res=5)
    output = "clip_resample"
    gs.run_command("r.clip", input=clip_dataset.input, output=output, flags="r")

    info = gs.raster_info(output)
    assert info["nsres"] == 5
    assert info["ewres"] == 5


def test_clipped_values_match_input(clip_dataset):
    """Values inside the clipped area equal the source raster values."""
    gs.run_command("g.region", n=50, s=0, e=50, w=0, res=clip_dataset.res)
    output = "clip_values"
    gs.run_command("r.clip", input=clip_dataset.input, output=output)

    # The source-minus-clip difference must be exactly zero everywhere.
    diff = "clip_diff"
    gs.mapcalc(f"{diff} = {clip_dataset.input} - {output}")
    stats = gs.parse_command("r.univar", map=diff, flags="g")
    assert float(stats["min"]) == 0
    assert float(stats["max"]) == 0


def test_overwrite_protection(clip_dataset):
    """Reusing an existing output name without --overwrite fails."""
    gs.run_command("g.region", n=100, s=0, e=100, w=0, res=clip_dataset.res)
    output = "clip_overwrite"
    gs.run_command("r.clip", input=clip_dataset.input, output=output)
    with pytest.raises(gs.CalledModuleError):
        gs.run_command("r.clip", input=clip_dataset.input, output=output)


def test_region_larger_than_input_produces_nulls_outside(clip_dataset):
    """A region larger than the input yields data only where the input exists."""
    gs.run_command("g.region", n=150, s=-50, e=150, w=-50, res=clip_dataset.res)
    output = "clip_larger"
    gs.run_command("r.clip", input=clip_dataset.input, output=output)

    # Only the original 10x10 = 100 input cells carry data; the rest are null.
    stats = gs.parse_command("r.univar", map=output, flags="g")
    assert int(stats["n"]) == 100


def test_default_grows_misaligned_region_to_input_grid(clip_dataset):
    """Default run snaps a misaligned region outward to the input grid."""
    # Region edges (5, 45) are off the input's 10-unit grid, at a different res.
    gs.run_command("g.region", n=45, s=5, e=45, w=5, res=7)
    output = "clip_misaligned"
    gs.run_command("r.clip", input=clip_dataset.input, output=output)

    info = gs.raster_info(output)
    # Resolution is reset to the input's, and the extent grows to the grid.
    assert info["nsres"] == clip_dataset.res
    assert info["ewres"] == clip_dataset.res
    assert info["north"] == 50
    assert info["south"] == 0
    assert info["east"] == 50
    assert info["west"] == 0


def test_projected_crs_clip_preserves_resolution(clip_dataset_utm):
    """r.clip works in a projected (metre) CRS and preserves the cell size."""
    gs.run_command("g.region", n=500, s=0, e=500, w=0, res=50)
    output = "clip_utm_out"
    gs.run_command("r.clip", input=clip_dataset_utm.input, output=output)

    info = gs.raster_info(output)
    assert info["nsres"] == clip_dataset_utm.res
    assert info["ewres"] == clip_dataset_utm.res
    assert info["north"] == 500
    assert info["south"] == 0
    assert info["east"] == 500
    assert info["west"] == 0
