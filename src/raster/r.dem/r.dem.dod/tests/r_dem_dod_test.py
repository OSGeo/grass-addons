import pytest

from grass.exceptions import CalledModuleError


def _colors(tools, name):
    """Color rules of a raster as {value: 'r:g:b'} for numeric breaks."""
    rules = {}
    for line in tools.r_colors_out(map=name).text.splitlines():
        value, rgb = line.split()
        try:
            rules[round(float(value), 6)] = rgb
        except ValueError:
            continue
    return rules


def test_aligned_inputs_difference_exactly(tools):
    result = tools.r_dem_dod(dem="dem_post", reference="dem_pre", output="dod")
    stats = tools.r_univar(map="dod", format="json")
    assert stats["n"] == 1600
    assert stats["min"] == pytest.approx(0.0, abs=1e-9)
    assert stats["max"] == pytest.approx(2.0, abs=1e-9)
    assert stats["sum"] == pytest.approx(121 * 2.0, abs=1e-6)
    assert "not aligned" not in result.stderr


def test_offset_below_tolerance_is_not_resampled(tools):
    # 5 micrometers is floating point noise at 1 m resolution.
    result = tools.r_dem_dod(
        dem="dem_5um", reference="dem_pre", output="dod_5um", overwrite=True
    )
    assert "not aligned" not in result.stderr
    stats = tools.r_univar(map="dod_5um", format="json")
    assert stats["n"] == 1600


def test_offset_above_tolerance_is_resampled(tools):
    # 1 mm is a tenth of a percent of a cell, above the tolerance.
    result = tools.r_dem_dod(
        dem="dem_1mm", reference="dem_pre", output="dod_1mm", overwrite=True
    )
    assert "not aligned" in result.stderr


def test_misaligned_input_is_resampled_with_warning(tools):
    result = tools.r_dem_dod(
        dem="dem_shift", reference="dem_pre", output="dod_shift", overwrite=True
    )
    assert "not aligned" in result.stderr
    assert "bilinear" in result.stderr
    # Bilinear interpolation reproduces a plane, so the interior is exact;
    # edge cells without four neighbors are null.
    stats = tools.r_univar(map="dod_shift", format="json")
    assert 0 < stats["n"] < 1600
    assert stats["min"] == pytest.approx(0.0, abs=1e-6)
    assert stats["max"] == pytest.approx(0.0, abs=1e-6)


def test_interp_option_reaches_resampling(tools):
    # On a curved surface bilinear interpolation leaves an error that bicubic
    # interpolation does not, so the two choices give different DoDs.
    for method in ("bilinear", "bicubic"):
        tools.r_dem_dod(
            dem="curve_shift",
            reference="curve_pre",
            output=f"dod_curve_{method}",
            interp=method,
            overwrite=True,
        )
    bilinear = tools.r_univar(map="dod_curve_bilinear", format="json")
    bicubic = tools.r_univar(map="dod_curve_bicubic", format="json")
    assert bilinear["mean"] > 1e-3
    assert abs(bicubic["mean"]) < bilinear["mean"]


def test_finer_input_warns(tools):
    result = tools.r_dem_dod(
        dem="dem_fine", reference="dem_pre", output="dod_fine", overwrite=True
    )
    assert "finer than the computational region" in result.stderr
    assert "r.resamp.stats" in result.stderr


def test_range_sets_palette(tools):
    tools.r_dem_dod(
        dem="dem_post", reference="dem_pre", output="dod_r1", range=1, overwrite=True
    )
    rules = _colors(tools, "dod_r1")
    assert rules[-1.0] == "255:0:255"
    assert rules[0.0] == "200:255:200"
    assert rules[0.6] == "0:0:255"
    assert rules[1.0] == "0:0:128"
    # Differences beyond the saturation value keep the end color.
    assert rules[2.0] == "0:0:128"


def test_default_range_is_rounded_98th_percentile(tools):
    tools.r_dem_dod(
        dem="dem_post", reference="dem_pre", output="dod_auto", overwrite=True
    )
    # 121 of 1600 cells hold 2 m, so the 98th percentile of |DoD| is 2.
    rules = _colors(tools, "dod_auto")
    assert rules[2.0] == "0:0:128"
    assert rules[1.2] == "0:0:255"


def test_invalid_range_fails(tools):
    with pytest.raises(CalledModuleError, match="greater than zero"):
        tools.r_dem_dod(dem="dem_post", reference="dem_pre", output="dod_bad", range=0)


def test_metadata_and_history(tools):
    tools.r_dem_dod(
        dem="dem_post", reference="dem_pre", output="dod_meta", overwrite=True
    )
    info = tools.r_info(map="dod_meta", flags="e").keyval
    assert "DEM of Difference" in info["title"]
    assert info["source1"].strip('"') == "dem_post"
    assert info["source2"].strip('"') == "dem_pre"
    history = tools.r_info(map="dod_meta", flags="h").text
    assert "r.dem.dod" in history
    assert "interp=bilinear" in history


def test_timestamps_propagate(tools):
    tools.r_mapcalc(expression="ts_pre = dem_pre")
    tools.r_mapcalc(expression="ts_post = dem_post")
    tools.r_timestamp(map="ts_pre", date="4 sep 2013 / 8 sep 2013")
    tools.r_timestamp(map="ts_post", date="14 sep 2022 / 29 oct 2022")
    tools.r_dem_dod(dem="ts_post", reference="ts_pre", output="dod_ts")
    assert tools.r_timestamp(map="dod_ts").text.strip() == "4 Sep 2013 / 29 Oct 2022"


def test_no_timestamp_without_input_timestamps(tools):
    tools.r_dem_dod(
        dem="dem_post", reference="dem_pre", output="dod_nots", overwrite=True
    )
    with pytest.raises(CalledModuleError):
        tools.r_timestamp(map="dod_nots")


def test_unit_mismatch_warns(tools):
    tools.r_mapcalc(expression="u_post = dem_post")
    tools.r_mapcalc(expression="u_pre = dem_pre")
    tools.r_support(map="u_post", units="meters")
    tools.r_support(map="u_pre", units="feet")
    result = tools.r_dem_dod(dem="u_post", reference="u_pre", output="dod_units")
    assert "Input units differ" in result.stderr
