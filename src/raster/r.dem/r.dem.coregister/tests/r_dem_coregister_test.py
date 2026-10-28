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
        pgcp="roads",
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
        pgcp="roads",
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
            pgcp="roads",
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
        pgcp="roads",
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
        pgcp="roads",
        stable_mask="stable",
        output="dsm_nk_icp",
        method="nk_icp",
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    assert _exists("dsm_nk_icp", env)


def test_icp_runs(session):
    if not shutil.which("r.dem.icp"):
        pytest.skip("r.dem.icp not installed")
    env = session.env
    gs.run_command(
        "r.dem.coregister",
        dem="dsm",
        reference="reference",
        pgcp="roads",
        stable_mask="stable",
        output="dsm_icp",
        method="icp",
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    assert _exists("dsm_icp", env)


def test_icp_runs_without_stable_mask(session):
    if not shutil.which("r.dem.icp"):
        pytest.skip("r.dem.icp not installed")
    env = session.env
    # stable_mask is optional for method=icp; ICP runs over all terrain.
    gs.run_command(
        "r.dem.coregister",
        dem="dsm",
        reference="reference",
        pgcp="roads",
        output="dsm_icp_nomask",
        method="icp",
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    assert _exists("dsm_icp_nomask", env)


def test_transform_output_and_replay(session, tmp_path):
    if not (shutil.which("r.dem.nk") and shutil.which("r.dem.icp")):
        pytest.skip("r.dem.nk and/or r.dem.icp not installed")
    env = session.env
    xform = str(tmp_path / "xf.txt")
    # Non-degenerate terrain: the radial cone in the fixture is ill-conditioned
    # for the ICP yaw estimate, so build a varied surface with full aspect range.
    gs.run_command(
        "r.mapcalc",
        expression="ref_v = 5.0 * sin(col() * 18.0) + 5.0 * cos(row() * 18.0)",
        overwrite=True,
        env=env,
    )
    # Two SfM surfaces sharing a 1-cell east shift but different vertical bias.
    gs.run_command(
        "r.mapcalc",
        expression="sfm_dtm_v = ref_v[0,-1] + 0.5",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.mapcalc",
        expression="sfm_dsm_v = ref_v[0,-1] + 1.0",
        overwrite=True,
        env=env,
    )
    gs.run_command("r.mapcalc", expression="stable_v = 1", overwrite=True, env=env)
    gs.run_command(
        "r.mapcalc",
        expression="road_rv = if(row() == 25, 1, null())",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.to.vect",
        input="road_rv",
        output="roads_v",
        type="line",
        overwrite=True,
        env=env,
    )

    # Solve the full chain on the DTM and write the transform.
    gs.run_command(
        "r.dem.coregister",
        dem="sfm_dtm_v",
        reference="ref_v",
        pgcp="roads_v",
        stable_mask="stable_v",
        method="nk_icp",
        output="dtm_coreg_v",
        transform_output=xform,
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    with open(xform) as f:
        text = f.read()
    assert "method=nk_icp" in text
    assert "nk_dx=" in text
    assert "icp_tx=" in text

    # Replay onto the DSM; horizontal is shared, vertical re-estimated per surface.
    gs.run_command(
        "r.dem.coregister",
        dem="sfm_dsm_v",
        reference="ref_v",
        pgcp="roads_v",
        apply_transform=xform,
        output="dsm_coreg_v",
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    assert _exists("dsm_coreg_v", env)
    gs.run_command(
        "r.mapcalc",
        expression="resid2 = abs(dsm_coreg_v - ref_v)",
        overwrite=True,
        env=env,
    )
    stats = gs.parse_command("r.univar", map="resid2", format="json", env=env)
    # The +1.0 m DSM bias and the shift are both removed: small residual.
    assert float(stats["mean"]) < 0.2


def test_icp_transform_output_and_replay(session, tmp_path):
    if not shutil.which("r.dem.icp"):
        pytest.skip("r.dem.icp not installed")
    env = session.env
    xform = str(tmp_path / "xf_icp.txt")
    # Varied surface with full aspect range so the ICP yaw estimate is well posed.
    gs.run_command(
        "r.mapcalc",
        expression="ref_vi = 5.0 * sin(col() * 18.0) + 5.0 * cos(row() * 18.0)",
        overwrite=True,
        env=env,
    )
    # Two SfM surfaces sharing a 1-cell east shift but different vertical bias.
    gs.run_command(
        "r.mapcalc",
        expression="sfm_dtm_vi = ref_vi[0,-1] + 0.5",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.mapcalc",
        expression="sfm_dsm_vi = ref_vi[0,-1] + 1.0",
        overwrite=True,
        env=env,
    )
    gs.run_command("r.mapcalc", expression="stable_vi = 1", overwrite=True, env=env)
    gs.run_command(
        "r.mapcalc",
        expression="road_rvi = if(row() == 25, 1, null())",
        overwrite=True,
        env=env,
    )
    gs.run_command(
        "r.to.vect",
        input="road_rvi",
        output="roads_vi",
        type="line",
        overwrite=True,
        env=env,
    )

    # Solve PGCP + ICP on the DTM and write the transform.
    gs.run_command(
        "r.dem.coregister",
        dem="sfm_dtm_vi",
        reference="ref_vi",
        pgcp="roads_vi",
        stable_mask="stable_vi",
        method="icp",
        output="dtm_coreg_vi",
        transform_output=xform,
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    with open(xform) as f:
        text = f.read()
    assert "method=icp" in text
    # The icp method carries no N&K horizontal component.
    assert "nk_dx=0.0000000000" in text
    assert "icp_tx=" in text

    # Replay onto the DSM; ICP horizontal is shared, vertical re-estimated.
    gs.run_command(
        "r.dem.coregister",
        dem="sfm_dsm_vi",
        reference="ref_vi",
        pgcp="roads_vi",
        apply_transform=xform,
        output="dsm_coreg_vi",
        buffer=2.0,
        min_points=10,
        overwrite=True,
        env=env,
    )
    assert _exists("dsm_coreg_vi", env)
    gs.run_command(
        "r.mapcalc",
        expression="resid_icp = abs(dsm_coreg_vi - ref_vi)",
        overwrite=True,
        env=env,
    )
    stats = gs.parse_command("r.univar", map="resid_icp", format="json", env=env)
    # The +1.0 m DSM bias and the shift are both removed: small residual.
    assert float(stats["mean"]) < 0.2
