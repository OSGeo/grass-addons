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


def test_stable_mask_requires_trim_percentile(session):
    """stable_mask without trim_percentile is rejected by the parser."""
    import subprocess

    env = session.env
    # The mask raster exists, so the parser rule is the only failure cause.
    gs.run_command("r.mapcalc", expression="stable = 1", overwrite=True, env=env)
    proc = gs.start_command(
        "r.dem.change",
        dem="dem_post",
        reference="dem_pre",
        lod="lod",
        output_dod="dod5",
        output_sig="dod_sig5",
        stable_mask="stable",
        overwrite=True,
        env=env,
        stderr=subprocess.PIPE,
    )
    _, err = proc.communicate()
    if isinstance(err, bytes):
        err = err.decode()
    assert proc.returncode != 0
    assert "requires" in err
    assert "trim_percentile" in err


def test_dod_input_path_equivalent(session, tmp_path):
    """dod= yields identical significance and volumes to dem+reference on
    the same difference, and the volume CSV carries the input name."""
    import csv as csvmod

    env = session.env
    csv_a = str(tmp_path / "vol_a.csv")
    csv_b = str(tmp_path / "vol_b.csv")
    gs.run_command(
        "r.mapcalc",
        expression="dod_pre2 = dem_post - dem_pre",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.dem.change",
        dem="dem_post",
        reference="dem_pre",
        lod="lod",
        output_dod="dod_ref",
        output_sig="sig_ref",
        volume_csv=csv_a,
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.dem.change",
        dod="dod_pre2",
        lod="lod",
        output_sig="sig_dod",
        volume_csv=csv_b,
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.mapcalc",
        expression="sig_diff = abs(sig_ref - sig_dod)",
        overwrite=True,
        env=env,
    )
    stats = gs.parse_command("r.univar", map="sig_diff", format="json", env=env)
    assert float(stats.get("max") or 0.0) < 1e-9

    with open(csv_a) as fa, open(csv_b) as fb:
        rows_a = list(csvmod.DictReader(fa))
        rows_b = list(csvmod.DictReader(fb))
    for ra, rb in zip(rows_a, rows_b, strict=True):
        assert abs(float(ra["value_m3"]) - float(rb["value_m3"])) < 1e-6
    assert rows_b[0]["input"] == "dod_pre2"
