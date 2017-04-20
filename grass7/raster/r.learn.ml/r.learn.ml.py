#!/usr/bin/env python
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
import numpy as np
import grass.script as grass
from copy import deepcopy
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.utils import set_path

set_path('r.learn.ml')
from raster_learning import (
    model_classifiers, save_training_data, load_training_data, extract,
    maps_from_group, predict, cross_val_scores, extract_points)

tmp_rast = []

def cleanup():
    for rast in tmp_rast:
        grass.run_command("g.remove", name=rast, type='raster', flags='f', quiet=True)

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
    prob_only = flags['z']
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
    if importances is True and cv == 1:
        grass.fatal('Feature importances require cross-validation cv > 1')

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
