#!/usr/bin/env python
# -- coding: utf-8 --

"""
The module rlearn_crossval contains functions to perform
model validation and permutation feature importances.

"""

from __future__ import absolute_import
from copy import deepcopy

import numpy as np
import os
from numpy.random import RandomState

import grass.script as gscript

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


def varimp_permutation(estimator, X, y, n_permutations, scorer,
                       n_jobs, random_state):
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
    X, y: data and labels from a test partition
    n_permutations: number of random permutations to apply
    scorer: scikit-learn metric function to use
    n_jobs: integer, number of processing cores
    random_state: seed to pass to the numpy random.seed

    Returns
    -------
    scores: scores for each predictor following permutation
    """

    from sklearn.externals.joblib import Parallel, delayed

    # calculate score on original variables without permutation
    # determine best metric type for binary/multiclass/regression scenarios
    y_pred = estimator.predict(X)
    best_score = scorer(y, y_pred)

    # repeated permutations and return difference from best score per predictor
    scores = Parallel(n_jobs=n_jobs)(
        delayed(__permute)(
            estimator, X, y, best_score, scorer, random_state)
        for n in range(n_permutations))

    # average the repetitions
    scores = np.asarray(scores)
    scores = scores.mean(axis=0)

    return scores


def __permute(estimator, X, y, best_score, scorer, random_state):
    """
    Permute each predictor and measure difference from best score

    Args
    ----
    estimator: scikit learn estimator
    X, y: data and labels from a test partition
    best_score: best scorer obtained on unperturbed data
    scorer: scoring method to use to measure importances
    random_state: random seed

    Returns
    -------
    scores: 2D numpy array of scores for each predictor following permutation
    """

    rstate = RandomState(random_state)

    # permute each predictor variable and assess difference in score
    scores = np.zeros(X.shape[1])

    for i in range(X.shape[1]):
        Xscram = np.copy(X)
        Xscram[:, i] = rstate.choice(X[:, i], X.shape[0])

        # fit the model on the training data and predict the test data
        y_pred = estimator.predict(Xscram)
        scores[i] = best_score-scorer(y, y_pred)
        if scores[i] < 0:
            scores[i] = 0

    return scores


def __parallel_fit(estimator, X, y, groups, train_indices, test_indices, sample_weight):
    """
    Fit classifiers/regressors in parallel

    Args
    ----
    estimator: scikit learn estimator
    X, y: 2D and 1D numpy arrays of training data and labels
    groups: 1D numpy array of len(y) containing group labels
    train_indices, test_indices: 1D numpy arrays of indices to use for training/validation
    sample_weight: 1D numpy array of len(y) containing weights to use during fitting
                    applied only to XGBoost and Gradient Boosting classifiers
    """

    # create training and test folds
    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]
    if groups is not None: groups_train = groups[train_indices]
    else: groups_train = None

    # subset training and test fold sample_weight
    if sample_weight is not None: weights = sample_weight[train_indices]

    # train estimator
    if groups is not None and type(estimator).__name__ in ['RandomizedSearchCV', 'GridSearchCV']:
        if sample_weight is None: estimator.fit(X_train, y_train, groups=groups_train)
        else: estimator.fit(X_train, y_train, groups=groups_train, sample_weight=weights)
    else:
        if sample_weight is None: estimator.fit(X_train, y_train)
        else: estimator.fit(X_train, y_train, sample_weight=weights)

    return estimator


def cross_val_scores(estimator, X, y, groups=None, sample_weight=None, cv=3,
                     scoring='accuracy', feature_importances=False,
                     n_permutations=25, random_state=None, n_jobs=-1):
    """
    Stratified Kfold and GroupFold cross-validation using multiple
    scoring metrics and permutation feature importances

    Args
    ----
    estimator: Scikit learn estimator
    X, y: 2D and 1D numpy array of training data and labels
    groups: 1D numpy array containing group labels
    sample_weight: 1D numpy array[n_samples,] of sample weights
    cv: Integer of cross-validation folds or sklearn.model_selection object
    scoring: List of performance metrics to use
    feature_importances: Boolean to perform permutation-based importances
    n_permutations: Number of permutations during feature importance
    random_state: Seed to pass to the random number generator

    Returns
    -------
    scores: Dict, containing lists of scores per cross-validation fold
    byclass_scores: Dict, containing scores per class
    fimp: 2D numpy array of permutation feature importances per feature
    clf_resamples: List, fitted estimators
    predictions: 2D numpy array with y_true, y_pred, fold
    """

    from sklearn import metrics
    from sklearn.model_selection import StratifiedKFold
    from sklearn.externals.joblib import Parallel, delayed

    # -------------------------------------------------------------------------
    # create copies of estimator and create cross-validation iterator
    # -------------------------------------------------------------------------

    # deepcopy estimator
    clf = deepcopy(estimator)

    # create model_selection method
    if isinstance(cv, int):
        cv = StratifiedKFold(n_splits=cv)

    # -------------------------------------------------------------------------
    # create dictionary of lists to store metrics
    # -------------------------------------------------------------------------

    if isinstance(scoring, basestring):
        scoring = [scoring]
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

    # create dict to store byclass metrics results
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
            gscript.fatal(('Scoring ', i, ' is not a valid scoring method',
                            os.linesep(),
                            'Valid methods are: ', scoring_methods.keys()))

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

    # -------------------------------------------------------------------------
    # extract cross-validation indices
    # -------------------------------------------------------------------------

    if groups is None:
        k_fold = cv.split(X, y)
    else:
        k_fold = cv.split(X, y, groups=groups)

    trains, tests = [], []
    for train_indices, test_indices in k_fold:
        trains.append(train_indices)
        tests.append(test_indices)

    # -------------------------------------------------------------------------
    # Perform multiprocessing fitting of clf on each fold
    # -------------------------------------------------------------------------

    clf_resamples = Parallel(n_jobs=n_jobs)(
        delayed(__parallel_fit)(clf, X, y, groups, train_indices,
                              test_indices, sample_weight)
        for train_indices, test_indices in zip(trains, tests))

    # -------------------------------------------------------------------------
    # loop through each fold and calculate performance metrics
    # -------------------------------------------------------------------------

    # store predictions and indices
    predictions = np.zeros((len(y), 3)) # y_true, y_pred, fold

    fold = 0
    for train_indices, test_indices in zip(trains, tests):

        # create training and test folds
        X_train, X_test = X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]

        # prediction of test fold
        y_pred = clf_resamples[fold].predict(X_test)
        predictions[test_indices, 0] = y_test
        predictions[test_indices, 1] = y_pred
        predictions[test_indices, 2] = fold

        # calculate global performance metrics
        for m in scores.keys():
            # metrics that require probabilties
            if m == 'brier_loss' or m == 'roc_auc':
                y_prob = clf_resamples[fold].predict_proba(X_test)[:, 1]
                scores[m] = np.append(
                    scores[m], scoring_methods[m](y_test, y_prob))

            # metrics that have no averaging for multiclass
            elif m == 'kappa' or m == 'specificity' or m == 'accuracy' \
            or m == 'hamming_loss' or m == 'jaccard_similarity' \
            or m == 'log_loss' or m == 'zero_one_loss' \
            or m == 'matthews_corrcoef' or m == 'r2' \
            or m == 'neg_mean_squared_error':
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
            fimp[fold, :] = varimp_permutation(
                clf_resamples[fold], X_test, y_test, n_permutations,
                scoring_methods[scoring[0]], n_jobs, random_state)
        fold += 1

    return(scores, byclass_scores, fimp, clf_resamples, predictions)