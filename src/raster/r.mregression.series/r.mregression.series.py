#!/usr/bin/env python
# -*- coding: utf-8  -*-
#
############################################################################
#
# MODULE:       r.mregression.series
#
# AUTHOR(S):    Dmitry Kolesov <kolesov.dm@gmail.com>
#
# PURPOSE:      multiple regression between several time series
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %Module
# % description: Calculates multiple regression between time series: Y(t) = b1*X1(t) + ... + bn*Xn(t).
# % overwrite: yes
# % keyword: raster
# % keyword: statistics
# % keyword: regression
# %End
# %option
# % key: samples
# % type: string
# % gisprompt: file with settings in csv format
# % description: File contains list of input and output rasters
# % required : yes
# % multiple: no
# %end
# %option
# % key: result_prefix
# % type: string
# % gisprompt: prefix for names of result rasters
# % description: Prefix for names of result raster (rasters of regression coefficients)
# % required : yes
# % multiple: no
# %end
# %option
# % key: model
# % type: string
# % gisprompt: model
# % description: model type: ols (ordinary least squares), rlm (robust linear model)
# % required: no
# % answer: ols
# % multiple: no
# %end


import os
import sys

import csv
import numpy as np
from numpy.linalg.linalg import LinAlgError

# statsmodels lazy imported at the end of the file

if "GISBASE" not in os.environ:
    sys.stderr.write("You must be in GRASS GIS to run this program.\n")
    sys.exit(1)

import grass.script as grass
from grass.pygrass import raster
from grass.pygrass.gis.region import Region

CNULL = -2147483648  # null value for CELL maps
FNULL = np.nan  # null value for FCELL and DCELL maps


def get_val_or_null(map, row, col):
    """
    Return map value of the cell or FNULL (if the cell is null)
    """
    value = map.get(row, col)
    if map.mtype == "CELL" and value == CNULL:
        value = FNULL
    return value


def fit(y, x, model="ols"):
    """Ordinary least squares.

    :param x:   MxN matrix of data points
    :param x:   numpy.array
    :param y:   vector of M output values
    :param y:   numpy.array
    :return:    vector b of coefficients (x * b = y)
    """
    # if a X sample has nan value,
    # then the fitting procedure crashes.
    # Delete no-data samples from the data
    factor_count = x.shape[1]
    nan_idx = np.logical_or(np.isnan(y), np.isnan(x).any(axis=1))
    if nan_idx.any():
        y = y[~nan_idx]
        x = x[~nan_idx]
    if x.shape[0] < x.shape[1]:
        # The system can't be solved
        return [FNULL for i in range(factor_count)]

    if model == "ols":
        model = sm.OLS(y, x)
    elif model == "rlm":
        model = sm.robust.robust_linear_model.RLM(y, x)
    else:
        raise NotImplementedError("Model %s doesn't implemented" % (model,))

    try:
        results = model.fit()
        coefs = results.params
    except LinAlgError:
        coefs = [FNULL for i in range(factor_count)]
    return coefs


def get_sample_names(filename, delimiter=","):
    """
    Analyse settings file, returns
    """
    with open(filename) as settings:
        reader = csv.reader(settings, delimiter=delimiter)
        headers = reader.next()
        inputs = []
        outputs = []
        for row in reader:
            outputs.append(row[0])
            inputs.append(row[1:])

    return headers, outputs, inputs


class DataModel(object):
    def __init__(self, headers, Y, X, prefix, restype="FCELL"):
        """Linear Least Square model  Y = X * b + e
        X are [[],.., []] of raster names
        Y are [] of raster names

        b are rasters of the regression coeficients, the rasters
            have type restype
        e are the errors of the model (the class doesn't compute e)

        header is [] of the variable names.
        names of the 'b' rasters are constructed as
            prefix+variable_name (see header)
        """
        if len(set(headers)) != len(headers):
            grass.error("The names of the variables are not unique!")

        self.mtype = restype

        self.x_headers = headers[1:]  # Names of the coefficient
        self.b_names = [prefix + name for name in self.x_headers]
        self.y_names = Y  # Names of Y rasters
        self.x_names = X  # Names of X rasters

        self.sample_count = len(self.y_names)
        self.factor_count = len(self.x_names[0])

        self._y_rasters = []
        self._x_rasters = []
        self._b_rasters = []
        self._init_rasters()

    def x(self, s, f):
        """Return input map (X) from sample number s and factor number f."""
        return self._x_rasters[s][f]

    def y(self, s):
        """Return output map (Y) from sample number s."""
        return self._y_rasters[s]

    def b(self, s):
        return self._b_rasters[s]

    def _init_rasters(self):
        for name in self.y_names:
            map = raster.RasterSegment(name)
            if not map.exist():
                raise ValueError("Raster map %s doesn't exist" % (name,))
            self._y_rasters.append(map)

        for names in self.x_names:
            maps = []
            for name in names:
                map = raster.RasterSegment(name)
                if not map.exist():
                    raise ValueError("Raster map %s doesn't exist" % (name,))
                maps.append(map)
            # Check count of X samples
            assert len(maps) == self.factor_count

            self._x_rasters.append(maps)

        # Rasters of the regression coefitients
        for i in range(self.factor_count):
            name = self.b_names[i]
            map = raster.RasterSegment(name)
            self._b_rasters.append(map)

    def open_rasters(self, overwrite):
        for i in range(self.sample_count):
            map = self.y(i)
            map.open()

        for j in range(self.factor_count):
            map = self.b(j)
            map.open("w", mtype=self.mtype, overwrite=overwrite)
            for i in range(self.sample_count):
                map = self.x(i, j)
                map.open()

    def close_rasters(self):
        for i in range(self.sample_count):
            map = self.y(i)
            map.close()

        for j in range(self.factor_count):
            map = self.b(j)
            map.close()
            for i in range(self.sample_count):
                map = self.x(i, j)
                map.close()

    def get_sample(self, row, col):
        """Return X and Y matrices for one pixel sample"""
        X = np.empty((self.sample_count, self.factor_count))
        Y = np.empty(self.sample_count)
        for snum in range(self.sample_count):
            y = self.y(snum)
            Y[snum] = get_val_or_null(y, row, col)
            for fnum in range(self.factor_count):
                x = self.x(snum, fnum)
                X[snum, fnum] = get_val_or_null(x, row, col)

        return Y, X

    def fit(self, model="ols", overwrite=None):
        try:
            reg = Region()
            self.open_rasters(overwrite=overwrite)
            rows, cols = reg.rows, reg.cols
            for r in range(rows):
                for c in range(cols):
                    Y, X = self.get_sample(r, c)
                    coefs = fit(Y, X, model)
                    for i in range(self.factor_count):
                        b = self.b(i)
                        b.put(r, c, coefs[i])
        finally:
            self.close_rasters()


def main(options, flags):
    samples = options["samples"]
    res_pref = options["result_prefix"]
    model_type = options["model"]
    if not os.path.isfile(samples):
        sys.stderr.write("File '%s' doesn't exist.\n" % (samples,))
        sys.exit(1)

    headers, outputs, inputs = get_sample_names(samples)

    model = DataModel(headers, outputs, inputs, res_pref)
    model.fit(model=model_type, overwrite=grass.overwrite())
    sys.exit(0)


if __name__ == "__main__":
    options, flags = grass.parser()

    # lazy import (global to avoid import in a loop)
    try:
        import statsmodels.api as sm
    except ImportError:
        grass.fatal(
            _("Cannot import statsmodels." " Install python-statmodels package first")
        )

    main(options, flags)
