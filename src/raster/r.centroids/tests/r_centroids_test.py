"""Tests for the r.centroids addon."""

import pytest

from grass.tools import ToolError

# Exact centroid per clump (region 10x10, res 1). These symmetric 3x3 blocks
# make r.volume's distance-weighted centroid land on the clump's middle cell,
# so exact coordinates are stable here; irregular or even-sized clumps can
# hit r.volume's counting/adjusted fallback and shift the point.
EXPECTED = {1: (1.5, 8.5), 2: (8.5, 8.5), 3: (1.5, 1.5), 4: (8.5, 1.5)}


def test_output_has_one_point_per_clump_excluding_background(clump_setup):
    """One centroid is produced per non-zero clump value; 0 is background."""
    tools = clump_setup.tools
    tools.r_centroids(input=clump_setup.input, output="out_centroids")

    info = tools.v_info(map="out_centroids", flags="t", format="json")
    assert info["points"] == 4

    records = tools.v_db_select(map="out_centroids", format="json")["records"]
    assert {row["cat"] for row in records} == {1, 2, 3, 4}


def test_volume_columns_are_dropped(clump_setup):
    """r.volume's volume/sum/count/average columns are removed."""
    tools = clump_setup.tools
    tools.r_centroids(input=clump_setup.input, output="out_columns")

    columns = tools.v_info(map="out_columns", flags="c", format="json")
    assert {col["name"] for col in columns} == {"cat"}


def test_overwrite_protection(clump_setup):
    """Reusing an output name without --overwrite fails."""
    tools = clump_setup.tools
    tools.r_centroids(input=clump_setup.input, output="out_overwrite")
    with pytest.raises(ToolError):
        tools.r_centroids(input=clump_setup.input, output="out_overwrite")


def test_centroid_matches_expected_coordinates(clump_setup):
    """Each centroid lands on its source clump's exact expected point."""
    tools = clump_setup.tools
    tools.r_centroids(input=clump_setup.input, output="out_extent")

    lines = tools.v_out_ascii(input="out_extent", format="point").stdout.splitlines()
    points = {
        int(cat): (float(x), float(y))
        for x, y, cat in (line.split("|") for line in lines)
    }
    assert points == pytest.approx(EXPECTED)
