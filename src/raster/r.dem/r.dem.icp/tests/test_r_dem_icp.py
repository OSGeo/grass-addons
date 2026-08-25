"""Tests for r.dem.icp (pytest).

These tests run r.dem.icp inside a temporary GRASS session created by the
fixture in conftest.py.
"""

from pathlib import Path

import grass.script as gs


def _rms_of_difference(diff_raster):
    stats = gs.parse_command("r.univar", flags="g", map=diff_raster)
    mean = float(stats["mean"])
    stddev = float(stats["stddev"])
    return (mean * mean + stddev * stddev) ** 0.5


def test_icp_reduces_residual_rms(dem_icp_dataset, tmp_path):
    out = "aligned"

    diff_before = "diff_before"
    diff_after = "diff_after"

    # Compute baseline residuals on the stable mask.
    gs.mapcalc(
        "{d} = if({m}, {s} - {r}, null())".format(
            d=diff_before,
            m=dem_icp_dataset.mask,
            s=dem_icp_dataset.src,
            r=dem_icp_dataset.ref,
        ),
        quiet=True,
    )
    rms_before = _rms_of_difference(diff_before)

    transform_out = Path(tmp_path) / "transform.txt"
    stats_out = Path(tmp_path) / "stats.txt"

    gs.run_command(
        "r.dem.icp",
        reference=dem_icp_dataset.ref,
        source=dem_icp_dataset.src,
        output=out,
        mask=dem_icp_dataset.mask,
        dof=4,
        levels=2,
        stride=2,
        max_iterations=25,
        trim=0.8,
        huber=1.0,
        tolerance=1e-6,
        distance_max=0,
        slope_max=90,
        init_dx=0,
        init_dy=0,
        init_dz=0,
        init_yaw=0,
        transform_out=str(transform_out),
        stats_out=str(stats_out),
        quiet=True,
    )

    gs.mapcalc(
        "{d} = if({m}, {o} - {r}, null())".format(
            d=diff_after, m=dem_icp_dataset.mask, o=out, r=dem_icp_dataset.ref
        ),
        quiet=True,
    )
    rms_after = _rms_of_difference(diff_after)

    # ICP should significantly reduce the residual RMS.
    assert rms_after < 0.5 * rms_before

    # Optional outputs should be created when requested.
    assert transform_out.exists()
    assert stats_out.exists()


def test_icp_corrects_yaw_rotation(dem_icp_yaw_dataset, tmp_path):
    """A yaw-rotated source must be rotated back, not further."""
    out = "aligned_yaw"
    diff_before = "diff_before_yaw"
    diff_after = "diff_after_yaw"

    gs.mapcalc(
        "{d} = if({m}, {s} - {r}, null())".format(
            d=diff_before,
            m=dem_icp_yaw_dataset.mask,
            s=dem_icp_yaw_dataset.src,
            r=dem_icp_yaw_dataset.ref,
        ),
        quiet=True,
    )
    rms_before = _rms_of_difference(diff_before)

    gs.run_command(
        "r.dem.icp",
        reference=dem_icp_yaw_dataset.ref,
        source=dem_icp_yaw_dataset.src,
        output=out,
        mask=dem_icp_yaw_dataset.mask,
        dof=4,
        levels=3,
        stride=2,
        max_iterations=50,
        trim=0.9,
        huber=1.0,
        tolerance=1e-7,
        distance_max=0,
        slope_max=90,
        quiet=True,
    )

    gs.mapcalc(
        "{d} = if({m}, {o} - {r}, null())".format(
            d=diff_after,
            m=dem_icp_yaw_dataset.mask,
            o=out,
            r=dem_icp_yaw_dataset.ref,
        ),
        quiet=True,
    )
    rms_after = _rms_of_difference(diff_after)

    # Correct inverse-yaw collapses the residual;
    assert rms_after < 0.3 * rms_before
