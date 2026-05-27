"""Conversion between GRASS rasters and RichDEM rdarray objects."""

import numpy as np
import grass.script as gs
from grass.pygrass.raster import RasterRow
from grass.pygrass.raster.buffer import Buffer
import richdem as rd

_NO_DATA = -9999.0


def rdarray_from_grass(name):
    """Read a GRASS raster map into a RichDEM rdarray."""
    region = gs.region()
    geotransform = np.array([
        region["w"], region["ewres"], 0,
        region["n"], 0, -region["nsres"],
    ])

    r = RasterRow(name)
    r.open()
    data = np.array([np.array(r[i]) for i in range(r.info.rows)], dtype="float64")
    r.close()

    # GRASS nulls come back as NaN for float types; replace with _NO_DATA
    data[np.isnan(data)] = _NO_DATA

    return rd.rdarray(data, no_data=_NO_DATA, geotransform=geotransform)


def rdarray_to_grass(rda, name, overwrite=False):
    """Write a RichDEM rdarray to a GRASS raster map."""
    data = np.array(rda, dtype="float64")
    # Convert no_data sentinel and any algorithm-produced NaN to GRASS null.
    # NaN == NaN is False in IEEE 754, so a plain == rda.no_data check would
    # silently pass through NaN values produced by C++ edge cases; the
    # explicit | np.isnan(data) guard catches those and normalises them to
    # Python's canonical quiet NaN, which PyGRASS writes as GRASS DCELL null.
    # (r.univar misreports max=nan on GRASS <= 8.3.2 when the true maximum is
    # exactly 0.0 — a separate upstream bug fixed in OSGeo/grass PR #3512,
    # included in GRASS 8.4.0.)
    data[(data == rda.no_data) | np.isnan(data)] = np.nan

    w = RasterRow(name)
    w.open("w", mtype="DCELL", overwrite=overwrite)
    for row in data:
        buf = Buffer(row.shape, mtype="DCELL")
        buf[:] = row
        w.put_row(buf)
    w.close()
