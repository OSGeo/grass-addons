#!/usr/bin/env python
# -- coding: utf-8 --

"""
The module rlearn_prediction contains functions to
perform predictions on GRASS rasters
"""

from __future__ import absolute_import
import numpy as np
import grass.script as gs
from grass.pygrass.gis.region import Region


def predict(estimator, predictors, output, predict_type='raw', index=None,
            class_labels=None, overwrite=False, rowincr=25, n_jobs=-2):
    """
    Prediction on list of GRASS rasters using a fitted scikit learn model

    Args
    ----
    estimator (object): scikit-learn estimator object
    predictors (list): Names of GRASS rasters
    output (string): Name of GRASS raster to output classification results
    predict_type (string): 'raw' for classification/regression;
        'prob' for class probabilities
    index (list): Optional, list of class indices to export
    class_labels (1d numpy array): Optional, class labels
    overwrite (boolean): enable overwriting of existing raster
    n_jobs (integer): Number of processing cores;
        -1 for all cores; -2 for all cores-1
    """

    from sklearn.externals.joblib import Parallel, delayed
    from grass.pygrass.raster import numpy2raster

    # TODO
    # better memory efficiency and use of memmap for parallel
    # processing
    #from sklearn.externals.joblib.pool import has_shareable_memory

    # first unwrap the estimator from any potential pipelines or gridsearchCV
    if type(estimator).__name__ == 'Pipeline':
       clf_type = estimator.named_steps['classifier']
    else:
        clf_type = estimator

    if type(clf_type).__name__ == 'GridSearchCV' or \
    type(clf_type).__name__ == 'RandomizedSearchCV':
        clf_type = clf_type.best_estimator_

    # check name against already multithreaded classifiers
    if type(clf_type).__name__ in [
       'RandomForestClassifier',
        'RandomForestRegressor',
        'ExtraTreesClassifier',
        'ExtraTreesRegressor',
        'KNeighborsClassifier']:
       n_jobs = 1

    # convert potential single index to list
    if isinstance(index, int): index = [index]

    # open predictors as list of rasterrow objects
    current = Region()

    # create lists of row increments
    row_mins, row_maxs = [], []
    for row in range(0, current.rows, rowincr):
        if row+rowincr > current.rows:
            rowincr = current.rows - row
        row_mins.append(row)
        row_maxs.append(row+rowincr)

    # perform predictions on lists of row increments in parallel
    prediction = Parallel(n_jobs=n_jobs, max_nbytes=None)(
        delayed(__predict_parallel2)
        (estimator, predictors, predict_type, current, row_min, row_max)
        for row_min, row_max in zip(row_mins, row_maxs))
    prediction = np.vstack(prediction)

    # determine raster dtype
    if prediction.dtype == 'float':
        ftype = 'FCELL'
    else:
        ftype = 'CELL'

    #  writing of predicted results for classification
    if predict_type == 'raw':
        numpy2raster(array=prediction, mtype=ftype, rastname=output,
                     overwrite=True)

    # writing of predicted results for probabilities
    if predict_type == 'prob':

        # use class labels if supplied
        # else output predictions as 0,1,2...n
        if class_labels is None:
            class_labels = range(prediction.shape[2])

        # output all class probabilities if subset is not specified
        if index is None:
            index = class_labels

        # select indexes of predictions 3d numpy array to be exported to rasters
        selected_prediction_indexes = [i for i, x in enumerate(class_labels) if x in index]

        # write each 3d of numpy array as a probability raster
        for pred_index, label in zip(selected_prediction_indexes, index):
            rastername = output + '_' + str(label)
            numpy2raster(array=prediction[:, :, pred_index], mtype='FCELL',
                         rastname=rastername, overwrite=overwrite)


def __predict_parallel2(estimator, predictors, predict_type, current, row_min, row_max):
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

    from grass.pygrass.raster import RasterRow

    # initialize output
    result, mask = None, None

    # open grass rasters
    n_features = len(predictors)
    rasstack = [0] * n_features

    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() is True:
            rasstack[i].open('r')
        else:
            gs.fatal("GRASS raster " + predictors[i] +
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
        else:
            nodata = -2147483648

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

    return result
