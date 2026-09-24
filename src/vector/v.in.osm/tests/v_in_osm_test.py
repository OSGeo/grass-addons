"""Tests for the v.in.osm addon: areas, lines, reprojection."""

import pytest

from grass.tools import ToolError


def test_polygon_layer_is_imported_as_areas(osm_setup):
    """A closed building way becomes one area with its attributes."""
    tools = osm_setup.tools
    tools.v_in_osm(
        input=osm_setup.input,
        table="multipolygons",
        where="building IS NOT NULL",
        output="buildings",
    )

    info = tools.v_info(map="buildings", flags="t", format="json")
    assert info["areas"] == 1
    assert info["lines"] == 0

    records = tools.v_db_select(map="buildings", format="json")["records"]
    assert [row["building"] for row in records] == ["hangar"]


def test_line_layer_has_no_boundaries(osm_setup):
    """Default types must not turn linestrings into boundaries."""
    tools = osm_setup.tools
    tools.v_in_osm(
        input=osm_setup.input,
        table="lines",
        where="highway IS NOT NULL",
        output="roads",
    )

    info = tools.v_info(map="roads", flags="t", format="json")
    assert info["lines"] >= 1
    assert info["boundaries"] == 0


def test_data_are_reprojected_to_project_crs(osm_setup):
    """Without -o, coordinates are Lambert-93, not WGS84 degrees."""
    tools = osm_setup.tools
    tools.v_in_osm(input=osm_setup.input, table="lines", output="projected")

    info = tools.v_info(map="projected", flags="g", format="json")
    assert 6.77e6 < info["north"] < 6.78e6
    assert 5.77e5 < info["east"] < 5.79e5


def test_override_flag_keeps_source_coordinates(osm_setup):
    """With -o, the data are imported without reprojection."""
    tools = osm_setup.tools
    tools.v_in_osm(input=osm_setup.input, table="lines", output="raw", flags="o")

    info = tools.v_info(map="raw", flags="g", format="json")
    assert info["north"] == pytest.approx(48.057, abs=1e-3)


def test_polygon_layer_rejects_line_type(osm_setup):
    """Requesting only lines from a polygon layer fails loudly."""
    with pytest.raises(ToolError, match="boundary"):
        osm_setup.tools.v_in_osm(
            input=osm_setup.input, table="multipolygons", type="line", output="bad"
        )
