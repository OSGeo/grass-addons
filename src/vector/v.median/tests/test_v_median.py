"""Tests for the v.median addon."""

import pytest
from grass.exceptions import CalledModuleError

# v.median computes the median of x's and y's independently, not a true
# geometric median. For ODD_POINTS (x: 1..5, y: 10..50) that lands exactly on
# the middle input point: x=3, y=30.
ODD_EXPECTED = (3.0, 30.0)
# For EVEN_POINTS (x: 1..4, y: 10..40) numpy averages the two middle values:
# x=(2+3)/2=2.5, y=(20+30)/2=25.
EVEN_EXPECTED = (2.5, 25.0)


def test_output_to_vector_map_matches_expected_median(median):
    tools = median.tools
    tools.v_median(input="odd_points", output="median_out")

    info = tools.v_info(map="median_out", format="json")
    assert info["points"] == 1

    x, y, _cat = tools.v_out_ascii(input="median_out", separator="pipe").text.split("|")
    assert (float(x), float(y)) == pytest.approx(ODD_EXPECTED, abs=1e-6)


def test_stdout_output_prints_median(median):
    text = median.tools.v_median(input="odd_points", output="-").text
    x, y = (float(v) for v in text.split("|"))
    assert (x, y) == pytest.approx(ODD_EXPECTED, abs=1e-6)


def test_stdout_output_creates_no_map(median):
    median.tools.v_median(input="odd_points", output="-")
    assert median.tools.g_list(type="vector", mapset=".", format="json").json == []


def test_overwrite_protection(median):
    tools = median.tools
    tools.v_median(input="odd_points", output="median_overwrite")
    with pytest.raises(CalledModuleError):
        tools.v_median(input="odd_points", output="median_overwrite")


def test_even_point_count_averages_middle_values(median):
    tools = median.tools
    tools.v_median(input="even_points", output="median_even")

    x, y, _cat = tools.v_out_ascii(input="median_even", separator="pipe").text.split(
        "|"
    )
    assert (float(x), float(y)) == pytest.approx(EVEN_EXPECTED, abs=1e-6)
