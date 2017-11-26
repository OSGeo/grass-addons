#!/usr/bin/env python
# -- coding: utf-8 --

"""
The module rlearn_utils contains functinons to assist
with passing pre-defined scikit learn classifiers
and other utilities for loading/saving training data.
"""

from __future__ import absolute_import
from subprocess import PIPE
import numpy as np
import os
import grass.script as gs
from grass.pygrass.modules.shortcuts import imagery as im


def model_classifiers(estimator, random_state, n_jobs, p, weights=None):
    """

    Provides the classifiers and parameters using by the module

    Args
    ----
    estimator (string): Name of scikit learn estimator
    random_state (float): Seed to use in randomized components
    n_jobs (integer): Number of processing cores to use;
        -1 for all cores; -2 for all cores-1
    p (dict): Classifier setttings (keys) and values
    weights (string): None, or 'balanced' to add class_weights

    Returns
    -------
    clf (object): Scikit-learn classifier object
    mode (string): Flag to indicate whether classifier performs classification
        or regression

    """

    from sklearn.linear_model import LogisticRegression
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
    from sklearn.naive_bayes import GaussianNB
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    from sklearn.ensemble import (
        RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier,
        ExtraTreesRegressor)
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
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

            earth_classifier = Pipeline(
                [('classifier', Earth(max_degree=p['max_degree'])),
                 ('Logistic', LogisticRegression(n_jobs=n_jobs))])

            classifiers = {
                'EarthClassifier': earth_classifier,
                'EarthRegressor': Earth(max_degree=p['max_degree'])
                }
        except:
            gs.fatal('Py-earth package not installed')
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
                                   solver='liblinear',
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
    X (2d numpy array): Numpy array containing predictor values
    y (1d numpy array): Numpy array containing labels
    groups (1d numpy array): Numpy array of group labels
    coords (2d numpy array): Numpy array containing xy coordinates of samples
    file (string): Path to a csv file to save data to

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
    file (string): Path to a csv file to save data to

    Returns
    -------
    X (2d numpy array): Numpy array containing predictor values
    y (1d numpy array): Numpy array containing labels
    groups (1d numpy array): Numpy array of group labels, or None
    coords (2d numpy array): Numpy array containing x,y coordinates of samples

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


def maps_from_group(group):
    """

    Parse individual rasters into a list from an imagery group

    Args
    ----
    group (string): Name of GRASS imagery group

    Returns
    -------
    maplist (list): List containing individual GRASS raster maps
    map_names (list): List with print friendly map names

    """
    groupmaps = im.group(group=group, flags="g",
                         quiet=True, stdout_=PIPE).outputs.stdout

    maplist = groupmaps.split(os.linesep)
    maplist = maplist[0:len(maplist)-1]
    map_names = []

    for rastername in maplist:
        map_names.append(rastername.split('@')[0])

    return(maplist, map_names)


def save_model(estimator, X, y, sample_coords, groups, filename):
    from sklearn.externals import joblib

    joblib.dump((estimator, X, y, sample_coords, group_id), filename)


def load_model(filename):
    from sklearn.externals import joblib
    
    estimator, X, y, sample_coords, groups = joblib.load(filename)

    return (estimator, X, y, sample_coords, groups)