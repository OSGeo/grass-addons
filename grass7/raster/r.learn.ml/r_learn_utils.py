#!/usr/bin/env python
# -- coding: utf-8 --

from __future__ import absolute_import
import numpy as np
import os
import tempfile
from copy import deepcopy
from numpy.random import RandomState
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.modules.shortcuts import imagery as im
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.table import Link
from grass.pygrass.utils import get_raster_for_points, pixel2coor
import grass.script as gscript
from subprocess import PIPE

def specificity_score(y_true, y_pred):
    """
    Calculate specificity score

    Args
    ----
    y_true: 1D numpy array of truth values
    y_pred: 1D numpy array of predicted classes

    Returns
    -------
    specificity: specificity score
    """
    from sklearn.metrics import confusion_matrix

    cm = confusion_matrix(y_true, y_pred)
    tn = float(cm[0][0])
    fp = float(cm[0][1])

    return tn/(tn+fp)


def varimp_permutation(estimator, X_test, y_true,
                       n_permutations, scorer,
                       random_state):

    """
    Method to perform permutation-based feature importance during
    cross-validation (cross-validation is applied externally to this
    method)

    Procedure is:
    1. Pass fitted estimator and test partition X y
    2. Assess AUC on the test partition (bestauc)
    3. Permute each variable and assess the difference between bestauc and
       the messed-up variable
    4. Repeat (3) for many random permutations
    5. Average the repeats

    Args
    ----
    estimator: estimator that has been fitted to a training partition
    X_test, y_true: data and labels from a test partition
    n_permutations: number of random permutations to apply
    scorer: scikit-learn metric function to use
    random_state: seed to pass to the numpy random.seed

    Returns
    -------
    scores: scores for each predictor following permutation
    """

    # calculate score on original variables without permutation
    # determine best metric type for binary/multiclass/regression scenarios
    y_pred = estimator.predict(X_test)
    best_score = scorer(y_true, y_pred)

    np.random.seed(seed=random_state)
    rstate = RandomState(random_state)
    scores = np.zeros((n_permutations, X_test.shape[1]))

    # outer loop to repeat the pemutation rep times
    for rep in range(n_permutations):

        # inner loop to permute each predictor variable and assess
        # difference in auc
        for i in range(X_test.shape[1]):
            Xscram = np.copy(X_test)
            Xscram[:, i] = rstate.choice(X_test[:, i], X_test.shape[0])

            # fit the model on the training data and predict the test data
            y_pred = estimator.predict(Xscram)
            scores[rep, i] = best_score-scorer(y_true, y_pred)
            if scores[rep, i] < 0:
                scores[rep, i] = 0

    # average the repetitions
    scores = scores.mean(axis=0)

    return scores


def cross_val_scores(estimator, X, y, groups=None, sample_weight=None, cv=3,
                     scoring='accuracy', feature_importances=False,
                     n_permutations=25, models=False, random_state=None):
    """
    Stratified Kfold and GroupFold cross-validation using multiple
    scoring metrics and permutation feature importances

    Args
    ----
    estimator: Scikit learn estimator
    X: 2D numpy array of training data
    y: 1D numpy array representing response variable
    groups: 1D numpy array containing group labels
    sample_weight: 1D numpy array[n_samples,] of sample weights
    cv: Integer of cross-validation folds or sklearn.model_selection object
    sampling: Over- or under-sampling object with fit_sample method
    scoring: List of performance metrics to use
    feature_importances: Boolean to perform permutation-based importances
    n_permutations: Number of permutations during feature importance
    models: Boolean, return a list of the fitted models
    random_state: Seed to pass to the random number generator
    """

    from sklearn import metrics
    from sklearn.model_selection import (
        RandomizedSearchCV, GridSearchCV, StratifiedKFold)

    # deepcopy estimator
    estimator = deepcopy(estimator)
    fitted_models = []

    # create model_selection method
    if isinstance(cv, int): cv = StratifiedKFold(n_splits=cv)

    # create dictionary of lists to store metrics
    if isinstance(scoring, basestring): scoring = [scoring]
    scores = dict.fromkeys(scoring)
    scores = {key: [] for key, value in scores.iteritems()}
    scoring_methods = {'accuracy': metrics.accuracy_score,
                       'balanced_accuracy': metrics.recall_score,
                       'average_precision': metrics.average_precision_score,
                       'brier_loss': metrics.brier_score_loss,
                       'kappa': metrics.cohen_kappa_score,
                       'f1': metrics.f1_score,
                       'fbeta': metrics.fbeta_score,
                       'hamming_loss': metrics.hamming_loss,
                       'jaccard_similarity': metrics.jaccard_similarity_score,
                       'log_loss': metrics.log_loss,
                       'matthews_corrcoef': metrics.matthews_corrcoef,
                       'precision': metrics.precision_score,
                       'recall': metrics.recall_score,
                       'specificity': specificity_score,
                       'roc_auc': metrics.roc_auc_score,
                       'zero_one_loss': metrics.zero_one_loss,
                       'r2': metrics.r2_score,
                       'neg_mean_squared_error': metrics.mean_squared_error}

    byclass_methods = {'f1': metrics.f1_score,
                       'fbeta': metrics.fbeta_score,
                       'precision': metrics.precision_score,
                       'recall': metrics.recall_score}

    # create diction to store byclass metrics results
    n_classes = len(np.unique(y))
    labels = np.unique(y)
    byclass_scores = dict.fromkeys(byclass_methods)
    byclass_scores = {key: np.zeros((0, n_classes)) for key, value in byclass_scores.iteritems()}

    # remove any byclass_scorers that are not in the scoring list
    byclass_scores = {key: value for key, value in byclass_scores.iteritems() if key in scores}

    # check if remaining scorers are valid sklearn metrics
    for i in scores.keys():
        try:
            list(scoring_methods.keys()).index(i)
        except:
            print('Scoring ' + i + ' is not a valid scoring method')
            print('Valid methods are:')
            print(scoring_methods.keys())

    # set averaging type for global binary or multiclass scores
    if len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
        average = 'binary'
    else:
        average = 'macro'

    # create np array to store feature importance scores
    if feature_importances is True:
        fimp = np.zeros((cv.get_n_splits(), X.shape[1]))
        fimp[:] = np.nan
    else:
        fimp = None

    # generate Kfold indices
    if groups is None:
        k_fold = cv.split(X, y)
    else:
        k_fold = cv.split(X, y, groups=groups)

    # store predictions and indices
    predictions = np.zeros((len(y), 3)) # y_true, y_pred, fold

    # train on k-1 folds and test of k folds
    fold = 0
    for train_indices, test_indices in k_fold:

        # create training and test folds
        X_train, X_test = X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]
        if groups is not None: groups_train = groups[train_indices]
        else: groups_train = None

        # subset training and test fold sample_weight
        if sample_weight is not None: weights = sample_weight[train_indices]

        # train estimator
        if groups is not None and isinstance(estimator, (RandomizedSearchCV, GridSearchCV)) is True:
            if sample_weight is None: estimator.fit(X_train, y_train, groups=groups_train)
            else: estimator.fit(X_train, y_train, groups=groups_train, sample_weight=weights)
        else:
            if sample_weight is None: estimator.fit(X_train, y_train)
            else: estimator.fit(X_train, y_train, sample_weight=weights)

        # optionally store the fitted models on each resample
        if models is True: fitted_models.append(deepcopy(estimator))

        # prediction of test fold
        y_pred = estimator.predict(X_test)
        predictions[test_indices, 0] = y_test
        predictions[test_indices, 1] = y_pred
        predictions[test_indices, 2] = fold

        # calculate global performance metrics
        for m in scores.keys():
            # metrics that require probabilties
            if m == 'brier_loss' or m == 'roc_auc':
                y_prob = estimator.predict_proba(X_test)[:, 1]
                scores[m] = np.append(
                    scores[m], scoring_methods[m](y_test, y_prob))

            # metrics that have no averaging for multiclass
            elif m == 'kappa' or m == 'specificity' or m == 'accuracy' \
            or m == 'hamming_loss' or m == 'jaccard_similarity' \
            or m == 'log_loss' or m == 'zero_one_loss' or m == 'matthews_corrcoef':
                scores[m] = np.append(
                    scores[m], scoring_methods[m](y_test, y_pred))

            # balanced accuracy
            elif m == 'balanced_accuracy':
                scores[m] = np.append(
                    scores[m], scoring_methods[m](
                        y_test, y_pred, average='macro'))

            # metrics that have averaging for multiclass
            else:
                scores[m] = np.append(
                    scores[m], scoring_methods[m](
                        y_test, y_pred, average=average))

        # calculate per-class performance metrics
        for key in byclass_scores.keys():
            byclass_scores[key] = np.vstack((
                byclass_scores[key], byclass_methods[key](
                    y_test, y_pred, labels=labels, average=None)))

        # feature importances using permutation
        if feature_importances is True:
            if bool((np.isnan(fimp)).all()) is True:
                fimp = varimp_permutation(
                    estimator, X_test, y_test, n_permutations,
                    scoring_methods[scoring[0]],
                    random_state)
            else:
                fimp = np.row_stack(
                    (fimp, varimp_permutation(
                        estimator, X_test, y_test,
                        n_permutations, scoring_methods[scoring[0]],
                        random_state)))
        fold += 1

    return(scores, byclass_scores, fimp, fitted_models, predictions)


def predict(estimator, predictors, output, predict_type='raw',
            index=None, rowincr=25):
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
    """

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

    # Prediction using blocks of rows per iteration
    for rowblock in range(0, current.rows, rowincr):
        gscript.percent(rowblock, current.rows, rowincr)

        # check that the row increment does not exceed the number of rows
        if rowblock+rowincr > current.rows:
            rowincr = current.rows - rowblock
        img_np_row = np.zeros((rowincr, current.cols, n_features))

        # loop through each row, and each band and add to 2D img_np_row
        for row in range(rowblock, rowblock+rowincr, 1):
            for band in range(n_features):
                img_np_row[row-rowblock, :, band] = \
                    np.array(rasstack[band][row])

        # create mask
        img_np_row[img_np_row == -2147483648] = np.nan
        mask = np.zeros((img_np_row.shape[0], img_np_row.shape[1]))
        for feature in range(n_features):
            invalid_indexes = np.nonzero(np.isnan(img_np_row[:, :, feature]))
            mask[invalid_indexes] = np.nan

        # reshape each row-band matrix into a n*m array
        nsamples = rowincr * current.cols
        flat_pixels = img_np_row.reshape((nsamples, n_features))

        # remove NaNs prior to passing to scikit-learn predict
        flat_pixels = np.nan_to_num(flat_pixels)

        # perform prediction for classification/regression
        if predict_type == 'raw':
            result = estimator.predict(flat_pixels)
            result = result.reshape((rowincr, current.cols))

            # determine nodata value and grass raster type
            if result.dtype == 'float':
                nodata = np.nan
                ftype = 'FCELL'
            else:
                nodata = -2147483648
                ftype = 'CELL'

            # replace NaN values so that the prediction does not have a border
            result[np.nonzero(np.isnan(mask))] = nodata

            # on first iteration create the RasterRow object
            if rowblock == 0:
                if predict_type == 'raw':
                    classification = RasterRow(output)
                    classification.open('w', ftype, overwrite=True)

            # write the classification result
            for row in range(rowincr):
                newrow = Buffer((result.shape[1],), mtype=ftype)
                newrow[:] = result[row, :]
                classification.put_row(newrow)

        # perform prediction for class probabilities
        if predict_type == 'prob':
            result_proba = estimator.predict_proba(flat_pixels)

            # on first loop determine number of probability classes
            # and open rasterrow objects for writing
            if rowblock == 0:
                if index is None:
                    index = range(result_proba.shape[1])
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

            for iclass, label in enumerate(index):
                result_proba_class = result_proba[:, label]
                result_proba_class = result_proba_class.reshape((rowincr, current.cols))
                result_proba_class[np.nonzero(np.isnan(mask))] = np.nan

                for row in range(rowincr):
                    newrow = Buffer((result_proba_class.shape[1],), mtype='FCELL')
                    newrow[:] = result_proba_class[row, :]
                    prob[iclass].put_row(newrow)

    # close all maps
    for i in range(n_features): rasstack[i].close()
    if predict_type == 'raw': classification.close()
    if predict_type == 'prob':
        try:
            for iclass in range(n_classes):
                prob[iclass].close()
        except:
            pass


def model_classifiers(estimator, random_state, n_jobs, p, weights=None):
    """
    Provides the classifiers and parameters using by the module

    Args
    ----
    estimator: Name of estimator
    random_state: Seed to use in randomized components
    n_jobs: Integer, number of processing cores to use
    p: Dict, containing classifier setttings
    weights: None, or 'balanced' to add class_weights

    Returns
    -------
    clf: Scikit-learn classifier object
    mode: Flag to indicate whether classifier performs classification or
          regression
    """

    from sklearn.linear_model import LogisticRegression
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
    from sklearn.naive_bayes import GaussianNB
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    from sklearn.ensemble import (
        RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier,
        ExtraTreesRegressor)
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.svm import SVC
    from sklearn.neighbors import KNeighborsClassifier

    # convert balanced boolean to scikit learn method
    if weights is True:
        weights = 'balanced'
    else: weights = None

    # optional packages that add additional classifiers here
    if estimator == 'EarthClassifier' or estimator == 'EarthRegressor':
        try:
            from sklearn.pipeline import Pipeline
            from pyearth import Earth

            earth_classifier = Pipeline([('Earth',
                                          Earth(max_degree=p['max_degree'])),
                                         ('Logistic', LogisticRegression(n_jobs=n_jobs))])

            classifiers = {'EarthClassifier': earth_classifier,
                           'EarthRegressor': Earth(max_degree=p['max_degree'])}
        except:
            gscript.fatal('Py-earth package not installed')

    elif estimator == 'XGBClassifier' or estimator == 'XGBRegressor':
        try:
            from xgboost import XGBClassifier, XGBRegressor

            if p['max_depth'] is None:
                p['max_depth'] = int(3)

            classifiers = {
                'XGBClassifier':
                    XGBClassifier(learning_rate=p['learning_rate'],
                                  n_estimators=p['n_estimators'],
                                  max_depth=p['max_depth'],
                                  subsample=p['subsample'],
                                  nthread=n_jobs),
                'XGBRegressor':
                    XGBRegressor(learning_rate=p['learning_rate'],
                                 n_estimators=p['n_estimators'],
                                 max_depth=p['max_depth'],
                                 subsample=p['subsample'],
                                 nthread=n_jobs)}
        except:
            gscript.fatal('XGBoost package not installed')
    else:
        # core sklearn classifiers go here
        classifiers = {
            'SVC': SVC(C=p['C'],
                       class_weight=weights,
                       probability=True,
                       random_state=random_state),
            'LogisticRegression':
                LogisticRegression(C=p['C'],
                                   class_weight=weights,
                                   random_state=random_state,
                                   n_jobs=n_jobs,
                                   fit_intercept=True),
            'DecisionTreeClassifier':
                DecisionTreeClassifier(max_depth=p['max_depth'],
                                       max_features=p['max_features'],
                                       min_samples_split=p['min_samples_split'],
                                       min_samples_leaf=p['min_samples_leaf'],
                                       class_weight=weights,
                                       random_state=random_state),
            'DecisionTreeRegressor':
                DecisionTreeRegressor(max_features=p['max_features'],
                                      min_samples_split=p['min_samples_split'],
                                      min_samples_leaf=p['min_samples_leaf'],
                                      random_state=random_state),
            'RandomForestClassifier':
                RandomForestClassifier(n_estimators=p['n_estimators'],
                                       max_features=p['max_features'],
                                       min_samples_split=p['min_samples_split'],
                                       min_samples_leaf=p['min_samples_leaf'],
                                       class_weight=weights,
                                       random_state=random_state,
                                       n_jobs=n_jobs,
                                       oob_score=False),
            'RandomForestRegressor':
                RandomForestRegressor(n_estimators=p['n_estimators'],
                                      max_features=p['max_features'],
                                      min_samples_split=p['min_samples_split'],
                                      min_samples_leaf=p['min_samples_leaf'],
                                      random_state=random_state,
                                      n_jobs=n_jobs,
                                      oob_score=False),
            'ExtraTreesClassifier':
                ExtraTreesClassifier(n_estimators=p['n_estimators'],
                                     max_features=p['max_features'],
                                     min_samples_split=p['min_samples_split'],
                                     min_samples_leaf=p['min_samples_leaf'],
                                     class_weight=weights,
                                     random_state=random_state,
                                     n_jobs=n_jobs,
                                     oob_score=False),
            'ExtraTreesRegressor':
                ExtraTreesRegressor(n_estimators=p['n_estimators'],
                                    max_features=p['max_features'],
                                    min_samples_split=p['min_samples_split'],
                                    min_samples_leaf=p['min_samples_leaf'],
                                    random_state=random_state,
                                    n_jobs=n_jobs,
                                    oob_score=False),
            'GradientBoostingClassifier':
                GradientBoostingClassifier(learning_rate=p['learning_rate'],
                                           n_estimators=p['n_estimators'],
                                           max_depth=p['max_depth'],
                                           min_samples_split=p['min_samples_split'],
                                           min_samples_leaf=p['min_samples_leaf'],
                                           subsample=p['subsample'],
                                           max_features=p['max_features'],
                                           random_state=random_state),
            'GradientBoostingRegressor':
                GradientBoostingRegressor(learning_rate=p['learning_rate'],
                                          n_estimators=p['n_estimators'],
                                          max_depth=p['max_depth'],
                                          min_samples_split=p['min_samples_split'],
                                          min_samples_leaf=p['min_samples_leaf'],
                                          subsample=p['subsample'],
                                          max_features=p['max_features'],
                                          random_state=random_state),
            'GaussianNB': GaussianNB(),
            'LinearDiscriminantAnalysis': LinearDiscriminantAnalysis(),
            'QuadraticDiscriminantAnalysis': QuadraticDiscriminantAnalysis(),
            'KNeighborsClassifier': KNeighborsClassifier(n_neighbors=p['n_neighbors'],
                                                         weights=p['weights'],
                                                         n_jobs=n_jobs)
        }

    # define classifier
    clf = classifiers[estimator]

    # classification or regression
    if estimator == 'LogisticRegression' \
        or estimator == 'DecisionTreeClassifier' \
        or estimator == 'RandomForestClassifier' \
        or estimator == 'ExtraTreesClassifier' \
        or estimator == 'GradientBoostingClassifier' \
        or estimator == 'GaussianNB' \
        or estimator == 'LinearDiscriminantAnalysis' \
        or estimator == 'QuadraticDiscriminantAnalysis' \
        or estimator == 'EarthClassifier' \
        or estimator == 'XGBClassifier' \
        or estimator == 'SVC' \
        or estimator == 'KNeighborsClassifier':
        mode = 'classification'
    else:
        mode = 'regression'

    return (clf, mode)


def save_training_data(X, y, groups, coords, file):
    """
    Saves any extracted training data to a csv file

    Args
    ----
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels
    coords: Numpy array containing xy coordinates of samples
    file: Path to a csv file to save data to
    """

    # if there are no group labels, create a nan filled array
    if groups is None:
        groups = np.empty((y.shape[0]))
        groups[:] = np.nan

    training_data = np.column_stack([coords, X, y, groups])
    np.savetxt(file, training_data, delimiter=',')


def load_training_data(file):
    """
    Loads training data and labels from a csv file

    Args
    ----
    file: Path to a csv file to save data to

    Returns
    -------
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels, or None
    coords: Numpy array containing x,y coordinates of samples
    """

    training_data = np.loadtxt(file, delimiter=',')
    n_cols = training_data.shape[1]
    last_Xcol = n_cols-2

    # check to see if last column contains group labels or nans
    groups = training_data[:, -1]

    # if all nans then set groups to None
    if bool(np.isnan(groups).all()) is True:
        groups = None

    # fetch X and y
    coords = training_data[:, 0:2]
    X = training_data[:, 2:last_Xcol]
    y = training_data[:, -2]

    return(X, y, groups, coords)


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


def maps_from_group(group):
    """
    Parse individual rasters into a list from an imagery group

    Args
    ----
    group: String; GRASS imagery group

    Returns
    -------
    maplist: List containing individual GRASS raster maps
    map_names: List with print friendly map names
    """
    groupmaps = im.group(group=group, flags="g",
                         quiet=True, stdout_=PIPE).outputs.stdout

    maplist = groupmaps.split(os.linesep)
    maplist = maplist[0:len(maplist)-1]
    map_names = []

    for rastername in maplist:
        map_names.append(rastername.split('@')[0])

    return(maplist, map_names)


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
