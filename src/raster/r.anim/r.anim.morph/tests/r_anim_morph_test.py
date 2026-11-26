import json

import numpy as np
import pytest

from grass.tools import ToolError, Tools

# numpy index of a GRASS cell: row index = GRASS row - 1 (row 1 is north),
# col index = GRASS col - 1.
CENTER = (9, 9)  # inside square_small and square_big
CORNER = (4, 4)  # corner of square_big, farthest from square_small
NEAR = (6, 9)  # in square_big, one cell north of square_small
BACKGROUND = (0, 5)  # outside both squares, away from the null cell


def univar(tools, name):
    return tools.r_univar(map=name, format="json").json


def as_array(tools, name):
    return np.asarray(tools.r_mapcalc_simple(expression="A", a=name, output=np.array))


def raster_names(tools, pattern):
    return tools.g_list(type="raster", pattern=pattern).text.split()


def test_blend_endpoints_and_nulls(session):
    tools = Tools(session=session)
    tools.r_anim_morph(before="before", after="after", output="blend", frames=3)
    first, middle, last = (univar(tools, f"blend_{i}") for i in (1, 2, 3))
    assert first["min"] == pytest.approx(100.0)
    assert first["max"] == pytest.approx(100.0)
    assert middle["min"] == pytest.approx(150.0)
    assert middle["max"] == pytest.approx(150.0)
    assert last["min"] == pytest.approx(200.0)
    assert last["max"] == pytest.approx(200.0)
    assert first["null_cells"] == 1
    assert last["null_cells"] == 1


def test_existing_frames_need_overwrite(session):
    tools = Tools(session=session)
    tools.r_anim_morph(before="before", after="after", output="keep", frames=2)
    with pytest.raises(ToolError):
        tools.r_anim_morph(before="before", after="after", output="keep", frames=2)
    tools.r_anim_morph(
        before="before", after="after", output="keep", frames=2, overwrite=True
    )


def test_multiband_frame_names(session):
    tools = Tools(session=session)
    tools.r_anim_morph(
        before="before,after", after="after,before", output="mb", frames=12
    )
    names = raster_names(tools, "mb_b*")
    assert len(names) == 24
    assert "mb_b1_01" in names
    assert "mb_b2_12" in names


def test_band_count_mismatch_fails(session):
    tools = Tools(session=session)
    with pytest.raises(ToolError):
        tools.r_anim_morph(before="before,after", after="after", output="bad")


def test_contraction_plan_order(session):
    tools = Tools(session=session)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="con",
        frames=2,
        primitive="contraction",
        mask_before="square_big",
        mask_after="square_small",
        roi_start=0.0,
        roi_end=0.8,
        bg_start=0.8,
        bg_end=1.0,
        blend_duration=0.2,
        output_plan="con_plan",
    )
    start = as_array(tools, "con_plan_S")
    end = as_array(tools, "con_plan_E")
    # Cells kept in both masks transition uniformly over the ROI window.
    assert start[CENTER] == pytest.approx(0.0)
    assert end[CENTER] == pytest.approx(0.8)
    # Background uses the background window.
    assert start[BACKGROUND] == pytest.approx(0.8)
    assert end[BACKGROUND] == pytest.approx(1.0)
    # Cells far from the new contour leave first, cells next to it last.
    assert start[CORNER] == pytest.approx(0.0)
    assert start[NEAR] == pytest.approx(0.6)
    assert end[NEAR] == pytest.approx(0.8)
    assert univar(tools, "con_plan_S")["null_cells"] == 0


def test_appearance_edge_first_and_plan_only(session):
    tools = Tools(session=session)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="app",
        primitive="appearance",
        mask_after="square_big",
        output_plan="app_plan",
        flags="p",
    )
    assert raster_names(tools, "app_*") == ["app_plan_E", "app_plan_S"]
    start = as_array(tools, "app_plan_S")
    assert start[CORNER] == pytest.approx(0.0)
    assert start[CENTER] == pytest.approx(0.7)
    assert start[BACKGROUND] == pytest.approx(0.0)


def test_expansion_near_old_contour_first(session):
    tools = Tools(session=session)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="exp",
        primitive="expansion",
        mask_before="square_small",
        mask_after="square_big",
        output_plan="exp_plan",
        flags="p",
    )
    start = as_array(tools, "exp_plan_S")
    assert start[NEAR] == pytest.approx(0.0)
    assert start[CORNER] == pytest.approx(0.7)
    assert start[CENTER] == pytest.approx(0.0)


def test_dem_high_first_and_invert(session):
    tools = Tools(session=session)
    south = (19, 0)
    north = (0, 5)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="demf",
        primitive="dem",
        dem="dem",
        output_plan="dem_plan",
        flags="p",
    )
    start = as_array(tools, "dem_plan_S")
    assert start[south] == pytest.approx(0.0)
    assert start[north] == pytest.approx(0.7)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="demf",
        primitive="dem",
        dem="dem",
        output_plan="dem_plan",
        flags="pi",
        overwrite=True,
    )
    start = as_array(tools, "dem_plan_S")
    assert start[south] == pytest.approx(0.7)
    assert start[north] == pytest.approx(0.0)


def test_directional_north_sweeps_from_south(session):
    tools = Tools(session=session)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="dir",
        primitive="directional",
        direction="N",
        output_plan="dir_plan",
        flags="p",
    )
    start = as_array(tools, "dir_plan_S")
    assert start[19, 3] == pytest.approx(0.0)
    assert start[0, 3] == pytest.approx(0.7)
    assert start[10, 0] == pytest.approx(start[10, 19])


def test_radial_from_coordinates(session):
    tools = Tools(session=session)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="rad",
        primitive="radial",
        coordinates=[10, 10],
        output_plan="rad_plan",
        flags="p",
    )
    start = as_array(tools, "rad_plan_S")
    assert start[0, 0] == pytest.approx(0.7)
    assert start[19, 19] == pytest.approx(0.7)
    assert start[CENTER] < start[4, 9] < start[0, 9]


def test_plan_primitive_renders_saved_plan(session):
    tools = Tools(session=session)
    tools.r_anim_morph(
        before="before",
        after="after",
        output="rt",
        primitive="contraction",
        mask_before="square_big",
        mask_after="square_small",
        roi_start=0.0,
        roi_end=0.8,
        bg_start=0.8,
        bg_end=1.0,
        blend_duration=0.2,
        output_plan="rt_plan",
        flags="p",
    )
    tools.r_anim_morph(
        before="before",
        after="after",
        output="rt",
        primitive="plan",
        plan_start="rt_plan_S",
        plan_end="rt_plan_E",
        frames=3,
    )
    middle = as_array(tools, "rt_2")
    assert middle[BACKGROUND] == pytest.approx(100.0)
    assert middle[CORNER] == pytest.approx(200.0)
    assert middle[CENTER] == pytest.approx(162.5)


def test_stages_compose_min_start_max_end(session, tmp_path):
    tools = Tools(session=session)
    stages = [
        {
            "primitive": "contraction",
            "mask_before": "square_big",
            "mask_after": "square_small",
            "roi_start": 0.0,
            "roi_end": 0.5,
            "bg_start": 0.5,
            "bg_end": 0.5,
            "blend_duration": 0.1,
        },
        {"primitive": "blend", "roi_start": 0.5, "roi_end": 1.0},
    ]
    path = tmp_path / "stages.json"
    path.write_text(json.dumps(stages))
    tools.r_anim_morph(
        before="before",
        after="after",
        output="stg",
        stages=str(path),
        output_plan="stg_plan",
        flags="p",
    )
    start = as_array(tools, "stg_plan_S")
    end = as_array(tools, "stg_plan_E")
    assert start[CORNER] == pytest.approx(0.0)
    assert start[BACKGROUND] == pytest.approx(0.5)
    assert end.min() == pytest.approx(1.0)


def test_missing_mask_fails(session):
    tools = Tools(session=session)
    with pytest.raises(ToolError):
        tools.r_anim_morph(
            before="before", after="after", output="nomask", primitive="appearance"
        )


def test_blend_duration_exceeding_window_fails(session):
    tools = Tools(session=session)
    with pytest.raises(ToolError):
        tools.r_anim_morph(
            before="before",
            after="after",
            output="toolong",
            roi_start=0.5,
            roi_end=0.6,
            blend_duration=0.3,
        )


def test_statistics_matching_flag(session):
    tools = Tools(session=session)
    tools.r_mapcalc(expression="bright = dem * 2 + 5")
    tools.r_anim_morph(
        before="dem", after="bright", output="match", frames=2, flags="c"
    )
    first = univar(tools, "match_1")
    target = univar(tools, "bright")
    assert first["mean"] == pytest.approx(target["mean"])
    assert first["stddev"] == pytest.approx(target["stddev"])
