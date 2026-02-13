"""Pytest fixtures for r.dem.icp.

Creates a temporary GRASS XY location and a small synthetic DEM pair with a
known horizontal/vertical offset.
"""

from types import SimpleNamespace

import pytest

import grass.script as gs


@pytest.fixture(scope="module")
def dem_icp_dataset(tmp_path_factory):
    """Create a GRASS session with synthetic DEMs for ICP alignment tests."""
    tmp_path = tmp_path_factory.mktemp("dem_icp")
    location = "test"

    ref = "reference"
    src = "source"
    mask = "stable_mask"

    # Known integer-cell shift (cols, rows) and vertical bias.
    # Note: In r.mapcalc offset syntax, [row_offset, col_offset].
    col_shift = 3
    row_shift = -2
    dz = 5.0

    gs.core._create_location_xy(tmp_path, location)  # pylint: disable=protected-access
    with gs.setup.init(tmp_path / location):
        # Keep this small so tests run quickly.
        gs.run_command("g.region", n=60, s=0, e=60, w=0, res=1, flags="a", quiet=True)

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

        yield SimpleNamespace(
            ref=ref,
            src=src,
            mask=mask,
            col_shift=col_shift,
            row_shift=row_shift,
            dz=dz,
        )
