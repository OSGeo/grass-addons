"""Tests for the r.centroids addon."""

import pytest

from grass.exceptions import CalledModuleError

# cat -> (x range, y range) of the source quadrant, for the loose
# extent-containment check below.
QUADRANTS = {
    1: ((0, 3), (7, 10)),
    2: ((7, 10), (7, 10)),
    3: ((0, 3), (0, 3)),
    4: ((7, 10), (0, 3)),
}


def test_output_has_one_point_per_clump_excluding_background(centroids):
    """One centroid is produced per non-zero clump value; 0 is background."""
    tools = centroids.tools
    tools.r_centroids(input=centroids.input, output="out_centroids")

    info = tools.v_info(map="out_centroids", flags="t", format="json")
    assert info["points"] == 4

    records = tools.v_db_select(map="out_centroids", format="json")["records"]
    assert {row["cat"] for row in records} == {1, 2, 3, 4}


def test_volume_columns_are_dropped(centroids):
    """r.volume's volume/sum/count/average columns are removed."""
    tools = centroids.tools
    tools.r_centroids(input=centroids.input, output="out_columns")

    columns = tools.v_info(map="out_columns", flags="c", format="json")
    assert {col["name"] for col in columns} == {"cat"}


def test_overwrite_protection(centroids):
    """Reusing an output name without --overwrite fails."""
    tools = centroids.tools
    tools.r_centroids(input=centroids.input, output="out_overwrite")
    with pytest.raises(CalledModuleError):
        tools.r_centroids(input=centroids.input, output="out_overwrite")


def test_centroid_lies_within_source_clump_extent(centroids):
    """Each centroid falls inside the bounding box of the quadrant it came from."""
    tools = centroids.tools
    tools.r_centroids(input=centroids.input, output="out_extent")

    lines = tools.v_out_ascii(input="out_extent", format="point").stdout.splitlines()
    assert len(lines) == 4
    for line in lines:
        x, y, cat = line.split("|")
        x_range, y_range = QUADRANTS[int(cat)]
        assert x_range[0] <= float(x) <= x_range[1]
        assert y_range[0] <= float(y) <= y_range[1]
