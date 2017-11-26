#!/usr/bin/env python
# -- coding: utf-8 --
#
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
# July, 2017. Jaan Janno, Mait Lang. Bugfixes concerning crossvalidation failure
# when class numeric ID-s were not continous increasing +1 each.
# Bugfix for processing index list of nominal layers.

#%module
#% description: Supervised classification and regression of GRASS rasters using the python scikit-learn package
#% keyword: raster
#% keyword: classification
#% keyword: regression
#% keyword: machine learning
#% keyword: scikit-learn
#%end

#%option G_OPT_I_GROUP
#% key: group
#% label: Group of raster layers to be classified
#% description: GRASS imagery group of raster maps representing feature variables to be used in the machine learning model
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
#% label: Vectorfile with training samples
#% description: Vector points map where each point is used as training sample. Handling of missing values in training data can be choosen later.
#% required: no
#% guisection: Required
#%end

#%option G_OPT_DB_COLUMN
#% key: field
#% label: Response attribute column
#% description: Name of attribute column in trainingpoints table containing response values
#% required: no
#% guisection: Required
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% label: Output Map
#% description: Raster layer name to store result from classification or regression model. The name will also used as a perfix if class probabilities or intermediate of cross-validation results are ordered as maps.
#% guisection: Required
#% required: no
#%end

#%option string
#% key: classifier
#% label: Classifier
#% description: Supervised learning model to use
#% answer: RandomForestClassifier
#% options: LogisticRegression,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,KNeighborsClassifier,GaussianNB,DecisionTreeClassifier,DecisionTreeRegressor,RandomForestClassifier,RandomForestRegressor,ExtraTreesClassifier,ExtraTreesRegressor,GradientBoostingClassifier,GradientBoostingRegressor,SVC,EarthClassifier,EarthRegressor
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
#% label: Number of features available during node splitting; zero uses classifier defaults
#% description: Number of features available during node splitting (tree-based classifiers and regressors)
#% answer:0
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: max_depth
#% type: integer
#% label: Maximum tree depth; zero uses classifier defaults
#% description: Maximum tree depth for tree-based method; zero uses classifier defaults (full-growing for Decision trees and Randomforest, 3 for GBM)
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

#%option
#% key: max_degree
#% type: integer
#% label: The maximum degree of terms in forward pass
#% description: The maximum degree of terms in forward pass for Py-earth
#% answer: 1
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option
#% key: n_neighbors
#% type: integer
#% label: Number of neighbors to use
#% description: Number of neighbors to use
#% answer: 5
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option string
#% key: weights
#% label: weight function
#% description: Distance weight function for k-nearest neighbours model prediction
#% answer: uniform
#% options: uniform,distance
#% multiple: yes
#% guisection: Classifier settings
#%end

#%option string
#% key: grid_search
#% label: Resampling method to use for hyperparameter optimization
#% description: Resampling method to use for hyperparameter optimization
#% options: cross-validation,holdout
#% answer: cross-validation
#% multiple: no
#% guisection: Classifier settings
#%end

#%option G_OPT_R_INPUT
#% key: categorymaps
#% required: no
#% multiple: yes
#% label: Names of categorical rasters within the imagery group
#% description: Names of categorical rasters within the imagery group that will be one-hot encoded. Leave empty if none.
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
#% label: Number of k-means spatial partitions
#% description: Number of k-means spatial partitions for k-means clustered cross-validation
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
#% answer: 10
#% guisection: Cross validation
#%end

#%flag
#% key: t
#% description: Perform hyperparameter tuning only
#% guisection: Cross validation
#%end

#%flag
#% key: n
#% label: Use nested cross validation
#% description: Use nested cross validation as part of hyperparameter tuning
#% guisection: Cross validation
#%end

#%flag
#% key: f
#% label: Estimate permutation-based feature importances
#% description: Estimate feature importance using a permutation-based method
#% guisection: Cross validation
#%end

#%flag
#% key: r
#% label: Make predictions for cross validation resamples
#% description: Produce raster predictions for all cross validation resamples
#% guisection: Cross validation
#%end

#%option G_OPT_F_OUTPUT
#% key: errors_file
#% label: Save cross-validation global accuracy results to csv
#% required: no
#% guisection: Cross validation
#%end

#%option G_OPT_F_OUTPUT
#% key: preds_file
#% label: Save cross-validation predictions to csv
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
#% key: indexes
#% type: integer
#% description: Indexes of class probabilities to predict. Default -1 predicts all classes
#% answer: -1
#% guisection: Optional
#% multiple: yes
#%end

#%option
#% key: rowincr
#% type: integer
#% description: Maximum number of raster rows to read/write in single chunk whilst performing prediction
#% answer: 25
#% guisection: Optional
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
#% description: Standardize feature variables (convert values the get zero mean and unit variance).
#% guisection: Optional
#%end

#%flag
#% key: p
#% label: Output class membership probabilities
#% description: A raster layer is created for each class. It is recommended to give a list of particular classes in interest to avoid consumption of large amounts of disk space.
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
#% label: Save model to file
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

from __future__ import absolute_import
import atexit
import os
from copy import deepcopy
import numpy as np
from grass.pygrass.utils import set_path
import grass.script as gs
from grass.pygrass.modules.shortcuts import raster as r

set_path('r.learn.ml')
from rlearn_crossval import cross_val_scores
from rlearn_sampling import extract_pixels, extract_points
from rlearn_prediction import predict
from rlearn_utils import (
    model_classifiers, save_training_data, load_training_data, maps_from_group)

tmp_rast = []

def cleanup():
    for rast in tmp_rast:
        gs.run_command(
            "g.remove", name=rast, type='raster', flags='f', quiet=True)

def warn(*args, **kwargs):
    pass

import warnings
warnings.warn = warn

def main():
    try:
        from sklearn.externals import joblib
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import (
            GridSearchCV, GroupShuffleSplit, ShuffleSplit,
            StratifiedKFold, GroupKFold)
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.pipeline import Pipeline
        from sklearn.utils import shuffle
        from sklearn import metrics
        from sklearn.metrics import make_scorer
    except:
        gs.fatal("Scikit learn 0.18 or newer is not installed")

    try:
        import pandas as pd
    except:
        gs.fatal("Pandas is not installed ")

    # required gui section
    group = options['group']
    trainingmap = options['trainingmap']
    trainingpoints = options['trainingpoints']
    field = options['field']
    output = options['output']

    # classifier gui section
    classifier = options['classifier']
    grid_search = options['grid_search']
    hyperparams = {
        'C': options['c'],
        'min_samples_split': options['min_samples_split'],
        'min_samples_leaf': options['min_samples_leaf'],
        'n_estimators': options['n_estimators'],
        'learning_rate': options['learning_rate'],
        'subsample': options['subsample'],
        'max_depth': options['max_depth'],
        'max_features': options['max_features'],
        'max_degree': options['max_degree'],
        'n_neighbors': options['n_neighbors'],
        'weights': options['weights']
        }

    # cross validation
    cv = int(options['cv'])
    cvtype = options['cvtype']
    group_raster = options['group_raster']
    n_partitions = int(options['n_partitions'])
    tune_only = flags['t']
    predict_resamples = flags['r']
    importances = flags['f']
    nested_cv = flags['n']
    n_permutations = int(options['n_permutations'])
    errors_file = options['errors_file']
    preds_file = options['preds_file']
    fimp_file = options['fimp_file']
    param_file = options['param_file']

    # general options
    norm_data = flags['s']
    categorymaps = options['categorymaps']
    model_only = flags['m']
    probability = flags['p']
    prob_only = flags['z']
    random_state = int(options['random_state'])
    model_save = options['save_model']
    model_load = options['load_model']
    load_training = options['load_training']
    save_training = options['save_training']
    indexes = options['indexes']
    rowincr = int(options['rowincr'])
    n_jobs = int(options['n_jobs'])
    lowmem = flags['l']
    balance = flags['b']

    # fetch individual raster names from group
    maplist, mapnames = maps_from_group(group)

    # extract indices of category maps
    if categorymaps.strip() == '':
        categorymaps = None
    else:
        if isinstance(categorymaps, str):
            categorymaps = [categorymaps]
        cat_indexes = []
        for cat in categorymaps:
            try:
                cat_indexes.append(maplist.index(cat))
            except:
                gs.fatal('Category map {0} not in the imagery group'.format(cat))
        categorymaps = cat_indexes

    # convert class probability indexes to list
    if ',' in indexes:
        indexes = [int(i) for i in indexes.split(',')]
    else:
        indexes = int(indexes)
    if indexes == -1: indexes = None

    # error checking
    # remove @ from output in case overwriting result
    if '@' in output:
        output = output.split('@')[0]

    # feature importances selected by no cross-validation scheme used
    if importances is True and cv == 1:
        gs.fatal('Feature importances require cross-validation cv > 1')

    # output map has not been entered and model_only is not set to True
    if output == '' and model_only is not True:
        gs.fatal('No output map specified')

    # perform prediction only for class probabilities but probability flag
    # is not set to True
    if prob_only is True:
        probability = True

    # check for field attribute if trainingpoints are used
    if trainingpoints != '' and field == '':
        gs.fatal('No attribute column specified for training points')

    # check that valid combination of training data input is present
    if trainingpoints == '' and trainingmap == '' and load_training == '' \
    and model_load =='':
        gs.fatal('No training vector, raster or tabular data is present')

    # make dicts for hyperparameters, datatypes and parameters for tuning
    hyperparams_type = dict.fromkeys(hyperparams, int)
    hyperparams_type['C'] = float
    hyperparams_type['learning_rate'] = float
    hyperparams_type['subsample'] = float
    hyperparams_type['weights'] = str
    param_grid = deepcopy(hyperparams_type)
    param_grid = dict.fromkeys(param_grid, None)

    for key, val in hyperparams.iteritems():
        # split any comma separated strings and add them to the param_grid
        if ',' in val:
            param_grid[key] = [hyperparams_type[key](i) for i in val.split(',')] # add all vals to param_grid
            hyperparams[key] = [hyperparams_type[key](i) for i in val.split(',')][0] # use first param for default
        # else convert the single strings to int or float
        else:
            hyperparams[key] = hyperparams_type[key](val)

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
        scoring = ['accuracy', 'precision', 'recall', 'f1', 'kappa',\
                   'balanced_accuracy']
        search_scorer = make_scorer(metrics.matthews_corrcoef)
    else:
        scoring = ['r2', 'explained_variance', 'neg_mean_absolute_error',
                   'neg_mean_squared_error', 'neg_mean_squared_log_error',
                   'neg_median_absolute_error']
        search_scorer = 'r2'

    # -------------------------------------------------------------------------
    # Extract training data
    # -------------------------------------------------------------------------

    if model_load == '':

        # Sample training data and group id
        if load_training != '':
            X, y, group_id, sample_coords = load_training_data(load_training)
        else:
            gs.message('Extracting training data')

            # generate spatial clump/patch partitions
            # clump the labelled pixel raster and set the group_raster
            # to the clumped raster
            if trainingmap != '' and cvtype == 'clumped' and group_raster == '':
                clumped_trainingmap = 'tmp_clumped_trainingmap'
                tmp_rast.append(clumped_trainingmap)
                r.clump(input=trainingmap, output=clumped_trainingmap,
                        overwrite=True, quiet=True)
                group_raster = clumped_trainingmap
            elif trainingmap == '' and cvtype == 'clumped':
                gs.fatal('Cross-validation using clumped training areas ',
                              'requires raster-based training areas')

            # append spatial clumps or group raster to the predictors
            if group_raster != '':
                maplist2 = deepcopy(maplist)
                maplist2.append(group_raster)
            else:
                maplist2 = maplist

            # extract training data
            if trainingmap != '':
                X, y, sample_coords = extract_pixels(
                    response=trainingmap, predictors=maplist2, lowmem=lowmem, na_rm=True)
            elif trainingpoints != '':
                X, y, sample_coords = extract_points(
                    trainingpoints, maplist2, field, na_rm=True)
            group_id = None

            if len(y) < 1 or X.shape[0] < 1:
                gs.fatal('There are too few training features to perform classification')

            # take group id from last column and remove from predictors
            if group_raster != '':
                group_id = X[:, -1]
                X = np.delete(X, -1, axis=1)

            if cvtype == 'kmeans':
                clusters = KMeans(
                    n_clusters=n_partitions,
                    random_state=random_state, n_jobs=n_jobs)
                clusters.fit(sample_coords)
                group_id = clusters.labels_

            # check for labelled pixels and training data
            if y.shape[0] == 0 or X.shape[0] == 0:
                gs.fatal('No training pixels or pixels in imagery group '
                              '...check computational region')

            # shuffle data
            if group_id is None:
                X, y, sample_coords = shuffle(
                    X, y, sample_coords, random_state=random_state)
            if group_id is not None:
                X, y, sample_coords, group_id = shuffle(
                    X, y, sample_coords, group_id, random_state=random_state)

            # optionally save extracted data to .csv file
            if save_training != '':
                save_training_data(
                    X, y, group_id, sample_coords, save_training)

        # ---------------------------------------------------------------------
        # define the inner search resampling method
        # ---------------------------------------------------------------------

        if any(param_grid) is True and cv == 1 and grid_search == 'cross-validation':
            gs.fatal(
                'Hyperparameter search using cross validation requires cv > 1')

        # define inner resampling using cross-validation method
        elif any(param_grid) is True and grid_search == 'cross-validation':
            if group_id is None:
                inner = StratifiedKFold(n_splits=cv, random_state=random_state)
            else:
                inner = GroupKFold(n_splits=cv)

        # define inner resampling using the holdout method
        elif any(param_grid) is True and grid_search == 'holdout':
            if group_id is None:
                inner = ShuffleSplit(
                    n_splits=1, test_size=0.33, random_state=random_state)
            else:
                inner = GroupShuffleSplit(
                    n_splits=1, test_size=0.33, random_state=random_state)
        else:
            inner = None

        # ---------------------------------------------------------------------
        # define the outer search resampling method
        # ---------------------------------------------------------------------
        if cv > 1:
            if group_id is None:
                outer = StratifiedKFold(n_splits=cv, random_state=random_state)
            else:
                outer = GroupKFold(n_splits=cv)

        # ---------------------------------------------------------------------
        # define sample weights for gradient boosting classifiers
        # ---------------------------------------------------------------------

        # classifiers that take sample_weights
        if balance is True and mode == 'classification' and classifier in (
                'GradientBoostingClassifier', 'GaussianNB'):
            from sklearn.utils import compute_class_weight
            class_weights = compute_class_weight(
                class_weight='balanced', classes=(y), y=y)
        else:
            class_weights = None

        # ---------------------------------------------------------------------
        # define the preprocessing pipeline
        # ---------------------------------------------------------------------
        # standardization
        if norm_data is True and categorymaps is None:
            clf = Pipeline([('scaling', StandardScaler()),
                            ('classifier', clf)])

        # onehot encoding
        if categorymaps is not None and norm_data is False:
            enc = OneHotEncoder(categorical_features=categorymaps)
            enc.fit(X)
            clf = Pipeline([('onehot', OneHotEncoder(
                categorical_features=categorymaps,
                n_values=enc.n_values_, handle_unknown='ignore',
                sparse=False)),  # dense because not all clf can use sparse
                            ('classifier', clf)])

        # standardization and onehot encoding
        if norm_data is True and categorymaps is not None:
            enc = OneHotEncoder(categorical_features=categorymaps)
            enc.fit(X)
            clf = Pipeline([('onehot', OneHotEncoder(
                categorical_features=categorymaps,
                n_values=enc.n_values_, handle_unknown='ignore',
                sparse=False)),
                            ('scaling', StandardScaler()),
                            ('classifier', clf)])

        # ---------------------------------------------------------------------
        # create the hyperparameter grid search method
        # ---------------------------------------------------------------------

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
                n_jobs=n_jobs, cv=inner)

        # ---------------------------------------------------------------------
        # classifier training
        # ---------------------------------------------------------------------

        gs.message(os.linesep)
        gs.message(('Fitting model using ' + classifier))

        # fitting ensuring that all options are passed
        if classifier in ('GradientBoostingClassifier', 'GausianNB') and balance is True:
            if isinstance(clf, Pipeline):
                fit_params = {'classifier__sample_weight': class_weights}
            else:
                fit_params = {'sample_weight': class_weights}
        else:
            fit_params = {}

        if isinstance(inner, (GroupKFold, GroupShuffleSplit)):
            clf.fit(X, y, groups=group_id, **fit_params)
        else:
            clf.fit(X, y, **fit_params)

        # message best hyperparameter setup and optionally save using pandas
        if any(param_grid) is True:
            gs.message(os.linesep)
            gs.message('Best parameters:')
            gs.message(str(clf.best_params_))
            if param_file != '':
                param_df = pd.DataFrame(clf.cv_results_)
                param_df.to_csv(param_file)
            if nested_cv is False:
                clf = clf.best_estimator_

        # ---------------------------------------------------------------------
        # cross-validation
        # ---------------------------------------------------------------------

        # If cv > 1 then use cross-validation to generate performance measures
        if cv > 1 and tune_only is not True:
            if mode == 'classification' and cv > np.histogram(
		    y, bins=np.unique(y))[0].min():
                gs.message(os.linesep)
                gs.message('Number of cv folds is greater than number of '
                            'samples in some classes. Cross-validation is being'
                            ' skipped')
            else:
                gs.message(os.linesep)
                gs.message(
                    "Cross validation global performance measures......:")

                # add auc and mcc as scorer if classification is binary
                if mode == 'classification' and \
                    len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
                    scoring.append('roc_auc')
                    scoring.append('matthews_corrcoef')

                # perform the cross-validatation
                scores, cscores, fimp, models, preds = cross_val_scores(
                    clf, X, y, group_id, class_weights, outer, scoring,
                    importances, n_permutations, random_state, n_jobs)

                # from sklearn.model_selection import cross_validate
                # scores = cross_validate(clf, X, y, group_id, scoring, outer, n_jobs, fit_params=fit_params)
                # test_scoring = ['test_' + i for i in scoring]
                # gs.message(os.linesep)
                # gs.message(('Metric \t Mean \t Error'))
                # for sc in test_scoring:
                #     gs.message(sc + '\t' + str(scores[sc].mean()) + '\t' + str(scores[sc].std()))

                preds = np.hstack((preds, sample_coords))

                for method, val in scores.iteritems():
                    gs.message(
                        method+":\t%0.3f\t+/-SD\t%0.3f" %
                        (val.mean(), val.std()))

                # individual class scores
                if mode == 'classification' and len(np.unique(y)) != 2:
                    gs.message(os.linesep)
                    gs.message(
                        'Cross validation class performance measures......:')
                    gs.message('Class \t' + '\t'.join(map(str, np.unique(y))))

                    for method, val in cscores.iteritems():
                        mat_cscores = np.matrix(val)
                        gs.message(
                            method+':\t' + '\t'.join(
                                map(str, np.round(
                                        mat_cscores.mean(axis=0), 2)[0])))
                        gs.message(
                            method+' std:\t' + '\t'.join(
                                map(str, np.round(
                                        mat_cscores.std(axis=0), 2)[0])))

                # write cross-validation results for csv file
                if errors_file != '':
                    errors = pd.DataFrame(scores)
                    errors.to_csv(errors_file, mode='w')

                # write cross-validation predictions to csv file
                if preds_file != '':
                    preds = pd.DataFrame(preds)
                    preds.columns = ['y_true', 'y_pred', 'fold', 'x', 'y']
                    preds.to_csv(preds_file, mode='w')
                    text_file = open(preds_file + 't', "w")
                    text_file.write(
                        '"Integer","Real","Real","integer","Real","Real"')
                    text_file.close()

                # feature importances
                if importances is True:
                    gs.message(os.linesep)
                    gs.message("Feature importances")
                    gs.message("id" + "\t" + "Raster" + "\t" + "Importance")

                    # mean of cross-validation feature importances
                    for i in range(len(fimp.mean(axis=0))):
                        gs.message(
                            str(i) + "\t" + maplist[i] +
                            "\t" + str(round(fimp.mean(axis=0)[i], 4)))

                    if fimp_file != '':
                        np.savetxt(fname=fimp_file, X=fimp, delimiter=',',
                                   header=','.join(maplist), comments='')
    else:
        # load a previously fitted train object
        if model_load != '':
            # load a previously fitted model
            X, y, sample_coords, group_id, clf = joblib.load(model_load)
            clf.fit(X,y)

    # Optionally save the fitted model
    if model_save != '':
        joblib.dump((X, y, sample_coords, group_id, clf), model_save)

    # -------------------------------------------------------------------------
    # prediction on grass imagery group
    # -------------------------------------------------------------------------

    if model_only is not True:
        gs.message(os.linesep)

        # predict classification/regression raster
        if prob_only is False:
            gs.message('Predicting classification/regression raster...')
            predict(estimator=clf, predictors=maplist, output=output,
                    predict_type='raw', overwrite=gs.overwrite(),
                    rowincr=rowincr, n_jobs=n_jobs)

            if predict_resamples is True:
                for i in range(cv):
                    resample_name = output + '_Resample' + str(i)
                    predict(estimator=models[i], predictors=maplist,
                            output=resample_name, predict_type='raw',
                            overwrite=gs.overwrite(),
                            rowincr=rowincr, n_jobs=n_jobs)

        # predict class probabilities
        if probability is True:
            gs.message('Predicting class probabilities...')
            predict(estimator=clf, predictors=maplist, output=output,
                    predict_type='prob', index=indexes,
                    class_labels=np.unique(y), overwrite=gs.overwrite(),
                    rowincr=rowincr, n_jobs=n_jobs)

            if predict_resamples is True:
                for i in range(cv):
                    resample_name = output + '_Resample' + str(i)
                    predict(estimator=models[i], predictors=maplist,
                            output=resample_name, predict_type='prob',
                            class_labels=np.unique(y), index=indexes,
                            overwrite=gs.overwrite(),
                            rowincr=rowincr, n_jobs=n_jobs)
    else:
        gs.message("Model built and now exiting")

if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
