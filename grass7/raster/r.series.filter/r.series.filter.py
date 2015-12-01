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
#%flag
#% key: c
#% description: Try to find optimal parameters for filtering
#% guisection: Parameters
#%end
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
#% descriptions: savgol; Savitzky–Golay filter; median; Median filter
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
#%option
#% key: opt_points
#% type: integer
#% answer: 50
#% required: no
#% multiple: no
#% description: Count of random points used for parameter optimization
#%end
#%option
#% key: diff_penalty
#% type: double
#% answer: 1.0
#% required: no
#% multiple: no
#% description: Penalty for difference between original and filtered signals
#%end
#%option
#% key: deriv_penalty
#% type: double
#% answer: 1.0
#% required: no
#% multiple: no
#% description: Penalty for big derivates of the filtered signal
#%end
#%option
#% key: iterations
#% type: integer
#% required: no
#% multiple: no
#% description: Number of iterations
#% answer: 1
#%end






import os
import sys

import numpy as np
from scipy.signal import savgol_filter
from scipy.signal import medfilt


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


def _filter(method, row_data, winsize, order, itercount):
    result = np.empty(row_data.shape)
    _, cols = row_data.shape
    for i in range(cols):
        arr = _fill_nulls(row_data[:, i])
        if method == 'savgol':
            for j in range(itercount):
                arr = savgol_filter(arr, winsize, order, mode='nearest')
        elif method == 'median':
            for j in range(itercount):
                arr = medfilt(arr, kernel_size=winsize)
        else:
            grass.fatal('The method is not implemented')
        result[:, i] = arr

    return result

def _non_zero(x):
    return x.nonzero()[0]

def _fill_nulls(arr):
    """Fill no-data values in arr
    Return np.array with filled data
    """
    nans = np.isnan(arr)
    if not all(nans):
        arr[nans] = np.interp(_non_zero(nans), _non_zero(~nans), arr[~nans])

    return arr

def fitting_quality(input_data, fitted_data, diff_penalty=1.0, deriv_penalty=1.0):
    """Returns penalty for fitted curves:
    :param input_data:      2d array of samples
    :param fitted_data:     result of the fitting
    :param diff_penalty:    penalty for difference between original data and fitted data
    :param deriv_penalty:   penalty for derivations of the fitted data
    """
    difference = np.nanmean(abs(input_data.flatten() - fitted_data.flatten()))
    deriv_diff = np.nanmean(abs(np.diff(fitted_data, axis=0).flatten()))

    return diff_penalty * difference + deriv_penalty * deriv_diff


def optimize_params(method, names, npoints, diff_penalty, deriv_penalty, itercount):
    """Perform crossvalidation:
        take 'npoints' random points,
        find winsize and order that minimize the quality function
    """

    reg = Region()
    map_count = len(names)
    input_data = np.empty((map_count, npoints), dtype=float)
    inputs = init_rasters(names)
    # Select sample data points
    try:
        open_rasters(inputs)
        i = attempt = 0
        while i < npoints:
            row = np.random.randint(reg.rows)
            col = np.random.randint(reg.cols)
            for map_num in range(len(inputs)):
                map = inputs[map_num]
                input_data[map_num, i] = get_val_or_nan(map, row=row, col=col)
            if not all(np.isnan(input_data[:, i])):
                i += 1
                attempt = 0
            else:
                attempt += 1
                grass.warning('Selected point contains NULL values in all input maps. Performing of selection another point.')
                if attempt >= npoints:
                    grass.fatal("Can't find points with non NULL data.")

    finally:
        close_rasters(inputs)

    # Find the optima
    best_winsize = best_order = None
    if method == 'savgol':
        best_winsize, best_order = _optimize_savgol(input_data, diff_penalty,
                                                    deriv_penalty, itercount)
    elif method == 'median':
        best_winsize = _optimize_median(input_data,
                                        diff_penalty, deriv_penalty, itercount)
    else:
        grass.fatal('The method is not implemented')

    return best_winsize, best_order


def _optimize_savgol(input_data, diff_penalty, deriv_penalty, itercount):
    """Find optimal params for savgol_filter.

    Returns winsize and order
    """
    map_count, npoints = input_data.shape
    best = np.inf
    best_winsize = best_order = None
    for winsize in range(5, map_count/2, 2):
        for order in range(2, min(winsize - 2, 10)):    # 10 is a 'magic' number: we don't want very hight polynomyal fitting usually
            test_data = np.copy(input_data)
            test_data = _filter('savgol', test_data, winsize, order, itercount)
            penalty = fitting_quality(input_data, test_data,
                                      diff_penalty, deriv_penalty)
            if penalty < best:
                best = penalty
                best_winsize, best_order = winsize, order

    return best_winsize, best_order

def _optimize_median(input_data, diff_penalty, deriv_penalty, itercount):
    """Find optimal params for median filter.

    Returns winsize
    """
    map_count, npoints = input_data.shape
    best = np.inf
    best_winsize = order = None
    for winsize in range(3, map_count/2, 2):
        test_data = np.copy(input_data)
        test_data = _filter('median', test_data, winsize, order, itercount)
        penalty = fitting_quality(input_data, test_data,
                                  diff_penalty, deriv_penalty)
        if penalty < best:
            best = penalty
            best_winsize = winsize

    return best_winsize


def filter(method, names, winsize, order, prefix, itercount):
    inputs = init_rasters(names)
    output_names = [prefix + name for name in names]
    outputs = init_rasters(output_names)
    try:
        open_rasters(outputs, write=True)
        open_rasters(inputs)

        reg = Region()
        for i in range(reg.rows):
            # import ipdb; ipdb.set_trace()
            row_data = np.array([_get_row_or_nan(r, i) for r in inputs])
            filtered_rows = _filter(method, row_data, winsize, order, itercount)
            for map_num in range(len(outputs)):
                map = outputs[map_num]
                row = filtered_rows[map_num, :]
                buf = Buffer(row.shape, map.mtype, row)
                map.put_row(i, buf)
    finally:
        close_rasters(outputs)
        close_rasters(inputs)


def get_val_or_nan(map, row, col):
    """
    Return map value of the cell or FNULL (if the cell is null)
    """
    value = map.get(row, col)
    if map.mtype == "CELL" and value == CNULL:
        value = FNULL
    return value


def _get_row_or_nan(raster, row_num):
    row = raster.get_row(row_num)
    if raster.mtype != 'CELL':
        return row
    nans = (row == CNULL)
    row = row.astype(np.float64)
    row[nans.astype(np.bool)] = np.nan
    return row

def main(options, flags):

    optimize = flags['c']

    method = options['method']

    xnames = options['input']
    xnames = xnames.split(',')

    winsize = options['winsize']
    winsize = int(winsize)

    order = options['order']
    order = int(order)

    opt_points = options['opt_points']
    opt_points = int(opt_points)

    diff_penalty = options['diff_penalty']
    diff_penalty = float(diff_penalty)

    deriv_penalty = options['deriv_penalty']
    deriv_penalty = float(deriv_penalty)

    itercount = options['iterations']
    itercount = int(itercount)

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

    if optimize:
        winsize, order = optimize_params(method, xnames, opt_points,
                                         diff_penalty, deriv_penalty, itercount)
        if winsize is None:
            grass.error("Optimization procedure doesn't convergence.")
            sys.exit(1)

    filter(method, xnames, winsize, order, res_prefix, itercount)

if __name__ == "__main__":
    options, flags = grass.parser()
    main(options, flags)
