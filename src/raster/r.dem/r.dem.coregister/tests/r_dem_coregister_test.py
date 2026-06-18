import csv
import shutil

import pytest

import grass.script as gs
from grass.exceptions import CalledModuleError


def _exists(name, env):
    return bool(gs.find_file(name, element="raster", env=env)["name"])


def test_pgcp_vertical_removes_bias(session):
    env = session.env
    gs.run_command(
        "r.dem.coregister",
        dem="dsm",
        reference="reference",
        roads="roads",
        output="dsm_coreg",
        method="pgcp_vertical",
        buffer=2.0,
        min_points=10,
        env=env,
    )
    assert _exists("dsm_coreg", env)
    # After removing the +0.5 m bias the co-registered DSM matches the
    # reference: mean residual should be near zero everywhere.
    gs.run_command(
        "r.mapcalc",
        expression="resid = dsm_coreg - reference",
        overwrite=True,
        env=env,
    )
    stats = gs.parse_command("r.univar", map="resid", format="json", env=env)
    assert abs(float(stats["mean"])) < 1e-6


def test_pgcp_vertical_writes_residual_csv(session, tmp_path):
    env = session.env
    csv_path = str(tmp_path / "pgcp.csv")
    gs.run_command(
        "r.dem.coregister",
        dem="dsm",
        reference="reference",
        roads="roads",
        output="dsm_coreg2",
        method="pgcp_vertical",
        buffer=2.0,
        min_points=10,
        bias_output=csv_path,
        flags="v",
        overwrite=True,
        env=env,
    )
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert set(rows[0].keys()) == {"x", "y", "residual_m"}
    # Every sampled residual is the known +0.5 m bias.
    assert all(abs(float(r["residual_m"]) - 0.5) < 1e-6 for r in rows)


def test_nk_requires_stable_mask(session):
    env = session.env
    # method=nk without a stable_mask must fail fast.
    with pytest.raises(CalledModuleError):
        gs.run_command(
            "r.dem.coregister",
            dem="dsm",
            reference="reference",
            roads="roads",
            output="dsm_nk_nomask",
            method="nk",
            min_points=10,
            env=env,
        )


def test_nk_runs(session):
    if not shutil.which("r.dem.nk"):
        pytest.skip("r.dem.nk not installed")
    env = session.env
    gs.run_command(
        "r.dem.coregister",
        dem="dsm",
        reference="reference",
        roads="roads",
        stable_mask="stable",
        output="dsm_nk",
        method="nk",
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    assert _exists("dsm_nk", env)


def test_nk_icp_runs(session):
    if not (shutil.which("r.dem.nk") and shutil.which("r.dem.icp")):
        pytest.skip("r.dem.nk and/or r.dem.icp not installed")
    env = session.env
    gs.run_command(
        "r.dem.coregister",
        dem="dsm",
        reference="reference",
        roads="roads",
        stable_mask="stable",
        output="dsm_nk_icp",
        method="nk_icp",
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    assert _exists("dsm_nk_icp", env)
