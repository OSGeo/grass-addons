"""Tests for r.soils.rosetta.

Numeric checks require the offline ``rosetta-soil`` package; they are skipped
when it is not installed. The reference values below are ROSETTA version 3
predictions for a loam of sand=40, silt=40, clay=20 (model code 2) and the same
loam with bulk density 1.4 (model code 3).
"""

import pytest

from grass.exceptions import CalledModuleError
from grass.tools import Tools

# ROSETTA v3 reference values for the loam above.
LOAM_KSAT_MM_PER_HOUR = 5.128
LOAM_KSAT_CM_PER_DAY = 12.307
LOAM_THETA_S = 0.4040
LOAM_THETA_R = 0.0887
LOAM_BD_KSAT_CM_PER_DAY = 16.557


def _make_loam(tools):
    """Create constant sand/silt/clay rasters for a loam texture."""
    tools.r_mapcalc(expression="sand = 40.0", overwrite=True)
    tools.r_mapcalc(expression="silt = 40.0", overwrite=True)
    tools.r_mapcalc(expression="clay = 20.0", overwrite=True)


def _mean(tools, raster):
    return float(tools.r_univar(map=raster, flags="g").keyval["mean"])


def test_ksat_mm_per_hour(session):
    """Default ksat output is in mm/hr and matches the ROSETTA reference."""
    pytest.importorskip("rosetta")
    tools = Tools(session=session)
    _make_loam(tools)
    tools.r_soils_rosetta(
        sand="sand", silt="silt", clay="clay", ksat="ks", version=3, overwrite=True
    )
    assert _mean(tools, "ks") == pytest.approx(LOAM_KSAT_MM_PER_HOUR, abs=0.01)


def test_ksat_cm_per_day_units(session):
    """ksat_units=cm_per_day returns ROSETTA's native units (no conversion)."""
    pytest.importorskip("rosetta")
    tools = Tools(session=session)
    _make_loam(tools)
    tools.r_soils_rosetta(
        sand="sand",
        silt="silt",
        clay="clay",
        ksat="ks",
        ksat_units="cm_per_day",
        version=3,
        overwrite=True,
    )
    assert _mean(tools, "ks") == pytest.approx(LOAM_KSAT_CM_PER_DAY, abs=0.02)


def test_water_content_outputs(session):
    """theta_r and theta_s match the ROSETTA reference and are back-transformed."""
    pytest.importorskip("rosetta")
    tools = Tools(session=session)
    _make_loam(tools)
    tools.r_soils_rosetta(
        sand="sand",
        silt="silt",
        clay="clay",
        theta_r="tr",
        theta_s="ts",
        version=3,
        overwrite=True,
    )
    assert _mean(tools, "ts") == pytest.approx(LOAM_THETA_S, abs=0.005)
    assert _mean(tools, "tr") == pytest.approx(LOAM_THETA_R, abs=0.005)


def test_model_code_3_uses_bulk_density(session):
    """Adding bulk_density selects model code 3, changing the prediction."""
    pytest.importorskip("rosetta")
    tools = Tools(session=session)
    _make_loam(tools)
    tools.r_mapcalc(expression="bd = 1.4", overwrite=True)
    tools.r_soils_rosetta(
        sand="sand",
        silt="silt",
        clay="clay",
        bulk_density="bd",
        ksat="ks",
        ksat_units="cm_per_day",
        version=3,
        overwrite=True,
    )
    assert _mean(tools, "ks") == pytest.approx(LOAM_BD_KSAT_CM_PER_DAY, abs=0.05)


def test_null_propagates(session):
    """Cells NULL in any input are NULL in the output."""
    pytest.importorskip("rosetta")
    tools = Tools(session=session)
    tools.g_region(n=10, s=0, e=10, w=0, rows=10, cols=10)
    _make_loam(tools)
    # NULL out the western half of the sand map (5 of 10 columns).
    tools.r_mapcalc(expression="sand = if(col() <= 5, null(), 40.0)", overwrite=True)
    tools.r_soils_rosetta(
        sand="sand", silt="silt", clay="clay", ksat="ks", version=3, overwrite=True
    )
    stats = tools.r_univar(map="ks", flags="g").keyval
    assert int(stats["null_cells"]) == 50
    assert int(stats["n"]) == 50


def test_no_output_is_fatal(session):
    """Requesting no output map fails cleanly."""
    tools = Tools(session=session)
    _make_loam(tools)
    with pytest.raises(CalledModuleError):
        tools.r_soils_rosetta(sand="sand", silt="silt", clay="clay", version=3)


def test_water_content_requires_bulk_density(session):
    """The parser rejects water_content_33 without bulk_density (input gap)."""
    tools = Tools(session=session)
    _make_loam(tools)
    tools.r_mapcalc(expression="wc33 = 0.30", overwrite=True)
    with pytest.raises(CalledModuleError):
        tools.r_soils_rosetta(
            sand="sand",
            silt="silt",
            clay="clay",
            water_content_33="wc33",
            ksat="ks",
            version=3,
            overwrite=True,
        )
