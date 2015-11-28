#!/usr/bin/env python
# -*- coding: utf-8  -*-
#
############################################################################
#
# MODULE:       r.series.filter
#
# AUTHOR(S):    Dmitry Kolesov <kolesov.dm@gmail.com>
#
# PURPOSE:      Perform filtering of raster time series X
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Perform filtering of raster time series X (in time domain)
#% overwrite: yes
#%End
#%option
#% key: input
#% type: string
#% gisprompt: list of raster names
#% description: Raster names of equally spaced time series.
#% required : yes
#% multiple: yes
#%end
#%option
#% key: result_prefix
#% type: string
#% gisprompt: prefix of result raster names
#% description: Prefix for raster names of filtered X(t)
#% required : yes
#% multiple: no
#%end
#%option
#% key: method
#% type: string
#% required : no
#% multiple: no
#% answer: savgol
#% description: Used method
#% descriptions: savgol; Savitzky–Golay filter
#%end
#%option
#% key: winsize
#% type: integer
#% answer: 5
#% required: no
#% multiple: no
#% description: Length of running window for the filter
#%end
#%option
#% key: order
#% type: integer
#% answer: 2
#% required: no
#% multiple: no
#% description: Order of the Savitzky-Golay filter
#%end



import os
import sys

import numpy as np
from scipy.signal import savgol_filter

if "GISBASE" not in os.environ:
    sys.stderr.write("You must be in GRASS GIS to run this program.\n")
    sys.exit(1)

import grass.script as grass
from grass.pygrass import raster
from grass.pygrass.raster.buffer import Buffer
from grass.exceptions import OpenError
from grass.pygrass.gis.region import Region

CNULL = -2147483648  # null value for CELL maps
FNULL = np.nan       # null value for FCELL and DCELL maps


def init_rasters(names):
    """Get list of raster names,
    return array of the rasters
    """
    rasters = []
    for name in names:
        r = raster.RasterSegment(name)
        rasters.append(r)
    return rasters


def open_rasters(raster_list, write=False):
    for r in raster_list:
        try:
            if write:
                if r.exist():
                    r.open('w', 'DCELL', overwrite=grass.overwrite())
                else:
                    r.open('w', 'DCELL')
            else:
                r.open()
        except OpenError:
            grass.error("Can't open raster %s" % (r.name, ))
            sys.exit(1)

def close_rasters(raster_list):
    for r in raster_list:
        if r.is_open():
            r.close()


def _filter(row_data, winsize, order):
    result = np.empty(row_data.shape)
    _, cols = row_data.shape
    for i in range(cols):
        arr = _fill_nulls(row_data[:, i])
        arr = savgol_filter(arr, winsize, order)
        result[:, i] = arr

    return result

def _fill_nulls(arr):
    """Fill no-data values in arr
    Return np.array with filled data
    """
    nz = lambda z: z.nonzero()[0]
    nans = np.isnan(arr)
    arr[nans] = np.interp(nz(nans), nz(~nans), arr[~nans])

    return arr

def filter(names, winsize, order, prefix):
    inputs = init_rasters(names)
    output_names = [prefix + name for name in names]
    outputs = init_rasters(output_names)
    try:
        open_rasters(outputs, write=True)
        open_rasters(inputs)

        reg = Region()
        for i in range(reg.rows):
            row_data = np.array([r.get_row(i) for r in inputs])
            filtered_rows = _filter(row_data, winsize, order)
            # import ipdb; ipdb.set_trace()
            for map_num in range(len(outputs)):
                map = outputs[map_num]
                row = filtered_rows[map_num]
                buf = Buffer(row.shape, map.mtype, row)
                map.put_row(i, buf)
    finally:
        close_rasters(outputs)
        close_rasters(inputs)

def main(options, flags):
    xnames = options['input']
    xnames = xnames.split(',')

    winsize = options['winsize']
    winsize = int(winsize)

    order = options['order']
    order = int(order)

    res_prefix = options['result_prefix']

    N = len(xnames)
    if N < winsize:
        grass.error("The used running window size is to big. Decrease the paramether or add more rasters to the series.")
        sys.exit(1)

    _, rem = divmod(winsize, 2)
    if rem == 0:
        grass.error("Window length must be odd.")
        sys.exit(1)

    if order >= winsize:
        grass.error("Order of the filter must be less than window length")

    filter(xnames, winsize, order, res_prefix)

if __name__ == "__main__":
    options, flags = grass.parser()
    main(options, flags)
