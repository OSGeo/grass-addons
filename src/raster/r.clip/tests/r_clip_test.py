"""Tests for the r.clip addon."""

import pytest

from grass.exceptions import CalledModuleError


def test_default_clips_to_region_and_preserves_resolution(clip_ll):
    """Default run clips to the region but keeps the input cell size."""
    tools = clip_ll.tools
    tools.g_region(n=5, s=0, e=5, w=0, res=0.5)
    tools.r_clip(input=clip_ll.input, output="clip_default")

    # Resolution stays that of the input, not the finer region.
    info = tools.r_info(map="clip_default", format="json")
    assert (info["nsres"], info["ewres"]) == (clip_ll.res, clip_ll.res)
    assert (info["north"], info["south"], info["east"], info["west"]) == (5, 0, 5, 0)


def test_r_flag_resamples_to_region_resolution(clip_ll):
    """With -r the output takes the current region resolution."""
    tools = clip_ll.tools
    tools.g_region(n=5, s=0, e=5, w=0, res=0.5)
    tools.r_clip(input=clip_ll.input, output="clip_resample", flags="r")

    info = tools.r_info(map="clip_resample", format="json")
    assert (info["nsres"], info["ewres"]) == pytest.approx((0.5, 0.5), abs=1e-9)


def test_clipped_values_match_input(clip_ll):
    """Clipped cells equal the source values."""
    tools = clip_ll.tools
    tools.g_region(n=5, s=0, e=5, w=0, res=clip_ll.res)
    tools.r_clip(input=clip_ll.input, output="clip_values")

    # Diff is zero everywhere the clip has data, i.e. clipped cells match the input.
    tools.r_mapcalc(expression=f"clip_diff = {clip_ll.input} - clip_values")
    stats = tools.r_univar(map="clip_diff", format="json")
    assert (stats["min"], stats["max"]) == (0, 0)


def test_overwrite_protection(clip_ll):
    """Reusing an output name without --overwrite fails."""
    tools = clip_ll.tools
    tools.g_region(n=10, s=0, e=10, w=0, res=clip_ll.res)
    tools.r_clip(input=clip_ll.input, output="clip_overwrite")
    with pytest.raises(CalledModuleError):
        tools.r_clip(input=clip_ll.input, output="clip_overwrite")


def test_region_larger_than_input_produces_nulls_outside(clip_ll):
    """A region larger than the input has data only where the input exists."""
    tools = clip_ll.tools
    tools.g_region(n=15, s=-5, e=15, w=-5, res=clip_ll.res)
    tools.r_clip(input=clip_ll.input, output="clip_larger")

    # Only the 100 input cells carry data; the rest are null.
    stats = tools.r_univar(map="clip_larger", format="json")
    assert stats["n"] == 100


def test_default_grows_misaligned_region_to_input_grid(clip_ll):
    """Default run snaps a misaligned region out to the input grid."""
    tools = clip_ll.tools
    # Edges 0.5 and 4.5 are off the input's 1 degree grid, so they snap to 0 and 5.
    tools.g_region(n=4.5, s=0.5, e=4.5, w=0.5, res=0.5)
    tools.r_clip(input=clip_ll.input, output="clip_misaligned")

    info = tools.r_info(map="clip_misaligned", format="json")
    assert (info["nsres"], info["ewres"]) == (clip_ll.res, clip_ll.res)
    assert (info["north"], info["south"], info["east"], info["west"]) == (5, 0, 5, 0)


def test_projected_crs_clip_preserves_resolution(clip_utm):
    """r.clip preserves cell size in a projected (metre) CRS."""
    tools = clip_utm.tools
    tools.g_region(n=500, s=0, e=500, w=0, res=50)
    tools.r_clip(input=clip_utm.input, output="clip_utm_out")

    info = tools.r_info(map="clip_utm_out", format="json")
    assert (info["nsres"], info["ewres"]) == (clip_utm.res, clip_utm.res)
    assert (info["north"], info["south"], info["east"], info["west"]) == (
        500,
        0,
        500,
        0,
    )
