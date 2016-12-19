#!/usr/bin/env python
############################################################################
# MODULE:        r.randomforest
# AUTHOR:        Steven Pawley
# PURPOSE:       Supervised classification and regression of GRASS rasters
#                using the python scikit-learn package
#
# COPYRIGHT: (c) 2016 Steven Pawley, and the GRASS Development Team
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
#% key: igroup
#% label: Imagery group to be classified
#% description: Series of raster maps to be used in the random forest classification
#% required: yes
#% multiple: no
#%end

#%option G_OPT_R_INPUT
#% key: roi
#% label: Labelled pixels
#% description: Raster map with labelled pixels
#% required: no
#% guisection: Required
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% required: yes
#% label: Output Map
#% description: Prediction surface result from classification or regression model
#%end

#%option string
#% key: model
#% required: yes
#% label: Classifier
#% description: Supervised learning model to use
#% answer: RandomForestClassifier
#% options: LogisticRegression,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,GaussianNB,DecisionTreeClassifier,DecisionTreeRegressor,RandomForestClassifier,RandomForestRegressor,GradientBoostingClassifier,GradientBoostingRegressor,SVC
#%end

#%option double
#% key: c
#% description: Inverse of regularization strength (logistic regresson and SVC)
#% answer: 1.0
#% guisection: Classifier Parameters
#%end

#%option
#% key: max_features
#% type: integer
#% description: Number of features to consider during splitting for tree-based classifiers. Default -1 is sqrt(n_features) for classification, and n_features for regression
#% answer: -1
#% guisection: Classifier Parameters
#%end

#%option
#% key: max_depth
#% type: integer
#% description: Maximum tree depth for tree-based classifiers. Value of -1 uses classifier defaults
#% answer: -1
#% guisection: Classifier Parameters
#%end

#%option
#% key: min_samples_split
#% type: integer
#% description: The minimum number of samples required for node splitting in tree-based classifiers
#% answer: 2
#% guisection: Classifier Parameters
#%end

#%option
#% key: min_samples_leaf
#% type: integer
#% description: The minimum number of samples required to form a leaf node for tree-based classifiers
#% answer: 1
#% guisection: Classifier Parameters
#%end

#%option
#% key: n_estimators
#% type: integer
#% description: Number of estimators for tree-based classifiers
#% answer: 500
#% guisection: Classifier Parameters
#%end

#%option
#% key: learning_rate
#% type: double
#% description: learning rate for gradient boosting
#% answer: 0.1
#% guisection: Classifier Parameters
#%end

#%option
#% key: subsample
#% type: double
#% description: The fraction of samples to be used for fitting for gradient boosting
#% answer: 1.0
#% guisection: Classifier Parameters
#%end

# General options

#%flag
#% key: l
#% label: Use memory swap
#% guisection: Optional
#%end

#%flag
#% key: s
#% label: Standardization preprocessing
#% guisection: Optional
#%end

#%option
#% key: cv
#% type: integer
#% description: Number of cross-validation folds to perform in cv > 1
#% answer: 1
#% guisection: Optional
#%end

#%option string
#% key: cvtype
#% required: no
#% label: Non-spatial or spatial cross-validation
#% description: Non-spatial, clumped or clustered k-fold cross-validation
#% answer: Non-spatial
#% options: non-spatial,clumped,kmeans
#%end

#%option G_OPT_F_OUTPUT
#% key: errors_file
#% label: Save cross-validation global accuracy results to csv
#% required: no
#% guisection: Optional
#%end

#%option
#% key: random_state
#% type: integer
#% description: Seed to pass onto the random state for reproducible results
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

#%flag
#% key: p
#% label: Output class membership probabilities
#% guisection: Optional
#%end

#%flag
#% key: m
#% description: Build model only - do not perform prediction
#% guisection: Optional
#%end

#%flag
#% key: f
#% description: Calculate feature importances using bagging or univariate methods
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: fimp_file
#% label: Save feature importances to csv
#% required: no
#% guisection: Optional
#%end

#%flag
#% key: b
#% description: Balance number of observations by weighting for logistic regression, CART and RF methods
#% guisection: Optional
#%end

#%flag
#% key: h
#% description: Perform parameter tuning on a split of the training data
#% guisection: Optional
#%end

#%option
#% key: ratio
#% type: double
#% description: Percentage of training data to use for model development and tuning
#% answer: 0.25
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
#% exclusive: roi,load_model
#% exclusive: save_training,load_training
#%end

import atexit
import os
import numpy as np
import grass.script as grass
import tempfile
import copy
from grass.pygrass.modules.shortcuts import imagery as im
from subprocess import PIPE
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.modules.shortcuts import raster as r

try:
    import sklearn
    from sklearn.externals import joblib
    from sklearn import metrics
    from sklearn import preprocessing
    from sklearn.model_selection import StratifiedKFold
    from sklearn.model_selection import GroupKFold
    from sklearn.model_selection import train_test_split
    from sklearn.model_selection import GridSearchCV
    from sklearn.feature_selection import SelectKBest
    from sklearn.feature_selection import f_classif
    from sklearn.utils import shuffle
    from sklearn.cluster import KMeans
    
    from sklearn.linear_model import LogisticRegression
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
    from sklearn.naive_bayes import GaussianNB
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.svm import SVC

except:
    grass.fatal("Scikit learn is not installed")

if (sklearn.__version__) < 0.18:
    grass.fatal("Scikit learn 0.18 or newer is required")


def cleanup():

    grass.run_command("g.remove", name='tmp_clfmask',
                      flags="f", type="raster", quiet=True)
    grass.run_command("g.remove", name='tmp_roi_clumped',
                      flags="f", type="raster", quiet=True)


def model_classifiers(estimator, random_state, class_weight,
                      C, max_depth, max_features,
                      min_samples_split, min_samples_leaf,
                      n_estimators, subsample, learning_rate):
    
    classifiers = {
        'SVC': SVC(C=C, probability=True, random_state=random_state),
        'LogisticRegression': LogisticRegression(C=C, class_weight=class_weight,
                                                 random_state=random_state),
        'DecisionTreeClassifier': DecisionTreeClassifier(max_depth=max_depth,
                                                         max_features=max_features,
                                                         min_samples_split=min_samples_split,
                                                         min_samples_leaf=min_samples_leaf,
                                                         random_state=random_state,
                                                         class_weight=class_weight),
        'DecisionTreeRegressor': DecisionTreeRegressor(max_features=max_features,
                                                       min_samples_split=min_samples_split,
                                                       min_samples_leaf=min_samples_leaf,
                                                       random_state=random_state),
        'RandomForestClassifier': RandomForestClassifier(n_estimators=n_estimators,
                                                         class_weight=class_weight,
                                                         max_features=max_features,
                                                         min_samples_split=min_samples_split,
                                                         random_state=random_state,
                                                         n_jobs=-1,
                                                         oob_score=True),
        'RandomForestRegressor': RandomForestRegressor(n_estimators=n_estimators,
                                                       max_features=max_features,
                                                       min_samples_split=min_samples_split,
                                                       random_state=random_state,
                                                       n_jobs=-1,
                                                       oob_score=True),
        'GradientBoostingClassifier': GradientBoostingClassifier(learning_rate=learning_rate,
                                                                 n_estimators=n_estimators,
                                                                 max_depth=max_depth,
                                                                 min_samples_split=min_samples_split,
                                                                 min_samples_leaf=min_samples_leaf,
                                                                 subsample=subsample,
                                                                 max_features=max_features,
                                                                 random_state=random_state),
        'GradientBoostingRegressor': GradientBoostingRegressor(learning_rate=learning_rate,
                                                               n_estimators=n_estimators,
                                                               max_depth=max_depth,
                                                               min_samples_split=min_samples_split,
                                                               min_samples_leaf=min_samples_leaf,
                                                               subsample=subsample,
                                                               max_features=max_features,
                                                               random_state=random_state),
        'GaussianNB': GaussianNB(),
        'LinearDiscriminantAnalysis': LinearDiscriminantAnalysis(),
        'QuadraticDiscriminantAnalysis': QuadraticDiscriminantAnalysis(),
    }

    SVCOpts = {'C': [1, 10, 100], 'shrinking': [True, False]}
    LogisticRegressionOpts = {'C': [1, 10, 100, 1000]}
    DecisionTreeOpts = {'max_depth': [2, 4, 6, 8, 10, 20],
                        'max_features': ['sqrt', 'log2', None],
                        'min_samples_split': [2, 0.01, 0.05, 0.1, 0.25]}
    RandomForestOpts = {'max_features': ['sqrt', 'log2', None]}
    GradientBoostingOpts = {'learning_rate': [0.01, 0.02, 0.05, 0.1],
                            'max_depth': [3, 4, 6, 10],
                            'max_features': ['sqrt', 'log2', None],
                            'n_estimators': [50, 100, 150, 250, 500]}

    param_grids = {
        'SVC': SVCOpts,
        'LogisticRegression': LogisticRegressionOpts,
        'DecisionTreeClassifier': DecisionTreeOpts,
        'DecisionTreeRegressor': DecisionTreeOpts,
        'RandomForestClassifier': RandomForestOpts,
        'RandomForestRegressor': RandomForestOpts,
        'GradientBoostingClassifier': GradientBoostingOpts,
        'GradientBoostingRegressor': GradientBoostingOpts,
        'GaussianNB': {},
        'LinearDiscriminantAnalysis': {},
        'QuadraticDiscriminantAnalysis': {},
    }
    
    # define classifier
    clf = classifiers[estimator]
    params = param_grids[estimator]
    
    # classification or regression
    if estimator == 'LogisticRegression' \
        or estimator == 'DecisionTreeClassifier' \
        or estimator == 'RandomForestClassifier' \
        or estimator == 'GradientBoostingClassifier' \
        or estimator == 'GaussianNB' \
        or estimator == 'LinearDiscriminantAnalysis' \
        or estimator == 'QuadraticDiscriminantAnalysis' \
        or estimator == 'EarthClassifier' \
            or estimator == 'SVC':
            mode = 'classification'
    else:
        mode = 'regression'

    return (clf, params, mode)


def save_training_data(X, y, groups, file):

    """
    Saves any extracted training data to a csv file

    Parameters
    ----------
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels
    file: Path to a csv file to save data to

    """

    # if there are no group labels, create a nan filled array
    if groups is None:
        groups = np.empty((y.shape[0]))
        groups[:] = np.nan

    training_data = np.zeros((y.shape[0], X.shape[1]+2))
    training_data[:, 0:X.shape[1]] = X
    training_data[:, X.shape[1]] = y
    training_data[:, X.shape[1]+1] = groups

    np.savetxt(file, training_data, delimiter=',')


def load_training_data(file):

    """
    Loads training data and labels from a csv file

    Parameters
    ----------
    file: Path to a csv file to save data to

    Returns
    -------
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels, or None

    """

    training_data = np.loadtxt(file, delimiter=',')
    n_features = training_data.shape[1]-1

    # check to see if last column contains group labels or nans
    groups = training_data[:, -1]
    training_data = training_data[:, 0:n_features]

    if np.isnan(groups).all() is True:
        # if all nans then ignore last column
        groups = None

    # fetch X and y
    X = training_data[:, 0:n_features-1]
    y = training_data[:, -1]
    
    return(X, y, groups)


def sample_predictors(response, predictors, shuffle_data, lowmem, random_state):

    """
    Samples a list of GRASS rasters using a labelled raster
    Per raster sampling

    Parameters
    ----------
    response: String; GRASS raster with labelled pixels
    predictors: List of GRASS rasters containing explanatory variables

    Returns
    -------

    training_data: Numpy array of extracted raster values
    training_labels: Numpy array of labels
    y_indexes: Row and Columns of label positions

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
        predictor_gr.close()

    # convert any CELL maps no datavals to NaN in the training data
    for i in range(n_features):
        training_data[training_data[:, i] == -2147483648] = np.nan

    # convert indexes of training pixels from tuple to n*2 np array
    is_train = np.array(is_train).T

    # Remove nan rows from training data
    X = training_data[~np.isnan(training_data).any(axis=1)]
    y = training_labels[~np.isnan(training_data).any(axis=1)]
    y_indexes = is_train[~np.isnan(training_data).any(axis=1)]

    roi_gr.close()

    # shuffle the training data
    if shuffle_data is True:
        X, y, y_indexes = shuffle(X, y, y_indexes, random_state=random_state)

    return(X, y, y_indexes)


def prediction(clf, labels, predictors, scaler, class_probabilities,
               rowincr, output, mode):

    """
    Prediction on list of GRASS rasters using a fitted scikit learn model

    Parameters
    ----------
    clf: Scikit learn estimator object
    labels: Numpy array of the labels used for the classification
    predictors: List of GRASS rasters
    scaler: Scaler for predictors, or None
    output: Name of GRASS raster to output classification results
    rowincr: Integer of raster rows to process at one time
    class_probabilties: Predict class probabilities
    mode: String, classification or regression mode

    """

    # create a list of rasterrow objects for predictors
    n_features = len(predictors)
    nclasses = len(labels)
    rasstack = [0] * n_features

    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() is True:
            rasstack[i].open('r')
        else:
            grass.fatal("GRASS raster " + predictors[i] +
                        " does not exist.... exiting")

    # use grass.pygrass.gis.region to get information about the current region
    current = Region()

    # create a imagery mask
    # the input rasters might have different dimensions and non-value pixels.
    # r.series used to automatically create a mask by propagating the nulls
    grass.run_command("r.series", output='tmp_clfmask',
                      input=predictors, method='count', flags='n',
                      overwrite=True)

    mask_raster = RasterRow('tmp_clfmask')
    mask_raster.open('r')

    # create and open RasterRow objects for classification
    classification = RasterRow(output)
    if mode == 'classification':
        ftype = 'CELL'
        nodata = -2147483648
    else:
        ftype = 'FCELL'
        nodata = np.nan
    classification.open('w', ftype, overwrite=True)

    # create and open RasterRow objects for  probabilities if enabled
    if class_probabilities is True:
        prob_out_raster = [0] * nclasses
        prob = [0] * nclasses
        for iclass in range(nclasses):
            prob_out_raster[iclass] = output + \
                '_classPr' + str(int(labels[iclass]))
            prob[iclass] = RasterRow(prob_out_raster[iclass])
            prob[iclass].open('w', 'FCELL', overwrite=True)

    """
    Prediction using row blocks
    """

    for rowblock in range(0, current.rows, rowincr):

        # check that the row increment does not exceed the number of rows
        if rowblock+rowincr > current.rows:
            rowincr = current.rows - rowblock
        img_np_row = np.zeros((rowincr, current.cols, n_features))
        mask_np_row = np.zeros((rowincr, current.cols))

        # loop through each row, and each band
        # and add these values to the 2D array img_np_row
        for row in range(rowblock, rowblock+rowincr, 1):
            mask_np_row[row-rowblock, :] = np.array(mask_raster[row])

            for band in range(n_features):
                img_np_row[row-rowblock, :, band] = \
                    np.array(rasstack[band][row])

        mask_np_row[mask_np_row == -2147483648] = np.nan
        nanmask = np.isnan(mask_np_row)  # True in the mask means invalid data

        # reshape each row-band matrix into a n*m array
        nsamples = rowincr * current.cols
        flat_pixels = img_np_row.reshape((nsamples, n_features))

        # remove NaN values
        flat_pixels = np.nan_to_num(flat_pixels)

        # rescale
        if scaler is not None:
            flat_pixels = scaler.transform(flat_pixels)

        # perform prediction
        result = clf.predict(flat_pixels)
        result = result.reshape((rowincr, current.cols))

        # replace NaN values so that the prediction does not have a border
        result = np.ma.masked_array(result, mask=nanmask, fill_value=-99999)

        # return a copy of result, with masked values filled with a value
        result = result.filled([nodata])

        # for each row we can perform computation, and write the result into
        for row in range(rowincr):
            newrow = Buffer((result.shape[1],), mtype=ftype)
            newrow[:] = result[row, :]
            classification.put_row(newrow)

        # same for probabilities
        if class_probabilities is True and mode is 'classification':
            result_proba = clf.predict_proba(flat_pixels)

            for iclass in range(result_proba.shape[1]):

                result_proba_class = result_proba[:, iclass]
                result_proba_class = result_proba_class.reshape(
                                        (rowincr, current.cols))

                result_proba_class = np.ma.masked_array(
                    result_proba_class, mask=nanmask, fill_value=np.nan)

                result_proba_class = result_proba_class.filled([np.nan])

                for row in range(rowincr):

                    newrow = Buffer((
                                result_proba_class.shape[1],), mtype='FCELL')

                    newrow[:] = result_proba_class[row, :]
                    prob[iclass].put_row(newrow)

    classification.close()
    mask_raster.close()

    if class_probabilities is True and mode is 'classification':
        for iclass in range(nclasses):
            prob[iclass].close()


def cross_val_classification(clf, X, y, group_ids, cv, rstate):

    """
    Stratified Kfold cross-validation
    Generates several scoring_metrics

    Parameters
    ----------
    clf: Scikit learn estimator object
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    group_ids: Numpy array containing group labels for samples
    cv: Integer of cross-validation folds
    rstate: Seed to pass to the random number generator

    Returns
    -------
    scores: Dictionary of global accuracy measures per fold
    y_test_agg: Aggregated test responses
    y_pred_agg: Aggregated predicted responses

    """

    # dicts of lists to store metrics
    scores = {
        'accuracy': [],
        'auc': [],
        'r2': []
    }

    # generate Kfold indices
    if group_ids is None:
        k_fold = StratifiedKFold(
            n_splits=cv, shuffle=False, random_state=rstate).split(X, y)
    else:

        n_groups = len(np.unique(group_ids))

        if cv > n_groups:
            grass.message(
                "Number of cv folds cannot be larger than the number of groups in the zonal raster, using n_groups")
            cv = n_groups
        k_fold = GroupKFold(n_splits=cv).split(X, y, groups=group_ids)

    y_test_agg = []
    y_pred_agg = []

    # loop through each fold
    for train_indices, test_indices in k_fold:

        X_train, X_test = X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]

        # fit the model on the training data and predict the test data
        fit = clf.fit(X_train, y_train)
        y_pred = fit.predict(X_test)

        y_test_agg = np.append(y_test_agg, y_test)
        y_pred_agg = np.append(y_pred_agg, y_pred)

        # calculate metrics
        try:
            scores['accuracy'] = np.append(
                scores['accuracy'], metrics.accuracy_score(y_test, y_pred))
        except:
            pass

        scores['r2'] = np.append(
            scores['r2'], metrics.r2_score(y_test, y_pred))

        # test for if binary and classes equal 0,1
        if len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
            try:
                y_pred_proba = fit.predict_proba(X_test)[:, 1]

                scores['auc'] = np.append(
                    scores['auc'], metrics.roc_auc_score(y_test, y_pred_proba))
            except:
                pass

    return(scores, y_test_agg, y_pred_agg)


def tune_split(X, y, Id, estimator, metric, params, test_size, random_state):

    if Id is None:
        X, X_devel, y, y_devel = train_test_split(X, y, test_size=test_size,
                            random_state=random_state)
        Id_devel = None
    else:
        X, X_devel, y, y_devel, Id, Id_devel = train_test_split(X, y, Id, test_size=test_size,
                            random_state=random_state, stratify=Id)

    clf = GridSearchCV(estimator=estimator, cv=3, param_grid=params,
                              scoring=metric, n_jobs=-1)
    
    clf.fit(X_devel, y_devel)

    return (X, X_devel, y, y_devel, Id, Id_devel, clf)


def feature_importances(clf, X, y):

    try:
        clfimp = clf.feature_importances_
    except:
        sk = SelectKBest(f_classif, k='all')
        sk_fit = sk.fit(X, y)
        clfimp = sk_fit.scores_

    return (clfimp)


def sample_training_data(roi, maplist, cv, cvtype, model_load,
                         load_training, save_training, lowmem, random_state):
    
    # load the model or training data
    if model_load != '':
        clf = joblib.load(model_load)
        X, y, Id = load_training_data(
                            model_load.replace('.pkl', '.csv'))
    else:
        clf = None
        if load_training != '':
            X, y, Id = load_training_data(load_training)
        else:
            # create clumped roi for spatial cross validation
            if cv > 1 and cvtype == 'clumped':
                r.clump(input=roi, output='tmp_roi_clumped', overwrite=True, quiet=True)
                maplist2 = copy.deepcopy(maplist)
                maplist2.append('tmp_roi_clumped')
                X, y, sample_coords = sample_predictors(response=roi,
                                                        predictors=maplist2,
                                                        shuffle_data=False,
                                                        lowmem=lowmem,
                                                        random_state=random_state)
                 # take Id from last column
                Id = X[:, -1]

                # remove Id column from predictors
                X = X[:, 0:X.shape[1]-1]
            else:
                # query predictor rasters with training features
                Id = None
                X, y, sample_coords = sample_predictors(
                    response=roi, predictors=maplist, shuffle_data=True,
                    lowmem=lowmem, random_state=random_state)
                
                # perform kmeans clustering on point coordinates
                if cv > 1 and cvtype == 'kmeans':
                    clusters = KMeans(
                        n_clusters=cv, random_state=random_state, n_jobs=-1)
                    clusters.fit(sample_coords)
                    Id = clusters.labels_

            if save_training != '':
                save_training_data(X, y, Id, save_training)

    
    return (X, y, Id, clf)


def main():

    """
    GRASS options and flags
    -----------------------
    """

    # General options and flags
    igroup = options['igroup']
    roi = options['roi']
    output = options['output']
    model = options['model']
    norm_data = flags['s']
    cv = int(options['cv'])
    cvtype = options['cvtype']
    modelonly = flags['m']
    probability = flags['p']
    rowincr = int(options['lines'])
    random_state = int(options['random_state'])
    model_save = options['save_model']
    model_load = options['load_model']
    load_training = options['load_training']
    save_training = options['save_training']
    importances = flags['f']
    tuning = flags['h']
    lowmem = flags['l']
    ratio = float(options['ratio'])
    errors_file = options['errors_file']
    fimp_file = options['fimp_file']
    ratio = float(options['ratio'])

    if flags['b'] is True:
        class_weight = 'balanced'
    else:
        class_weight = None

    # classifier options
    C = float(options['c'])
    min_samples_split = int(options['min_samples_split'])
    min_samples_leaf = int(options['min_samples_leaf'])
    n_estimators = int(options['n_estimators'])
    learning_rate = float(options['learning_rate'])
    subsample = float(options['subsample'])
    max_depth = int(options['max_depth'])
    max_features = int(options['max_features'])

    if max_features == -1:
        max_features = str('auto')
    if max_depth == -1:
        max_depth = None

    if (model == 'LinearDiscriminantAnalysis' or
    model == 'QuadraticDiscriminantAnalysis' or
    model == 'GaussianNB'):
        grass.warning('No parameters to tune for selected model...ignoring')
        tuning = False
        
    """
    Obtain information about GRASS rasters to be classified
    -------------------------------------------------------
    """

    Id = None

    # fetch individual raster names from group
    groupmaps = im.group(group=igroup, flags="g",
                         quiet=True, stdout_=PIPE).outputs.stdout

    maplist = groupmaps.split(os.linesep)
    maplist = maplist[0:len(maplist)-1]
    n_features = len(maplist)

    # Error checking for m_features settings
    if max_features > n_features:
        max_features = n_features

    """
    Sample training data using training ROI
    ---------------------------------------
    """

    # load or sample training data
    X, y, Id, clf = sample_training_data(roi, maplist, cv, cvtype, model_load,
                                         load_training,
                                         save_training, lowmem, random_state)

    # determine the number of class labels using np.unique
    labels = np.unique(y)

    """
    Data preprocessing
    --------------------
    """
    if norm_data is True:
        scaler = preprocessing.StandardScaler().fit(X)
        X = scaler.transform(X)
    else:
        scaler = None

    """
    Train the classifier
    --------------------
    """

    grass.message("Model=" + model)
    clf, param_grid, mode =\
        model_classifiers(model, random_state,
                          class_weight, C, max_depth,
                          max_features, min_samples_split,
                          min_samples_leaf, n_estimators,
                          subsample, learning_rate)

    # check for classification or regression mode
    if mode == 'regression' and probability is True:
        grass.warning('Class probabilities only possible for classifications...ignoring')
        probability = False

    # define classifier unless model is to be loaded from file
    if model_load == '':

        # data splitting for automatic parameter tuning
        if tuning is True:                

            if mode == 'classification':
                metric = 'accuracy'
            else:
                metric = 'r2'
            
            X, X_devel, y, y_devel, Id, Id_devel, clf = \
                tune_split(X, y, Id, clf, metric, param_grid,
                           ratio, random_state)

            grass.message('\n')
            grass.message('Searched parameters:')
            grass.message(str(clf.param_grid))
            grass.message('\n')
            grass.message('Best parameters:')
            grass.message(str(clf.best_params_))

            clf = clf.best_estimator_

        """
        Cross Validation
        ----------------
        """

        # If cv > 1 then use cross-validation to generate performance measures
        if cv > 1:

            grass.message('\r\n')
            grass.message(
                "Cross validation global performance measures......:")

            # get metrics from kfold cross validation
            scores, y_test, y_pred = cross_val_classification(
                clf, X, y, Id, cv, random_state)

            if mode == 'classification':

                grass.message(
                    "Accuracy:\t%0.2f\t+/-SD\t%0.2f" %
                    (scores['accuracy'].mean(), scores['accuracy'].std()))

                # test for if binary and classes equal 0,1
                if len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
                    grass.message(
                        "ROC AUC :\t%0.2f\t+/-SD\t%0.2f" %
                        (scores['auc'].mean(), scores['auc'].std()))

                # classification report
                grass.message("\n")
                grass.message("Classification report:")
                grass.message(metrics.classification_report(y_test, y_pred))                   

            else:
                grass.message("R2:\t%0.2f\t+/-\t%0.2f" %
                              (scores['r2'].mean(), scores['r2'].std()))
            
            # write cross-validation results for csv file
            if errors_file != '':
                try:
                    import pandas as pd
                    
                    if mode == 'classification':
                        errors = pd.DataFrame({'accuracy': scores['accuracy'],
                                               'auc': scores['auc']})
                    else:
                        errors = pd.DataFrame({'r2': scores['r2']})
                    errors.to_csv(errors_file, mode='w')
                except:
                    grass.warning("Pandas is not installed. Pandas is required to write the cross-validation results to file")

        # train classifier
        clf.fit(X, y)
        y_pred = clf.predict(X)

        # check that all classes can be predicted
        # otherwise update labels with only predictable classes
        # otherwise the predicted probabilties will fail
        test = len(np.unique(y_pred)) == len(labels)
        if test is False:
            labels = np.unique(y_pred)

        """
        Feature Importances
        -------------------
        """

        if importances is True:

            clfimp = feature_importances(clf, X, y)

            # output to GRASS message
            grass.message("\r\n")
            grass.message("Feature importances")
            grass.message("id" + "\t" + "Raster" + "\t" + "Importance")
            for i in range(len(clfimp)):
                grass.message(
                    str(i) + "\t" + maplist[i] +
                    "\t" + str(round(clfimp[i], 4)))

            if fimp_file != '':
                fimp_output = pd.DataFrame(
                    {'grass raster': maplist, 'importance': clfimp})
                fimp_output.to_csv(
                    path_or_buf=fimp_file,
                    header=['grass raster', 'importance'])

        """
        Save the fitted model
        ---------------------
        """

        if model_save != '':
            joblib.dump(clf, model_save)

            save_training_data(
                X, y, Id, model_save.replace(".pkl", ".csv"))


        if modelonly is True:
            grass.fatal("Model built and now exiting")

    """
    Prediction on the rest of the GRASS rasters in the imagery group
    ----------------------------------------------------------------
    """
    prediction(clf, labels, maplist, scaler, probability,
               rowincr, output, mode)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
