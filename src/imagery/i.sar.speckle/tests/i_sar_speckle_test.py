"""Tests for the removal of temporary maps by i.sar.speckle."""

import grass.script as gs


def listed(env):
    return sorted(gs.read_command("g.list", type="raster", mapset=".", env=env).split())


def test_user_rasters_are_kept(user_data):
    """User rasters starting with "tmp" are kept."""
    user_data.tools.i_sar_speckle(input="sar@PERMANENT", output="sar_lee", size=3)
    assert listed(user_data.env) == ["sar_lee", "tmp_slope", "tmpdem"]


def test_output_starting_with_tmp_is_kept(user_data):
    """An output named with a "tmp" prefix is not removed as temporary."""
    user_data.tools.i_sar_speckle(input="sar@PERMANENT", output="tmp_lee", size=3)
    assert "tmp_lee" in listed(user_data.env)
