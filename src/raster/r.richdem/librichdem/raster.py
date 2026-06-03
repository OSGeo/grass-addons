"""Conversion between GRASS rasters and RichDEM rdarray objects."""

import os
import tempfile

import numpy as np
import grass.script as gs
import richdem as rd

_NO_DATA = -9999.0


def rdarray_from_grass(name):
    """Read a GRASS raster map into a RichDEM rdarray."""
    region = gs.region()
    geotransform = np.array(
        [
            region["w"],
            region["ewres"],
            0,
            region["n"],
            0,
            -region["nsres"],
        ]
    )

    rows = region["rows"]
    cols = region["cols"]

    # r.out.bin -f bytes=8: IEEE-754 double-precision, native byte order.
    # null=-9999 writes _NO_DATA for GRASS null cells.
    tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
    tmp.close()
    try:
        gs.run_command(
            "r.out.bin",
            flags="f",
            input=name,
            output=tmp.name,
            bytes=8,
            null=_NO_DATA,
            overwrite=True,
            quiet=True,
        )
        data = np.fromfile(tmp.name, dtype="float64").reshape(rows, cols).copy()
    finally:
        os.unlink(tmp.name)

    return rd.rdarray(data, no_data=_NO_DATA, geotransform=geotransform)


def rdarray_to_grass(rda, name, overwrite=False):
    """Write a RichDEM rdarray to a GRASS raster map."""
    data = np.array(rda, dtype="float64")
    # Convert no_data sentinel and any algorithm-produced NaN to _NO_DATA so
    # that r.in.bin can identify and null them out.
    # NaN == NaN is False in IEEE 754, so the explicit | np.isnan(data) guard
    # catches NaN values produced by C++ edge cases.
    # (r.univar misreports max=nan on GRASS <= 8.3.2 when the true maximum is
    # exactly 0.0 — a separate upstream bug fixed in OSGeo/grass PR #3512,
    # included in GRASS 8.4.0.)
    data[(data == rda.no_data) | np.isnan(data)] = _NO_DATA

    region = gs.region()
    rows, cols = data.shape

    tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
    try:
        tmp.write(data.tobytes())
        tmp.close()
        gs.run_command(
            "r.in.bin",
            flags="d",
            input=tmp.name,
            output=name,
            north=region["n"],
            south=region["s"],
            east=region["e"],
            west=region["w"],
            rows=rows,
            cols=cols,
            anull=_NO_DATA,
            overwrite=overwrite,
            quiet=True,
        )
    finally:
        os.unlink(tmp.name)
