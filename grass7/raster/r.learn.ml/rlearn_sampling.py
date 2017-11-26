#!/usr/bin/env python
# -- coding: utf-8 --

"""
The module rlearn_sampling contains functions to
extract training data from GRASS rasters.
"""

from __future__ import absolute_import
import numpy as np
import tempfile
import grass.script as gs
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.vector import VectorTopo
from grass.pygrass.utils import get_raster_for_points, pixel2coor


def extract_pixels(response, predictors, lowmem=False, na_rm=False):
    """

    Samples a list of GRASS rasters using a labelled raster
    Per raster sampling

    Args
    ----
    response (string): Name of GRASS raster with labelled pixels
    predictors (list): List of GRASS raster names containing explanatory variables
    lowmem (boolean): Use numpy memmap to query predictors
    na_rm (boolean): Remove samples containing NaNs

    Returns
    -------
    training_data (2d numpy array): Extracted raster values
    training_labels (1d numpy array): Numpy array of labels
    is_train (2d numpy array): Row and Columns of label positions

    """

    current = Region()

    # open response raster as rasterrow and read as np array
    if RasterRow(response).exist() is True:
        roi_gr = RasterRow(response)
        roi_gr.open('r')

        if lowmem is False:
            response_np = np.array(roi_gr)
        else:
            response_np = np.memmap(
                tempfile.NamedTemporaryFile(),
                dtype='float32', mode='w+',
                shape=(current.rows, current.cols))
            response_np[:] = np.array(roi_gr)[:]
    else:
        gs.fatal("GRASS response raster does not exist.... exiting")

    # determine number of predictor rasters
    n_features = len(predictors)

    # check to see if all predictors exist
    for i in range(n_features):
        if RasterRow(predictors[i]).exist() is not True:
            gs.fatal("GRASS raster " + predictors[i] +
                          " does not exist.... exiting")

    # check if any of those pixels are labelled (not equal to nodata)
    # can use even if roi is FCELL because nodata will be nan
    is_train = np.nonzero(response_np > -2147483648)
    training_labels = response_np[is_train]
    n_labels = np.array(is_train).shape[1]

    # Create a zero numpy array of len training labels
    if lowmem is False:
        training_data = np.zeros((n_labels, n_features))
    else:
        training_data = np.memmap(tempfile.NamedTemporaryFile(),
                                  dtype='float32', mode='w+',
                                  shape=(n_labels, n_features))

    # Loop through each raster and sample pixel values at training indexes
    if lowmem is True:
        feature_np = np.memmap(tempfile.NamedTemporaryFile(),
                               dtype='float32', mode='w+',
                               shape=(current.rows, current.cols))

    for f in range(n_features):
        predictor_gr = RasterRow(predictors[f])
        predictor_gr.open('r')

        if lowmem is False:
            feature_np = np.array(predictor_gr)
        else:
            feature_np[:] = np.array(predictor_gr)[:]

        training_data[0:n_labels, f] = feature_np[is_train]

        # close each predictor map
        predictor_gr.close()

    # convert any CELL maps no datavals to NaN in the training data
    for i in range(n_features):
        training_data[training_data[:, i] == -2147483648] = np.nan

    # convert indexes of training pixels from tuple to n*2 np array
    is_train = np.array(is_train).T
    for i in range(is_train.shape[0]):
        is_train[i, :] = np.array(pixel2coor(tuple(is_train[i]), current))

    # close the response map
    roi_gr.close()

    # remove samples containing NaNs
    if na_rm is True:
        if np.isnan(training_data).any() == True:
            gs.message('Removing samples with NaN values in the raster feature variables...')
        training_labels = training_labels[~np.isnan(training_data).any(axis=1)]
        is_train = is_train[~np.isnan(training_data).any(axis=1)]
        training_data = training_data[~np.isnan(training_data).any(axis=1)]

    return(training_data, training_labels, is_train)


def extract_points(gvector, grasters, field, na_rm=False):
    """

    Extract values from grass rasters using vector points input

    Args
    ----
    gvector (string): Name of grass points vector
    grasters (list): Names of grass raster to query
    field (string): Name of field in table to use as response variable
    na_rm (boolean): Remove samples containing NaNs

    Returns
    -------
    X (2d numpy array): Training data
    y (1d numpy array): Array with the response variable
    coordinates (2d numpy array): Sample coordinates

    """

    # open grass vector
    points = VectorTopo(gvector.split('@')[0])
    points.open('r')

    # create link to attribute table
    points.dblinks.by_name(name=gvector)

    # extract table field to numpy array
    table = points.table
    cur = table.execute("SELECT {field} FROM {name}".format(field=field, name=table.name))
    y = np.array([np.isnan if c is None else c[0] for c in cur])
    y = np.array(y, dtype='float')

    # extract raster data
    X = np.zeros((points.num_primitives()['point'], len(grasters)), dtype=float)
    for i, raster in enumerate(grasters):
        rio = RasterRow(raster)
        if rio.exist() is False:
            gs.fatal('Raster {x} does not exist....'.format(x=raster))
        values = np.asarray(get_raster_for_points(points, rio))
        coordinates = values[:, 1:3]
        X[:, i] = values[:, 3]
        rio.close()

    # set any grass integer nodata values to NaN
    X[X == -2147483648] = np.nan

    # remove missing response data
    X = X[~np.isnan(y)]
    coordinates = coordinates[~np.isnan(y)]
    y = y[~np.isnan(y)]

    # int type if classes represented integers
    if all(y % 1 == 0) is True:
        y = np.asarray(y, dtype='int')

    # close
    points.close()

    # remove samples containing NaNs
    if na_rm is True:
        if np.isnan(X).any() == True:
            gs.message('Removing samples with NaN values in the raster feature variables...')

        y = y[~np.isnan(X).any(axis=1)]
        coordinates = coordinates[~np.isnan(X).any(axis=1)]
        X = X[~np.isnan(X).any(axis=1)]

    return(X, y, coordinates)
