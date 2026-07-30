import csv

import grass.script as gs
import pytest


def _univar(name, env):
    return gs.parse_command("r.univar", map=name, format="json", env=env)


def test_raw_dod_and_significance(session):
    env = session.env
    gs.run_command(
        "r.dem.change",
        dem="dem_post",
        reference="dem_pre",
        lod="lod",
        output_dod="dod",
        output_sig="dod_sig",
        env=env,
    )
    # Raw DoD spans the full region (no nulls).
    dod = _univar("dod", env)
    assert int(dod["n"]) == 1600
    # Significant cells: the 11x11 block (121) plus the isolated spike (1).
    sig = _univar("dod_sig", env)
    assert int(sig["n"]) == 122
    assert float(sig["max"]) == pytest.approx(5.0)


def test_speckle_removal_drops_isolated_cell(session):
    env = session.env
    gs.run_command(
        "r.dem.change",
        dem="dem_post",
        reference="dem_pre",
        lod="lod",
        output_dod="dod2",
        output_sig="dod_sig_clean",
        flags="n",
        overwrite=True,
        env=env,
    )
    # The isolated +5 spike is removed; only the 121-cell block remains.
    sig = _univar("dod_sig_clean", env)
    assert int(sig["n"]) == 121
    assert float(sig["max"]) == pytest.approx(2.0)


def test_volume_csv(session, tmp_path):
    env = session.env
    csv_path = str(tmp_path / "vol.csv")
    gs.run_command(
        "r.dem.change",
        dem="dem_post",
        reference="dem_pre",
        lod="lod",
        output_dod="dod3",
        output_sig="dod_sig3",
        volume_csv=csv_path,
        flags="n",
        overwrite=True,
        env=env,
    )
    with open(csv_path) as f:
        rows = {r["metric"]: r for r in csv.DictReader(f)}
    # 121 cells of +2 m at 1 m^2 cells => 242 m^3 deposition, no erosion.
    assert float(rows["deposition"]["value_m3"]) == pytest.approx(242.0)
    assert float(rows["erosion"]["value_m3"]) == pytest.approx(0.0)
    assert float(rows["net"]["value_m3"]) == pytest.approx(242.0)


def test_trim_percentile_drops_blunder(session):
    env = session.env
    # Trimming below the spike magnitude removes it before thresholding.
    gs.run_command(
        "r.dem.change",
        dem="dem_post",
        reference="dem_pre",
        lod="lod",
        output_dod="dod4",
        output_sig="dod_sig4",
        trim_percentile=99,
        overwrite=True,
        env=env,
    )
    sig = _univar("dod_sig4", env)
    # The 99th percentile of |DoD| sits at 2.0, so the +5 spike is trimmed.
    assert float(sig["max"]) == pytest.approx(2.0)
