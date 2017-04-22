#!/usr/bin/env python
# -- coding: utf-8 --

############################################################################
# MODULE:        r.learn.ml
# AUTHOR:        Steven Pawley
# PURPOSE:       Supervised classification and regression of GRASS rasters
#                using the python scikit-learn package
#
# COPYRIGHT: (c) 2017 Steven Pawley, and the GRASS Development Team
#                This program is free software under the GNU General Public
#                for details.
#
#############################################################################

#%module
#% description: Supervised classification and regression of GRASS rasters using the python scikit-learn package
#% keyword: classification
#% keyword: regression
#% keyword: machine learning
#% keyword: scikit-learn
#%end

#%option G_OPT_I_GROUP
#% key: group
#% label: Imagery group to be classified
#% description: GRASS imagery group of raster maps to be used in the machine learning model
#% required: yes
#% multiple: no
#%end

#%option G_OPT_R_INPUT
#% key: trainingmap
#% label: Labelled pixels
#% description: Raster map with labelled pixels for training
#% required: no
#% guisection: Required
#%end

#%option G_OPT_V_INPUT
#% key: trainingpoints
#% label: Training point vector
#% description: Vector points map for training
#% required: no
#% guisection: Required
#%end

#%option G_OPT_DB_COLUMN
#% key: field
#% label: Response attribute column
#% description: Name of attribute column in trainingpoints containing response value
#% required: no
#% guisection: Required
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% label: Output Map
#% description: Prediction surface result from classification or regression model
#% guisection: Required
#% required: no
#%end

#%option string
#% key: classifier
#% label: Classifier
#% description: Supervised learning model to use
#% answer: RandomForestClassifier
#% options: LogisticRegression,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,GaussianNB,DecisionTreeClassifier,DecisionTreeRegressor,RandomForestClassifier,RandomForestRegressor,ExtraTreesClassifier,ExtraTreesRegressor,GradientBoostingClassifier,GradientBoostingRegressor,SVC,EarthClassifier,EarthRegressor,XGBClassifier,XGBRegressor
#% guisection: Classifier settings
#% required: no
#%end

#%option
#% key: c
#% type: double
#% label: Inverse of regularization strength
#% description: Inverse of regularization strength (LogisticRegression and SVC)
#% answer: 1.0
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: max_features
#% type: integer
#% label: Number of features avaiable during node splitting
#% description: Number of features avaiable during node splitting (tree-based classifiers and regressors)
#% answer:0
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: max_depth
#% type: integer
#% label: Maximum tree depth; zero uses classifier defaults
#% description: Maximum tree depth for tree-based method; zero uses classifier defaults (full-growing for Decision trees and Randomforest, 3 for GBM and XGB)
#% answer:0
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: min_samples_split
#% type: integer
#% label: The minimum number of samples required for node splitting
#% description: The minimum number of samples required for node splitting in tree-based classifiers
#% answer: 2
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: min_samples_leaf
#% type: integer
#% label: The minimum number of samples required to form a leaf node
#% description: The minimum number of samples required to form a leaf node in tree-based classifiers
#% answer: 1
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: n_estimators
#% type: integer
#% label: Number of estimators
#% description: Number of estimators (trees) in ensemble tree-based classifiers
#% answer: 100
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: learning_rate
#% type: double
#% label: learning rate
#% description: learning rate (also known as shrinkage) for gradient boosting methods
#% answer: 0.1
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: subsample
#% type: double
#% label: The fraction of samples to be used for fitting
#% description: The fraction of samples to be used for fitting, controls stochastic behaviour of gradient boosting methods
#% answer: 1.0
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option integer
#% key: max_degree
#% label: The maximum degree of terms in forward pass
#% description: The maximum degree of terms in forward pass for Py-earth
#% answer: 1
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option integer
#% key: categorymaps
#% multiple: yes
#% label: Indices of categorical rasters within the imagery group (0..n)
#% description: Indices of categorical rasters within the imagery group (0..n) that will be one-hot encoded
#% guisection: Optional
#%end

#%option string
#% key: cvtype
#% label: Non-spatial or spatial cross-validation
#% description: Perform non-spatial, clumped or clustered k-fold cross-validation
#% answer: Non-spatial
#% options: non-spatial,clumped,kmeans
#% guisection: Cross validation
#%end

#%option
#% key: n_partitions
#% type: integer
#% label: Number of kmeans spatial partitions
#% description: Number of kmeans spatial partitions for kmeans clustered cross-validation
#% answer: 10
#% guisection: Cross validation
#%end

#%option G_OPT_R_INPUT
#% key: group_raster
#% label: Custom group ids for training samples from GRASS raster
#% description: GRASS raster containing group ids for training samples. Samples with the same group id will not be split between training and test cross-validation folds
#% required: no
#% guisection: Cross validation
#%end

#%option
#% key: cv
#% type: integer
#% description: Number of cross-validation folds
#% answer: 1
#% guisection: Cross validation
#%end

#%option
#% key: n_permutations
#% type: integer
#% description: Number of permutations to perform for feature importances
#% answer: 50
#% guisection: Cross validation
#%end

#%flag
#% key: t
#% description: Perform hyperparameter tuning only
#% guisection: Cross validation
#%end

#%flag
#% key: f
#% description: Calculate permutation importances during cross validation
#% guisection: Cross validation
#%end

#%option G_OPT_F_OUTPUT
#% key: errors_file
#% label: Save cross-validation global accuracy results to csv
#% required: no
#% guisection: Cross validation
#%end

#%option G_OPT_F_OUTPUT
#% key: fimp_file
#% label: Save feature importances to csv
#% required: no
#% guisection: Cross validation
#%end

#%option G_OPT_F_OUTPUT
#% key: param_file
#% label: Save hyperparameter search scores to csv
#% required: no
#% guisection: Cross validation
#%end

#%option
#% key: random_state
#% type: integer
#% description: Seed to use for random state
#% answer: 1
#% guisection: Optional
#%end

#%option
#% key: lines
#% type: integer
#% description: Processing block size in terms of number of rows
#% answer: 25
#% guisection: Optional
#%end

#%option
#% key: indexes
#% type: integer
#% description: Indexes of class probabilities to predict. Default -1 predicts all classes
#% answer: -1
#% guisection: Optional
#% multiple: yes
#%end

#%option
#% key: n_jobs
#% type: integer
#% description: Number of cores for multiprocessing, -2 is n_cores-1
#% answer: -2
#% guisection: Optional
#%end

#%flag
#% key: s
#% label: Standardization preprocessing
#% guisection: Optional
#%end

#%flag
#% key: i
#% label: Impute training data preprocessing
#% guisection: Optional
#%end

#%flag
#% key: p
#% label: Output class membership probabilities
#% guisection: Optional
#%end

#%flag
#% key: z
#% label: Only predict class probabilities
#% guisection: Optional
#%end

#%flag
#% key: m
#% description: Build model only - do not perform prediction
#% guisection: Optional
#%end

#%flag
#% key: b
#% description: Balance training data using class weights
#% guisection: Optional
#%end

#%flag
#% key: l
#% label: Use memory swap
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: save_training
#% label: Save training data to csv
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_INPUT
#% key: load_training
#% label: Load training data from csv
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: save_model
#% label: Save model from file
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_INPUT
#% key: load_model
#% label: Load model from file
#% required: no
#% guisection: Optional
#%end

#%rules
#% exclusive: trainingmap,load_model
#% exclusive: load_training,save_training
#% exclusive: trainingmap,load_training
#% exclusive: trainingpoints,trainingmap
#% exclusive: trainingpoints,load_training
#%end

import atexit
import os
import tempfile
import itertools
from copy import deepcopy
import numpy as np
from numpy.random import RandomState

import grass.script as grass
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.modules.shortcuts import imagery as im
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.table import Link
from grass.pygrass.utils import get_raster_for_points
from subprocess import PIPE

tmp_rast = []

def cleanup():
    for rast in tmp_rast:
        grass.run_command("g.remove", name=rast, type='raster', flags='f', quiet=True)

def specificity_score(y_true, y_pred):
    """
    Function to calculate specificity score

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

    return (tn/(tn+fp))


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

    return(scores)


def cross_val_scores(estimator, X, y, groups=None, sample_weight=None, cv=3,
                     scoring=['accuracy'], feature_importances=False,
                     n_permutations=25, random_state=None):

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
    random_state: Seed to pass to the random number generator
    """

    from sklearn import metrics
    from sklearn.model_selection import (
        RandomizedSearchCV, GridSearchCV, StratifiedKFold)

    estimator = deepcopy(estimator)

    # create model_selection method
    if isinstance(cv, int):
        cv = StratifiedKFold(n_splits=cv)

    # fit the model on the training data and predict the test data
    # need the groups parameter because the estimator can be a
    # RandomizedSearchCV or GridSearchCV estimator where cv=GroupKFold
    if isinstance(estimator, RandomizedSearchCV) is True \
            or isinstance(estimator, GridSearchCV):
        param_search = True
    else:
        param_search = False

    # create dictionary of lists to store metrics
    scores = dict.fromkeys(scoring)
    scores = { key: [] for key, value in scores.iteritems()}
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
    byclass_scores = { key: np.zeros((0, n_classes)) for key, value in byclass_scores.iteritems()}

    # remove any byclass_scorers that are not in the scoring list
    byclass_scores = {key: value for key, value in byclass_scores.iteritems() if key in scores}

    # set averaging type for global binary or multiclass scores
    if len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
        average='binary'
    else:
        average='macro'

    # check to see if scoring is a valid sklearn metric
    for i in scores.keys():
        try:
            list(scoring_methods.keys()).index(i)
        except:
            print('Scoring ' + i + ' is not a valid scoring method')
            print('Valid methods are:')
            print(scoring_methods.keys())

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

    # train on k-1 folds and test of k folds
    for train_indices, test_indices in k_fold:

        # subset training and test fold data
        X_train, X_test = X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]

        # subset training and test fold group ids
        if groups is not None: groups_train = groups[train_indices]
        else: groups_train = None

        # subset training and test fold sample_weight
        if sample_weight is not None: weights = sample_weight[train_indices]

        # train estimator on training fold
        if groups is not None and param_search is True:
            if sample_weight is None: estimator.fit(X_train, y_train, groups=groups_train)
            else: estimator.fit(X_train, y_train, groups=groups_train, sample_weight=weights)
        else:
            if sample_weight is None: estimator.fit(X_train, y_train)
            else: estimator.fit(X_train, y_train, sample_weight=weights)

        # prediction of test fold
        y_pred = estimator.predict(X_test)

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

    return(scores, byclass_scores, fimp)


def predict(estimator, predictors, output, predict_type='raw', labels=None,
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

    # current region
    current = Region()

    # determine output data type and nodata
    if labels is not None:
        ftype = 'CELL'
        nodata = -2147483648
    else:
        ftype = 'FCELL'
        nodata = np.nan

    # open predictors as list of rasterrow objects
    n_features = len(predictors)
    rasstack = [0] * n_features

    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() is True:
            rasstack[i].open('r')
        else:
            grass.fatal("GRASS raster " + predictors[i] +
                        " does not exist.... exiting")

    # create and open RasterRow object for writing of classification result
    if predict_type == 'raw':
        classification = RasterRow(output)
        classification.open('w', ftype, overwrite=True)

    # Prediction using row blocks
    for rowblock in range(0, current.rows, rowincr):
        grass.percent(rowblock, current.rows, rowincr)

        # check that the row increment does not exceed the number of rows
        if rowblock+rowincr > current.rows:
            rowincr = current.rows - rowblock
        img_np_row = np.zeros((rowincr, current.cols, n_features))

        # loop through each row, and each band
        # and add these values to the 2D array img_np_row
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

            # replace NaN values so that the prediction does not have a border
            result[np.nonzero(np.isnan(mask))] = nodata

            # for each row we can perform computation, and write the result
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

                # replace NaN values so that the prediction does not have a border
                result_proba_class[np.nonzero(np.isnan(mask))] = np.nan

                for row in range(rowincr):
                    newrow = Buffer((result_proba_class.shape[1],), mtype='FCELL')
                    newrow[:] = result_proba_class[row, :]
                    prob[iclass].put_row(newrow)

    # close all maps
    for i in range(n_features): rasstack[i].close()

    # close all class probability maps
    if predict_type == 'raw':
        classification.close()
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
            grass.fatal('Py-earth package not installed')

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
            grass.fatal('XGBoost package not installed')
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
        or estimator == 'SVC':
        mode = 'classification'
    else:
        mode = 'regression'

    return (clf, mode)


def save_training_data(X, y, groups, file):

    """
    Saves any extracted training data to a csv file

    Args
    ----
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels
    file: Path to a csv file to save data to
    """

    # if there are no group labels, create a nan filled array
    if groups is None:
        groups = np.empty((y.shape[0]))
        groups[:] = np.nan

    training_data = np.column_stack([X, y, groups])
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
    X = training_data[:, 0:last_Xcol]
    y = training_data[:, -2]

    return(X, y, groups)


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
            response_np = np.memmap(tempfile.NamedTemporaryFile(),
                                    dtype='float32', mode='w+',
                                    shape=(current.rows, current.cols))
            response_np[:] = np.array(roi_gr)[:]
    else:
        grass.fatal("GRASS response raster does not exist.... exiting")

    # determine number of predictor rasters
    n_features = len(predictors)

    # check to see if all predictors exist
    for i in range(n_features):
        if RasterRow(predictors[i]).exist() is not True:
            grass.fatal("GRASS raster " + predictors[i] +
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
    maplist: Python list containing individual GRASS raster maps
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

    import pandas as pd

    # open grass vector
    points = VectorTopo(gvector.split('@')[0])
    points.open('r')

    # create link to attribute table
    points.dblinks.by_name(name=gvector)
    link = points.dblinks[0]

    # convert to pandas array
    gvector_df = pd.DataFrame(points.table_to_dict()).T
    gvector_df.columns = points.table.columns
    y = gvector_df.loc[:, field].as_matrix()
    y = y.astype(float)

    # extract training data
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

def main():
    try:
        from sklearn.externals import joblib
        from sklearn.cluster import KMeans
        from sklearn.model_selection import StratifiedKFold, GroupKFold
        from sklearn.preprocessing import StandardScaler, Imputer
        from sklearn.model_selection import GridSearchCV
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.pipeline import Pipeline
        from sklearn.utils import shuffle
        from sklearn import metrics
        from sklearn.metrics import make_scorer
        import warnings
        warnings.filterwarnings('ignore')  # turn off UndefinedMetricWarning
    except:
        grass.fatal("Scikit learn 0.18 or newer is not installed")

    try:
        import pandas as pd
    except:
        grass.fatal("Pandas is not installed")

    group = options['group']
    trainingmap = options['trainingmap']
    trainingpoints = options['trainingpoints']
    field = options['field']
    output = options['output']
    if '@' in output:
        output = output.split('@')[0]
    classifier = options['classifier']
    norm_data = flags['s']
    cv = int(options['cv'])
    cvtype = options['cvtype']
    group_raster = options['group_raster']
    categorymaps = options['categorymaps']
    n_partitions = int(options['n_partitions'])
    modelonly = flags['m']
    probability = flags['p']
    prob_only = flags['z']
    tuneonly = flags['t']
    rowincr = int(options['lines'])
    random_state = int(options['random_state'])
    model_save = options['save_model']
    model_load = options['load_model']
    load_training = options['load_training']
    save_training = options['save_training']
    importances = flags['f']
    indexes = options['indexes']
    if ',' in indexes:
        indexes = [int(i) for i in indexes.split(',')]
    else:
        indexes = [int(indexes)] # predict expects list
    if indexes == [-1]:
        indexes = None
    n_permutations = int(options['n_permutations'])
    n_jobs = int(options['n_jobs'])
    lowmem = flags['l']
    impute = flags['i']
    errors_file = options['errors_file']
    fimp_file = options['fimp_file']
    param_file = options['param_file']
    balance = flags['b']
    if balance is True:
        balance = 'balanced'
    else: balance = None
    if ',' in categorymaps:
        categorymaps = [int(i) for i in categorymaps.split(',')]
    else: categorymaps = None
    
    # error checking
    # feature importances selected by no cross-validation scheme used
    if importances is True and cv == 1:
        grass.fatal('Feature importances require cross-validation cv > 1')
    
    # output map has not been entered and modelonly is not set to True
    if output == '' and modelonly is True:
        grass.fatal('No output map specified')
    
    # perform prediction only for class probabilities but probability flag is not set to True
    if prob_only is True:
        probability = True

    # make dicts for hyperparameters, datatypes and parameters for tuning
    hyperparams = {'C': options['c'],
                   'min_samples_split': options['min_samples_split'],
                   'min_samples_leaf': options['min_samples_leaf'],
                   'n_estimators': options['n_estimators'],
                   'learning_rate': options['learning_rate'],
                   'subsample': options['subsample'],
                   'max_depth': options['max_depth'],
                   'max_features': options['max_features'],
                   'max_degree': options['max_degree']}
    hyperparams_type = dict.fromkeys(hyperparams, int)
    hyperparams_type['C'] = float
    hyperparams_type['learning_rate'] = float
    hyperparams_type['subsample'] = float
    param_grid = deepcopy(hyperparams_type)
    param_grid = dict.fromkeys(param_grid, None)

    for key, val in hyperparams.iteritems():
        # split any comma separated strings and add them to the param_grid
        if ',' in val: param_grid[key] = [hyperparams_type[key](i) for i in val.split(',')]
        # else convert the single strings to int or float
        else: hyperparams[key] = hyperparams_type[key](val)

    if hyperparams['max_depth'] == 0: hyperparams['max_depth'] = None
    if hyperparams['max_features'] == 0: hyperparams['max_features'] = 'auto'
    param_grid = {k: v for k, v in param_grid.iteritems() if v is not None}

    # retrieve sklearn classifier object and parameters
    clf, mode = model_classifiers(
        classifier, random_state, n_jobs, hyperparams, balance)

    # remove dict keys that are incompatible for the selected classifier
    clf_params = clf.get_params()
    param_grid = {
        key: value for key, value in param_grid.iteritems()
        if key in clf_params}

    # scoring metrics
    if mode == 'classification':
        scoring = ['matthews_corrcoef', 'accuracy', 'precision', 'recall', 'f1', 'kappa', 'balanced_accuracy']
        search_scorer = make_scorer(metrics.cohen_kappa_score)
    else:
        scoring = ['r2', 'neg_mean_squared_error']
        search_scorer = 'r2'

    # Sample training data and group ids
    # ----------------------------------

    # fetch individual raster names from group
    maplist, map_names = maps_from_group(group)

    if model_load == '':

        # Sample training data and group id
        if load_training != '':
            X, y, group_id = load_training_data(load_training)
        else:
            grass.message('Extracting training data')

            # clump the labelled pixel raster if labels represent polygons
            # then set the group_raster to the clumped raster to extract the
            # group_ids used in the GroupKFold cross-validation
            if trainingmap != '' and cvtype == 'clumped' and group_raster == '':
                clumped_trainingmap = 'tmp_clumped_trainingmap'
                tmp_rast.append(clumped_trainingmap)
                r.clump(input=trainingmap, output=clumped_trainingmap,
                        overwrite=True, quiet=True)
                group_raster = clumped_trainingmap
            elif trainingmap == '' and cvtype == 'clumped':
                grass.fatal('Cross-validation using clumped training areas ',
                            'requires raster-based training areas')

            # extract training data from maplist and take group ids from
            # group_raster. Shuffle=False so that group ids and labels align
            # because cross-validation will be performed spatially
            if group_raster != '':
                maplist2 = deepcopy(maplist)
                maplist2.append(group_raster)
                if trainingmap != '':
                    X, y, sample_coords = extract(
                        response=trainingmap, predictors=maplist2, lowmem=lowmem)
                elif trainingpoints != '':
                    X, y, sample_coords = extract_points(
                        trainingpoints, maplist2, field)

                # take group id from last column and remove from predictors
                group_id = X[:, -1]
                X = np.delete(X, -1, axis=1)
            else:
                # extract training data from maplist without group Ids
                # shuffle this data by default
                if trainingmap != '':
                    X, y, sample_coords = extract(
                        response=trainingmap, predictors=maplist, lowmem=lowmem)
                elif trainingpoints != '':
                    X, y, sample_coords = extract_points(
                        trainingpoints, maplist, field)
                group_id = None

                if cvtype == 'kmeans':
                    clusters = KMeans(
                        n_clusters=n_partitions,
                        random_state=random_state, n_jobs=n_jobs)

                    clusters.fit(sample_coords)
                    group_id = clusters.labels_
            # check for labelled pixels and training data
            if y.shape[0] == 0 or X.shape[0] == 0:
                grass.fatal('No training pixels or pixels in imagery group '
                            '...check computational region')

            # impute or remove NaNs
            if impute is False:
                y = y[~np.isnan(X).any(axis=1)]
                sample_coords = sample_coords[~np.isnan(X).any(axis=1)]
                if group_id is not None:
                    group_id = group_id[~np.isnan(X).any(axis=1)]
                X = X[~np.isnan(X).any(axis=1)]
            else:
                missing = Imputer(strategy='median')
                X = missing.fit_transform(X)

            # shuffle data
            if group_id is None:
                X, y, sample_coords = shuffle(X, y, sample_coords, random_state=random_state)
            if group_id is not None:
                X, y, sample_coords, group_id = shuffle(
                    X, y, sample_coords, group_id, random_state=random_state)

        # option to save extracted data to .csv file
        if save_training != '':
            save_training_data(X, y, group_id, save_training)

        # define model selection cross-validation method
        if any(param_grid) is True and cv == 1:
            grass.fatal('Hyperparameter search requires cv > 1')
        if any(param_grid) is True or cv > 1:
            if group_id is None:
                resampling = StratifiedKFold(
                    n_splits=cv, random_state=random_state)
            else:
                resampling = GroupKFold(n_splits=cv)
        else:
            resampling = None

        # define preprocessing pipeline
        # -----------------------------

        # sample weights for GradientBoosting or XGBClassifier
        if balance == 'balanced' and mode == 'classification' and classifier in (
                'GradientBoostingClassifier', 'XGBClassifier'):
            from sklearn.utils import compute_class_weight
            class_weights = compute_class_weight(
                class_weight='balanced', classes=(y), y=y)
        else:
            class_weights = None

        # scaling and onehot encoding
        if norm_data is True and categorymaps is None:
            clf = Pipeline([('scaling', StandardScaler()),
                            ('classifier', clf)])
        if categorymaps is not None and norm_data is False:
            enc = OneHotEncoder(categorical_features=categorymaps)
            enc.fit(X)
            clf = Pipeline([('onehot', OneHotEncoder(
                categorical_features=categorymaps,
                n_values=enc.n_values_, handle_unknown='ignore', # prevent failure due to new categorical vars
                sparse=False)),  # dense because not all clf can use sparse
                            ('classifier', clf)])
        if norm_data is True and categorymaps is not None:
            enc = OneHotEncoder(categorical_features=categorymaps)
            enc.fit(X)
            clf = Pipeline([('onehot', OneHotEncoder(
                categorical_features=categorymaps,
                n_values=enc.n_values_, handle_unknown='ignore',
                sparse=False)),
                            ('scaling', StandardScaler()),
                            ('classifier', clf)])

        # define hyperparameter grid search
        # ---------------------------------

        # check if dict contains and keys - perform GridSearchCV
        if any(param_grid) is True:

            # if Pipeline then change param_grid keys to named_step
            if isinstance(clf, Pipeline):
                for key in param_grid.keys():
                    newkey = 'classifier__' + key
                    param_grid[newkey] = param_grid.pop(key)

            # create grid search method
            clf = GridSearchCV(
                estimator=clf, param_grid=param_grid, scoring=search_scorer,
                n_jobs=n_jobs, cv=resampling)

        # classifier training
        # -------------------

        # fit and parameter search
        grass.message(os.linesep)
        grass.message(('Fitting model using ' + classifier))

        # use groups if GroupKFold and param_grid are present
        if isinstance(resampling, GroupKFold) and any(param_grid) is True:
            if balance == 'balanced' and classifier in (
                    'GradientBoostingClassifier', 'XGBClassifier'):
                clf.fit(X=X, y=y, groups=group_id, sample_weight=class_weights)
            else:
                clf.fit(X=X, y=y, groups=group_id)
        else:
            if balance == 'balanced' and classifier in (
                    'GradientBoostingClassifier', 'XGBClassifier'):
                clf.fit(X=X, y=y, sample_weight=class_weights)
            else:
                clf.fit(X, y)

        if any(param_grid) is True:
            grass.message(os.linesep)
            grass.message('Best parameters:')
            grass.message(str(clf.best_params_))
            if param_file != '':
                param_df = pd.DataFrame(clf.cv_results_)
                param_df.to_csv(param_file)

        # cross-validation
        # -----------------

        # If cv > 1 then use cross-validation to generate performance measures
        if cv > 1 and tuneonly is not True :
            if mode == 'classification' and cv > np.histogram(
                    y, bins=len(np.unique(y)))[0].min():
                grass.message(os.linesep)
                grass.message('Number of cv folds is greater than number of '
                              'samples in some classes. Cross-validation is being'
                              ' skipped')
            else:
                grass.message(os.linesep)
                grass.message(
                    "Cross validation global performance measures......:")

                # cross-validate the training object
                if mode == 'classification' and \
                    len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
                    scoring.append('roc_auc')
                scores, cscores, fimp = cross_val_scores(
                    clf, X, y, group_id, class_weights, resampling, scoring,
                    importances, n_permutations, random_state)

                # global scores
                for method, val in scores.iteritems():
                    grass.message(
                        method+":\t%0.3f\t+/-SD\t%0.3f" %
                        (val.mean(), val.std()))

                # individual class scores
                if mode == 'classification' and len(np.unique(y)) != 2:
                    grass.message(os.linesep)
                    grass.message('Cross validation class performance measures......:')
                    grass.message('Class \t' + '\t'.join(map(str, np.unique(y))))

                    for method, val in cscores.iteritems():
                        mat_cscores = np.matrix(val)
                        grass.message(
                            method+':\t' + '\t'.join(
                                map(str, np.round(mat_cscores.mean(axis=0), 2)[0])))
                        grass.message(
                            method+' std:\t' + '\t'.join(
                                map(str, np.round(mat_cscores.std(axis=0), 2)[0])))

                # write cross-validation results for csv file
                if errors_file != '':
                    errors = pd.DataFrame(scores)
                    errors.to_csv(errors_file, mode='w')

                # feature importances
                if importances is True:
                    grass.message(os.linesep)
                    grass.message("Feature importances")
                    grass.message("id" + "\t" + "Raster" + "\t" + "Importance")

                    # mean of cross-validation feature importances
                    for i in range(len(fimp.mean(axis=0))):
                        grass.message(
                            str(i) + "\t" + maplist[i] +
                            "\t" + str(round(fimp.mean(axis=0)[i], 4)))

                    if fimp_file != '':
                        np.savetxt(fname=fimp_file, X=fimp, delimiter=',',
                                   header=','.join(maplist), comments='')
    else:
        # load a previously fitted train object
        if model_load != '':
            # load a previously fitted model
            clf = joblib.load(model_load)

    # Optionally save the fitted model
    if model_save != '':
        joblib.dump(clf, model_save)

    # prediction on the rest of the GRASS rasters in the imagery group
    # ----------------------------------------------------------------

    if modelonly is not True:
        grass.message(os.linesep)
        if mode == 'classification':
            if prob_only is False:
                grass.message('Predicting classification raster...')
                predict(estimator=clf, predictors=maplist, output=output, predict_type='raw',
                        labels=np.unique(y), rowincr=rowincr)

            if probability is True:
                grass.message('Predicting class probabilities...')
                predict(estimator=clf, predictors=maplist, output=output, predict_type='prob',
                        labels=np.unique(y), index=indexes, rowincr=rowincr)

        elif mode == 'regression':
            grass.message('Predicting regression raster...')
            predict(estimator=clf, predictors=maplist, output=output, predict_type='raw',
                    labels=None, rowincr=rowincr)
    else:
        grass.message("Model built and now exiting")

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
