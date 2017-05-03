#!/usr/bin/env python
# -- coding: utf-8 --

"""
The module rlearn_rasters contains functions to
extract training data from GRASS rasters.

"""


from __future__ import absolute_import

import numpy as np
import tempfile

import grass.script as gscript
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.vector import VectorTopo
from grass.pygrass.utils import get_raster_for_points, pixel2coor


def extract(response, predictors, lowmem=False):
    """
    Samples a list of GRASS rasters using a labelled raster
    Per raster sampling

    Args
    ----
    response: String; GRASS raster with labelled pixels
    predictors: List of GRASS rasters containing explanatory variables
    lowmem: Boolean, use numpy memmap to query predictors

    Returns
    -------
    training_data: Numpy array of extracted raster values
    training_labels: Numpy array of labels
    is_train: Row and Columns of label positions
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
        gscript.fatal("GRASS response raster does not exist.... exiting")

    # determine number of predictor rasters
    n_features = len(predictors)

    # check to see if all predictors exist
    for i in range(n_features):
        if RasterRow(predictors[i]).exist() is not True:
            gscript.fatal("GRASS raster " + predictors[i] +
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

    return(training_data, training_labels, is_train)


def extract_points(gvector, grasters, field):
    """
    Extract values from grass rasters using vector points input

    Args
    ----
    gvector: character, name of grass points vector
    grasters: list of names of grass raster to query
    field: character, name of field in table to use as response variable

    Returns
    -------
    X: 2D numpy array of training data
    y: 1D numpy array with the response variable
    coordinates: 2D numpy array of sample coordinates
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

    # extract raster data
    X = np.zeros((points.num_primitives()['point'], len(grasters)), dtype=float)
    for i, raster in enumerate(grasters):
        rio = RasterRow(raster)
        values = np.asarray(get_raster_for_points(points, rio))
        coordinates = values[:, 1:3]
        X[:, i] = values[:, 3]

    # set any grass integer nodata values to NaN
    X[X == -2147483648] = np.nan

    # remove missing response data
    X = X[~np.isnan(y)]
    coordinates = coordinates[~np.isnan(y)]
    y = y[~np.isnan(y)]

    # close
    points.close()

    return(X, y, coordinates)


def predict(estimator, predictors, output, predict_type='raw',
            index=None, rowincr=25, n_jobs=-2):
    """
    Prediction on list of GRASS rasters using a fitted scikit learn model

    Args
    ----
    estimator: scikit-learn estimator object
    predictors: list of GRASS rasters
    output: Name of GRASS raster to output classification results
    predict_type: character, 'raw' for classification/regression;
                  'prob' for class probabilities
    index: Optional, list of class indices to export
    rowincr: Integer of raster rows to process at one time
    n_jobs: Number of processing cores
    """

    from sklearn.externals.joblib import Parallel, delayed

    # convert potential single index to list
    if isinstance(index, int): index = [index]

    # open predictors as list of rasterrow objects
    current = Region()
    n_features = len(predictors)
    rasstack = [0] * n_features

    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() is True:
            rasstack[i].open('r')
        else:
            gscript.fatal("GRASS raster " + predictors[i] +
                          " does not exist.... exiting")

    # -------------------------------------------------------------------------
    # parallel prediction
    # -------------------------------------------------------------------------

    # create lists of row increments
    row_mins, row_maxs = [], []
    for row in range(0, current.rows, rowincr):
        if row+rowincr > current.rows:
            rowincr = current.rows - row
        row_mins.append(row)
        row_maxs.append(row+rowincr)

    # perform predictions on lists of row increments in parallel
    predictions = Parallel(n_jobs=n_jobs)(
        delayed(__predict_parallel)
        (estimator, predictors, predict_type, current, row_min, row_max)
        for row_min, row_max in zip(row_mins, row_maxs))

    # unpack the results
    results = []
    ftypes = []
    for block in predictions:
        results.append(block[0])
        ftypes.append(block[1])

    # -------------------------------------------------------------------------
    #  writing of predicted results for classification
    # -------------------------------------------------------------------------
    if predict_type == 'raw':
        classification = RasterRow(output)
        classification.open('w', ftypes[0], overwrite=True)

        # write the classification result
        for result_block in results:
            for row in range(result_block.shape[0]):
                newrow = Buffer((result_block.shape[1],), mtype=ftypes[0])
                newrow[:] = result_block[row, :]
                classification.put_row(newrow)

    # -------------------------------------------------------------------------
    # writing of predicted results for probabilities
    # -------------------------------------------------------------------------
    if predict_type == 'prob':
        # determine number of classes
        if index is None:
            index = range(results[0].shape[2])
            n_classes = len(index)
        else:
            n_classes = len(np.unique(index))

        # create and open RasterRow objects for probabilities
        prob_out_raster = [0] * n_classes
        prob = [0] * n_classes
        for iclass, label in enumerate(index):
            prob_out_raster[iclass] = output + '_classPr' + str(label)
            prob[iclass] = RasterRow(prob_out_raster[iclass])
            prob[iclass].open('w', 'FCELL', overwrite=True)

        # write the class probability results
        for results_proba_block in results:
            for iclass, label in enumerate(index):
                result_proba_class = results_proba_block[:, :, label]

                for row in range(result_proba_class.shape[0]):
                    newrow = Buffer((result_proba_class.shape[1],), mtype='FCELL')
                    newrow[:] = result_proba_class[row, :]
                    prob[iclass].put_row(newrow)

    # -------------------------------------------------------------------------
    # close all maps
    # -------------------------------------------------------------------------
    if predict_type == 'raw': classification.close()
    if predict_type == 'prob':
        try:
            for iclass in range(n_classes):
                prob[iclass].close()
        except:
            pass


def __predict_parallel(estimator, predictors, predict_type, current, row_min, row_max):
    """
    Performs prediction on range of rows in grass rasters

    Args
    ----
    estimator: scikit-learn estimator object
    predictors: list of GRASS rasters
    predict_type: character, 'raw' for classification/regression;
                  'prob' for class probabilities
    current: current region settings
    row_min, row_max: Range of rows of grass rasters to perform predictions

    Returns
    -------
    result: 2D (classification) or 3D numpy array (class probabilities) of predictions
    ftypes: data storage type
    """

    # initialize output
    result, ftype, mask = None, None, None

    # open grass rasters
    n_features = len(predictors)
    rasstack = [0] * n_features

    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() is True:
            rasstack[i].open('r')
        else:
            gscript.fatal("GRASS raster " + predictors[i] +
                          " does not exist.... exiting")

    # loop through each row, and each band and add to 2D img_np_row
    img_np_row = np.zeros((row_max-row_min, current.cols, n_features))
    for row in range(row_min, row_max):
        for band in range(n_features):
            img_np_row[row-row_min, :, band] = np.array(rasstack[band][row])

    # create mask
    img_np_row[img_np_row == -2147483648] = np.nan
    mask = np.zeros((img_np_row.shape[0], img_np_row.shape[1]))
    for feature in range(n_features):
        invalid_indexes = np.nonzero(np.isnan(img_np_row[:, :, feature]))
        mask[invalid_indexes] = np.nan

    # reshape each row-band matrix into a n*m array
    nsamples = (row_max-row_min) * current.cols
    flat_pixels = img_np_row.reshape((nsamples, n_features))

    # remove NaNs prior to passing to scikit-learn predict
    flat_pixels = np.nan_to_num(flat_pixels)

    # perform prediction for classification/regression
    if predict_type == 'raw':
        result = estimator.predict(flat_pixels)
        result = result.reshape((row_max-row_min, current.cols))

        # determine nodata value and grass raster type
        if result.dtype == 'float':
            nodata = np.nan
            ftype = 'FCELL'
        else:
            nodata = -2147483648
            ftype = 'CELL'

        # replace NaN values so that the prediction does not have a border
        result[np.nonzero(np.isnan(mask))] = nodata

    # perform prediction for class probabilities
    if predict_type == 'prob':
        result = estimator.predict_proba(flat_pixels)
        result = result.reshape((row_max-row_min, current.cols, result.shape[1]))
        result[np.nonzero(np.isnan(mask))] = np.nan

    # close maps
    for i in range(n_features):
        rasstack[i].close()

    return (result, ftype)

