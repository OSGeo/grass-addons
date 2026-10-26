"""Tests for the v.profile.points addon (point map input)."""

import pytest
from grass.exceptions import CalledModuleError


def read_points(tools, name):
    """Return the output map as a list of (x, y, z) tuples sorted by category."""
    text = tools.v_out_ascii(input=name, separator="pipe").text
    rows = [line.split("|") for line in text.splitlines()]
    rows.sort(key=lambda row: int(row[3]))
    return [(float(x), float(y), float(z)) for x, y, z, _cat in rows]


def test_profile_from_coordinates(profile):
    """Output x is distance along the line, y is height, z is the offset."""
    tools = profile.tools
    tools.v_profile_points(
        point_input="points", coordinates=profile.coordinates, output="out", width=10
    )
    # Buffer of 5 keeps the points on the line and the three slightly off it.
    assert read_points(tools, "out") == [
        (10, 5, 0),
        (50, 10, 0),
        (90, 15, 0),
        (50, 20, 2),
        (50, 22, 2.4),
        (50, 21, 3),
    ]


def test_line_input_matches_coordinates(profile):
    tools = profile.tools
    tools.v_profile_points(
        point_input="points",
        coordinates=profile.coordinates,
        output="from_coords",
        width=10,
    )
    tools.v_profile_points(
        point_input="points", line_input="line", output="from_line", width=10
    )
    assert read_points(tools, "from_line") == read_points(tools, "from_coords")


def test_width_limits_selected_points(profile):
    tools = profile.tools
    tools.v_profile_points(
        point_input="points", coordinates=profile.coordinates, output="narrow", width=5
    )
    # Buffer of 2.5 drops the point offset by 3 and keeps those offset by less.
    assert [p[2] for p in read_points(tools, "narrow")] == [0, 0, 0, 2, 2.4]


def test_default_width_is_fraction_of_line_length(profile):
    """Default width is 5% of the line length, so the buffer is 2.5 here."""
    tools = profile.tools
    tools.v_profile_points(
        point_input="points", coordinates=profile.coordinates, output="default_width"
    )
    offsets = [p[2] for p in read_points(tools, "default_width")]
    assert offsets == [0, 0, 0, 2, 2.4]
    assert max(offsets) <= 0.025 * profile.line_length


def test_z_flag_starts_heights_at_zero(profile):
    tools = profile.tools
    tools.v_profile_points(
        point_input="points",
        coordinates=profile.coordinates,
        output="shifted",
        width=10,
        flags="z",
    )
    heights = [p[1] for p in read_points(tools, "shifted")]
    assert heights == [0, 5, 10, 15, 17, 16]


def test_overwrite_protection(profile):
    tools = profile.tools
    tools.v_profile_points(
        point_input="points", coordinates=profile.coordinates, output="out", width=10
    )
    with pytest.raises(CalledModuleError):
        tools.v_profile_points(
            point_input="points",
            coordinates=profile.coordinates,
            output="out",
            width=10,
        )


def test_no_temporary_maps_left(profile):
    tools = profile.tools
    tools.v_profile_points(
        point_input="points", coordinates=profile.coordinates, output="out", width=10
    )
    maps = tools.g_list(type="vector", mapset=".", format="json").json
    assert [m["name"] for m in maps] == ["out"]
