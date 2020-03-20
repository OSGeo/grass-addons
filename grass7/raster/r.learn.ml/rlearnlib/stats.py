#!/usr/bin/env python
# -- coding: utf-8 --

"""The statistics module contains simple wrappers around GRASS modules for statistical functions
on raster maps"""

import os
import numpy as np
from subprocess import PIPE
from grass.pygrass.modules.shortcuts import raster as r
from grass.script.utils import parse_key_val


class StatisticsMixin(object):
    def covar(self, correlation=False):
        """
        Outputs a covariance or correlation matrix for the layers within the RasterStack object

        Parameters
        ----------
        correlation : logical, default is False.
            Whether to produce a correlation matrix or a covariance matrix.

        Returns
        -------
        numpy.ndarray
            Covariance/correlation matrix of the layers within the RasterStack with diagonal and
            upper triangle positions set to nan.
        """

        if correlation is True:
            flags = "r"
        else:
            flags = ""

        corr = r.covar(map=self.names, flags=flags, stdout_=PIPE)
        corr = corr.outputs.stdout.strip().split(os.linesep)[1:]
        corr = [i.strip() for i in corr]
        corr = [i.split(" ") for i in corr]
        corr = np.asarray(corr, dtype=np.float32)

        np.fill_diagonal(corr, np.nan)
        corr[np.triu_indices(corr.shape[0], 0)] = np.nan

        return corr

    def linear_regression(self, x, y):
        """
        Simple wrapper around the GRASS GIS module r.regression.line
        
        Parameters
        ----------
        x : str
            Name of GRASS GIS raster map to use as the x-variable. Has to be within the RasterStack
            object.
        
        y : str
            Name of GRASS GIS raster map to use as the y-variable.
        
        Returns
        -------
        dict
            Containing the regression statistics.
        """

        regr = r.regression_line(
            mapx=x, mapy=y, flags="g", stdout_=PIPE
        ).outputs.stdout.strip()

        regr = parse_key_val(regr, sep="=")

        return regr

    def multiple_regression(
        self, xs, y, estimates=None, residuals=None, overwrite=False
    ):
        """
        Simple wrapper around the GRASS GIS module r.regression.multi
        
        Parameters
        ----------
        x : str
            Name of GRASS GIS raster map to use as the x-variable. Has to be within the RasterStack
            object.
        
        y : str
            Name of GRASS GIS raster map to use as the y-variable.
        
        estimates : str (opt)
            Optionally specify a name to create a raster map of the regression estimate.
        
        residuals : str (opt)
            Optionally specify a name to create a raste rmap of the residuals.
        
        overwrite : bool (default is False)
            Overwrite existing GRASS GIS rasters for estimates and residuals.
        
        Returns
        -------
        dict
            Containing the regression statistics.
        """

        regr = r.regression_multi(
            mapx=xs,
            mapy=y,
            flags="g",
            residuals=residuals,
            estimates=estimates,
            overwrite=overwrite,
            stdout_=PIPE,
        ).outputs.stdout.strip()

        regr = parse_key_val(regr, sep="=")

        return regr
