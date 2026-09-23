"""Tests for v.surf.rst.cv"""

import json
import subprocess

import pytest

import grass.script as gs


def run_cv(session, points=None, flags="", **kwargs):
    """Run v.surf.rst.cv and return (stdout, stderr)"""
    kwargs.setdefault("npmin", session.npmin)
    kwargs.setdefault("segmax", session.segmax)
    kwargs.setdefault("nprocs", 3)
    process = gs.start_command(
        "v.surf.rst.cv",
        point_cloud=points or session.points,
        flags=flags or None,
        overwrite=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs,
    )
    stdout, stderr = process.communicate()
    assert process.returncode == 0, gs.decode(stderr)
    return gs.decode(stdout), gs.decode(stderr)


def run_cv_json(session, points=None, flags="", **kwargs):
    stdout, stderr = run_cv(session, points, flags, format="json", **kwargs)
    return json.loads(stdout), stderr


@pytest.fixture(scope="module")
def grid_result(session):
    """Shared 2x2 grid run"""
    return run_cv_json(session, tension=20, smooth=[0.1, 1.0])


def test_json_structure(session, grid_result):
    data, _ = grid_result
    assert data["input"] == session.points
    assert data["method"] == "grid"
    assert len(data["results"]) == 2
    for row in data["results"]:
        assert row["error"] is None
        assert isinstance(row["tension"], float)
        assert isinstance(row["smooth"], float)
        assert row["n"] == session.npoints
        for key in ("rmse", "mae", "nmad", "me", "median", "p68", "p95", "dnorm"):
            assert isinstance(row[key], float)
        assert row["rmse"] >= row["mae"] > 0
    assert set(data["best"]) == {"rmse", "mae", "nmad"}


def test_best_is_minimum(grid_result):
    data, _ = grid_result
    for metric in ("rmse", "mae", "nmad"):
        best = data["best"][metric][metric]
        assert best == min(row[metric] for row in data["results"])


def test_csv_output_file(session, tmp_path):
    output_file = tmp_path / "results.csv"
    stdout, _ = run_cv(
        session,
        tension=[20, 40],
        smooth=0.1,
        format="csv",
        output_file=str(output_file),
    )
    lines = output_file.read_text().splitlines()
    assert lines[0].startswith("tension,smooth,")
    assert len(lines) == 3
    assert stdout.splitlines() == lines


def test_determinism_across_nprocs(session, grid_result):
    data, _ = grid_result
    serial, _ = run_cv_json(session, tension=20, smooth=[0.1, 1.0], nprocs=1)
    for parallel_row, serial_row in zip(data["results"], serial["results"]):
        assert parallel_row["smooth"] == serial_row["smooth"]
        assert parallel_row["rmse"] == pytest.approx(serial_row["rmse"], rel=1e-9)
        assert parallel_row["n"] == serial_row["n"]


def test_selected_smoothing_increases_with_noise(session):
    """More noise in the samples must select stronger smoothing"""
    best_smooth = []
    for name in ("clean", "noisy", "very_noisy"):
        data, _ = run_cv_json(
            session,
            points=session.points_by_noise[name],
            tension=40,
            smooth=[0.01, 0.1, 1.0, 10.0],
        )
        best_smooth.append(data["best"]["rmse"]["smooth"])
    assert best_smooth == sorted(best_smooth)
    assert best_smooth[0] == pytest.approx(0.01)


def test_refine_at_least_as_good_as_grid(session):
    tension = [10, 40, 160]
    smooth = [0.01, 0.1, 1.0]
    grid, _ = run_cv_json(session, tension=tension, smooth=smooth)
    refined, _ = run_cv_json(
        session, tension=tension, smooth=smooth, method="refine", levels=2
    )
    assert len(refined["results"]) > len(grid["results"])
    assert refined["best"]["rmse"]["rmse"] <= grid["best"]["rmse"]["rmse"] + 1e-9


def test_refine_boundary_warning(session):
    """A minimum on the edge of the searched range must be flagged"""
    _, stderr = run_cv_json(
        session,
        points=session.points_by_noise["clean"],
        tension=40,
        smooth=[1.0, 10.0],
        method="refine",
        levels=1,
    )
    assert "boundary" in stderr


def test_failed_combination_recorded(session):
    """A failing parameter combination becomes a row, not a fatal error"""
    data, stderr = run_cv_json(session, tension=40, smooth=0.1, dmin=[1, 2000])
    errors = [row["error"] for row in data["results"]]
    assert None in errors
    assert any(errors)
    assert "incomplete" in stderr
    best = data["best"]["rmse"]
    assert best["error"] is None


def test_dmin_sweep_reports_sample_change(session):
    data, stderr = run_cv_json(session, tension=40, smooth=0.1, dmin=[1, 60])
    counts = {row["dmin"]: row["n"] for row in data["results"]}
    assert counts[1.0] > counts[60.0]
    assert "not directly comparable" in stderr


def test_subsample_seeded_and_reproducible(session):
    runs = [
        run_cv_json(session, tension=40, smooth=0.1, npoints=120, seed=7)[0]
        for _ in range(2)
    ]
    for data in runs:
        assert data["subsample"] == {"npoints": 120, "seed": 7}
        assert data["results"][0]["n"] == 120
    assert runs[0]["results"][0]["rmse"] == runs[1]["results"][0]["rmse"]


def test_scale_dependent_tension_reported(session):
    data, _ = run_cv_json(session, flags="t", tension=40, smooth=0.1)
    row = data["results"][0]
    assert data["scale_dependent_tension"] is True
    assert row["tension_rescaled"] == pytest.approx(
        row["tension"] * row["dnorm"] / 1000.0
    )


def test_scalex_without_theta_rejected(session):
    """Anisotropy scaling without an angle must fail before any runs"""
    process = gs.start_command(
        "v.surf.rst.cv",
        point_cloud=session.points,
        tension=40,
        smooth=0.1,
        scalex=2.0,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = process.communicate()
    assert process.returncode != 0
    assert "theta" in gs.decode(stderr)
