from types import SimpleNamespace

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def icp_session(tmp_path_factory):
    """A single GRASS XY session with the region used by all ICP datasets."""
    tmp_path = tmp_path_factory.mktemp("dem_icp")
    location = "test"

    gs.core._create_location_xy(tmp_path, location)  # pylint: disable=protected-access
    with gs.setup.init(tmp_path / location) as session:
        # Keep this small so tests run quickly.
        gs.run_command("g.region", n=60, s=0, e=60, w=0, res=1, flags="a", quiet=True)
        yield session


@pytest.fixture(scope="module")
def dem_icp_dataset(icp_session):
    """Synthetic DEM pair with a known horizontal shift and vertical bias."""
    ref = "reference"
    src = "source"
    mask = "stable_mask"

    # Known integer-cell shift (cols, rows) and vertical bias.
    # Note: In r.mapcalc offset syntax, [row_offset, col_offset].
    col_shift = 3
    row_shift = -2
    dz = 5.0

    # Non-planar synthetic surface so horizontal shifts are observable.
    gs.mapcalc(
        (
            "{ref} = 0.2 * x() + 0.1 * y() "
            "+ 5.0 * sin(x() / 8.0) + 3.0 * cos(y() / 11.0)"
        ).format(ref=ref),
        quiet=True,
    )

    gs.mapcalc(
        "{src} = {ref}[{ro},{co}] + {dz}".format(
            src=src, ref=ref, ro=row_shift, co=col_shift, dz=dz
        ),
        quiet=True,
    )

    # Stable-terrain mask: use only cells where both rasters have values.
    gs.mapcalc(
        "{mask} = if(!isnull({ref}) && !isnull({src}), 1, null())".format(
            mask=mask, ref=ref, src=src
        ),
        quiet=True,
    )

    return SimpleNamespace(
        ref=ref,
        src=src,
        mask=mask,
        col_shift=col_shift,
        row_shift=row_shift,
        dz=dz,
    )


@pytest.fixture(scope="module")
def dem_icp_yaw_dataset(icp_session):
    """Synthetic DEM pair related by a known yaw rotation about the center.

    The source is the reference surface sampled at coordinates rotated by
    ``yaw_deg`` about the region center, so a pure 4-DoF yaw alignment should
    recover the reference. Exercises the rotation path in the resample stage
    (regression test for the inverse-yaw sign).
    """
    ref = "reference_yaw"
    src = "source_yaw"
    mask = "stable_mask_yaw"
    yaw_deg = 4.0

    cx, cy = 30.0, 30.0
    # Non-planar, non-symmetric surface so yaw is observable.
    surface = "0.2 * {x} + 0.1 * {y} + 5.0 * sin({x} / 8.0) + 3.0 * cos({y} / 11.0)"

    gs.mapcalc(
        "{ref} = {expr}".format(ref=ref, expr=surface.format(x="x()", y="y()")),
        quiet=True,
    )

    # Coordinates rotated by yaw_deg about (cx, cy); mapcalc trig is in degrees.
    xr = "({cx} + cos({a}) * (x() - {cx}) - sin({a}) * (y() - {cy}))".format(
        cx=cx, cy=cy, a=yaw_deg
    )
    yr = "({cy} + sin({a}) * (x() - {cx}) + cos({a}) * (y() - {cy}))".format(
        cx=cx, cy=cy, a=yaw_deg
    )
    gs.mapcalc(
        "{src} = {expr}".format(src=src, expr=surface.format(x=xr, y=yr)),
        quiet=True,
    )

    gs.mapcalc(
        "{mask} = if(!isnull({ref}) && !isnull({src}), 1, null())".format(
            mask=mask, ref=ref, src=src
        ),
        quiet=True,
    )

    return SimpleNamespace(ref=ref, src=src, mask=mask, yaw_deg=yaw_deg)
