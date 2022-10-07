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

# %module
# % description: Supervised classification and regression of GRASS rasters using the python scikit-learn package
# % keyword: raster
# % keyword: classification
# % keyword: regression
# % keyword: machine learning
# % keyword: scikit-learn
# % keyword: parallel
# %end

# %option G_OPT_I_GROUP
# % key: group
# % label: Group of raster layers to be classified
# % description: GRASS imagery group of raster maps representing feature variables to be used in the machine learning model
# % required: yes
# % multiple: no
# %end

# %option G_OPT_R_INPUT
# % key: trainingmap
# % label: Labelled pixels
# % description: Raster map with labelled pixels for training
# % required: no
# % guisection: Required
# %end

# %option G_OPT_V_INPUT
# % key: trainingpoints
# % label: Vector map with training samples
# % description: Vector points map where each point is used as training sample. Handling of missing values in training data can be choosen later.
# % required: no
# % guisection: Required
# %end

# %option G_OPT_DB_COLUMN
# % key: field
# % label: Response attribute column
# % description: Name of attribute column in trainingpoints table containing response values
# % required: no
# % guisection: Required
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % label: Output Map
# % description: Raster layer name to store result from classification or regression model. The name will also used as a perfix if class probabilities or intermediate of cross-validation results are ordered as maps.
# % guisection: Required
# % required: no
# %end

# %option string
# % key: classifier
# % label: Classifier
# % description: Supervised learning model to use
# % answer: RandomForestClassifier
# % options: LogisticRegression,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,KNeighborsClassifier,GaussianNB,DecisionTreeClassifier,DecisionTreeRegressor,RandomForestClassifier,RandomForestRegressor,ExtraTreesClassifier,ExtraTreesRegressor,GradientBoostingClassifier,GradientBoostingRegressor,SVC,EarthClassifier,EarthRegressor
# % guisection: Classifier settings
# % required: no
# %end

# %option
# % key: c
# % type: double
# % label: Inverse of regularization strength
# % description: Inverse of regularization strength (LogisticRegression and SVC)
# % answer: 1.0
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: max_features
# % type: integer
# % label: Number of features available during node splitting; zero uses classifier defaults
# % description: Number of features available during node splitting (tree-based classifiers and regressors)
# % answer:0
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: max_depth
# % type: integer
# % label: Maximum tree depth; zero uses classifier defaults
# % description: Maximum tree depth for tree-based method; zero uses classifier defaults (full-growing for Decision trees and Randomforest, 3 for GBM)
# % answer:0
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: min_samples_split
# % type: integer
# % label: The minimum number of samples required for node splitting
# % description: The minimum number of samples required for node splitting in tree-based classifiers
# % answer: 2
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: min_samples_leaf
# % type: integer
# % label: The minimum number of samples required to form a leaf node
# % description: The minimum number of samples required to form a leaf node in tree-based classifiers
# % answer: 1
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: n_estimators
# % type: integer
# % label: Number of estimators
# % description: Number of estimators (trees) in ensemble tree-based classifiers
# % answer: 100
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: learning_rate
# % type: double
# % label: learning rate
# % description: learning rate (also known as shrinkage) for gradient boosting methods
# % answer: 0.1
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: subsample
# % type: double
# % label: The fraction of samples to be used for fitting
# % description: The fraction of samples to be used for fitting, controls stochastic behaviour of gradient boosting methods
# % answer: 1.0
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: max_degree
# % type: integer
# % label: The maximum degree of terms in forward pass
# % description: The maximum degree of terms in forward pass for Py-earth
# % answer: 1
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option
# % key: n_neighbors
# % type: integer
# % label: Number of neighbors to use
# % description: Number of neighbors to use
# % answer: 5
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option string
# % key: weights
# % label: weight function
# % description: Distance weight function for k-nearest neighbours model prediction
# % answer: uniform
# % options: uniform,distance
# % multiple: yes
# % guisection: Classifier settings
# %end

# %option string
# % key: grid_search
# % label: Resampling method to use for hyperparameter optimization
# % description: Resampling method to use for hyperparameter optimization
# % options: cross-validation,holdout
# % answer: cross-validation
# % multiple: no
# % guisection: Classifier settings
# %end

# %option G_OPT_R_INPUT
# % key: categorymaps
# % required: no
# % multiple: yes
# % label: Names of categorical rasters within the imagery group
# % description: Names of categorical rasters within the imagery group that will be one-hot encoded. Leave empty if none.
# % guisection: Optional
# %end

# %option string
# % key: cvtype
# % label: Non-spatial or spatial cross-validation
# % description: Perform non-spatial, clumped or clustered k-fold cross-validation
# % answer: Non-spatial
# % options: non-spatial,clumped,kmeans
# % guisection: Cross validation
# %end

# %option
# % key: n_partitions
# % type: integer
# % label: Number of k-means spatial partitions
# % description: Number of k-means spatial partitions for k-means clustered cross-validation
# % answer: 10
# % guisection: Cross validation
# %end

# %option G_OPT_R_INPUT
# % key: group_raster
# % label: Custom group ids for training samples from GRASS raster
# % description: GRASS raster containing group ids for training samples. Samples with the same group id will not be split between training and test cross-validation folds
# % required: no
# % guisection: Cross validation
# %end

# %option
# % key: cv
# % type: integer
# % description: Number of cross-validation folds
# % answer: 1
# % guisection: Cross validation
# %end

# %option
# % key: n_permutations
# % type: integer
# % description: Number of permutations to perform for feature importances
# % answer: 10
# % guisection: Cross validation
# %end

# %flag
# % key: t
# % description: Perform hyperparameter tuning only
# % guisection: Cross validation
# %end

# %flag
# % key: f
# % label: Estimate permutation-based feature importances
# % description: Estimate feature importance using a permutation-based method
# % guisection: Cross validation
# %end

# %flag
# % key: r
# % label: Make predictions for cross validation resamples
# % description: Produce raster predictions for all cross validation resamples
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: errors_file
# % label: Save cross-validation global accuracy results to csv
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: preds_file
# % label: Save cross-validation predictions to csv
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: fimp_file
# % label: Save feature importances to csv
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: param_file
# % label: Save hyperparameter search scores to csv
# % required: no
# % guisection: Cross validation
# %end

# %option
# % key: random_state
# % type: integer
# % description: Seed to use for random state
# % answer: 1
# % guisection: Optional
# %end

# %option
# % key: indexes
# % type: integer
# % description: Indexes of class probabilities to predict. Default -1 predicts all classes
# % answer: -1
# % guisection: Optional
# % multiple: yes
# %end

# %option
# % key: rowincr
# % type: integer
# % description: Maximum number of raster rows to read/write in single chunk whilst performing prediction
# % answer: 25
# % guisection: Optional
# %end

# %option
# % key: n_jobs
# % type: integer
# % description: Number of cores for multiprocessing, -2 is n_cores-1
# % answer: -2
# % guisection: Optional
# %end

# %flag
# % key: s
# % label: Standardization preprocessing
# % description: Standardize feature variables (convert values the get zero mean and unit variance).
# % guisection: Optional
# %end

# %flag
# % key: p
# % label: Output class membership probabilities
# % description: A raster layer is created for each class. It is recommended to give a list of particular classes in interest to avoid consumption of large amounts of disk space.
# % guisection: Optional
# %end

# %flag
# % key: z
# % label: Only predict class probabilities
# % guisection: Optional
# %end

# %flag
# % key: m
# % description: Build model only - do not perform prediction
# % guisection: Optional
# %end

# %flag
# % key: b
# % description: Balance training data using class weights
# % guisection: Optional
# %end

# %flag
# % key: l
# % label: Use memory swap
# % guisection: Optional
# %end

# %option G_OPT_F_OUTPUT
# % key: save_training
# % label: Save training data to csv
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_F_INPUT
# % key: load_training
# % label: Load training data from csv
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_F_OUTPUT
# % key: save_model
# % label: Save model to file (for compression use e.g. '.gz' extension)
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_F_INPUT
# % key: load_model
# % label: Load model from file
# % required: no
# % guisection: Optional
# %end

# %rules
# % exclusive: trainingmap,load_model
# % exclusive: load_training,save_training
# % exclusive: trainingmap,load_training
# % exclusive: trainingpoints,trainingmap
# % exclusive: trainingpoints,load_training
# % requires: fimp_file,-f
# %end

from __future__ import absolute_import
import atexit
import os
import tempfile
from copy import deepcopy
import numpy as np
import grass.script as gs
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import imagery as im
from grass.pygrass.gis.region import Region
from grass.pygrass.raster import RasterRow


try:
    basestring
except NameError:
    basestring = str


def model_classifiers(estimator, random_state, n_jobs, p, weights=None):
    """
    Provides the classifiers and parameters using by the module

    Args
    ----
    estimator (string): Name of scikit learn estimator
    random_state (float): Seed to use in randomized components
    n_jobs (integer): Number of processing cores to use
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
        RandomForestClassifier,
        RandomForestRegressor,
        ExtraTreesClassifier,
        ExtraTreesRegressor,
    )
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
    from sklearn.svm import SVC
    from sklearn.neighbors import KNeighborsClassifier

    # convert balanced boolean to scikit learn method
    if weights is True:
        weights = "balanced"
    else:
        weights = None

    # optional packages that add additional classifiers here
    if estimator == "EarthClassifier" or estimator == "EarthRegressor":
        try:
            from sklearn.pipeline import Pipeline
            from pyearth import Earth

            earth_classifier = Pipeline(
                [
                    ("classifier", Earth(max_degree=p["max_degree"])),
                    ("Logistic", LogisticRegression(n_jobs=n_jobs)),
                ]
            )

            classifiers = {
                "EarthClassifier": earth_classifier,
                "EarthRegressor": Earth(max_degree=p["max_degree"]),
            }
        except:
            gs.fatal("Py-earth package not installed")
    else:
        # core sklearn classifiers go here
        classifiers = {
            "SVC": SVC(
                C=p["C"],
                class_weight=weights,
                probability=True,
                random_state=random_state,
            ),
            "LogisticRegression": LogisticRegression(
                C=p["C"],
                class_weight=weights,
                solver="liblinear",
                random_state=random_state,
                n_jobs=n_jobs,
                fit_intercept=True,
            ),
            "DecisionTreeClassifier": DecisionTreeClassifier(
                max_depth=p["max_depth"],
                max_features=p["max_features"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                class_weight=weights,
                random_state=random_state,
            ),
            "DecisionTreeRegressor": DecisionTreeRegressor(
                max_features=p["max_features"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                random_state=random_state,
            ),
            "RandomForestClassifier": RandomForestClassifier(
                n_estimators=p["n_estimators"],
                max_features=p["max_features"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                class_weight=weights,
                random_state=random_state,
                n_jobs=n_jobs,
                oob_score=False,
            ),
            "RandomForestRegressor": RandomForestRegressor(
                n_estimators=p["n_estimators"],
                max_features=p["max_features"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                random_state=random_state,
                n_jobs=n_jobs,
                oob_score=False,
            ),
            "ExtraTreesClassifier": ExtraTreesClassifier(
                n_estimators=p["n_estimators"],
                max_features=p["max_features"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                class_weight=weights,
                random_state=random_state,
                n_jobs=n_jobs,
                oob_score=False,
            ),
            "ExtraTreesRegressor": ExtraTreesRegressor(
                n_estimators=p["n_estimators"],
                max_features=p["max_features"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                random_state=random_state,
                n_jobs=n_jobs,
                oob_score=False,
            ),
            "GradientBoostingClassifier": GradientBoostingClassifier(
                learning_rate=p["learning_rate"],
                n_estimators=p["n_estimators"],
                max_depth=p["max_depth"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                subsample=p["subsample"],
                max_features=p["max_features"],
                random_state=random_state,
            ),
            "GradientBoostingRegressor": GradientBoostingRegressor(
                learning_rate=p["learning_rate"],
                n_estimators=p["n_estimators"],
                max_depth=p["max_depth"],
                min_samples_split=p["min_samples_split"],
                min_samples_leaf=p["min_samples_leaf"],
                subsample=p["subsample"],
                max_features=p["max_features"],
                random_state=random_state,
            ),
            "GaussianNB": GaussianNB(),
            "LinearDiscriminantAnalysis": LinearDiscriminantAnalysis(),
            "QuadraticDiscriminantAnalysis": QuadraticDiscriminantAnalysis(),
            "KNeighborsClassifier": KNeighborsClassifier(
                n_neighbors=p["n_neighbors"], weights=p["weights"], n_jobs=n_jobs
            ),
        }

    # define classifier
    clf = classifiers[estimator]

    # classification or regression
    if (
        estimator == "LogisticRegression"
        or estimator == "DecisionTreeClassifier"
        or estimator == "RandomForestClassifier"
        or estimator == "ExtraTreesClassifier"
        or estimator == "GradientBoostingClassifier"
        or estimator == "GaussianNB"
        or estimator == "LinearDiscriminantAnalysis"
        or estimator == "QuadraticDiscriminantAnalysis"
        or estimator == "EarthClassifier"
        or estimator == "SVC"
        or estimator == "KNeighborsClassifier"
    ):
        mode = "classification"
    else:
        mode = "regression"

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
    np.savetxt(file, training_data, delimiter=",")


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

    training_data = np.loadtxt(file, delimiter=",")
    n_cols = training_data.shape[1]
    last_Xcol = n_cols - 2

    # check to see if last column contains group labels or nans
    groups = training_data[:, -1]

    # if all nans then set groups to None
    if bool(np.isnan(groups).all()) is True:
        groups = None

    # fetch X and y
    coords = training_data[:, 0:2]
    X = training_data[:, 2:last_Xcol]
    y = training_data[:, -2]

    return (X, y, groups, coords)


def save_model(estimator, X, y, sample_coords, groups, filename):
    import joblib

    joblib.dump((estimator, X, y, sample_coords, group_id), filename)


def load_model(filename):
    import joblib

    estimator, X, y, sample_coords, groups = joblib.load(filename)

    return (estimator, X, y, sample_coords, groups)


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

    from grass.pygrass.utils import pixel2coor

    current = Region()

    # open response raster as rasterrow and read as np array
    if RasterRow(response).exist() is True:
        roi_gr = RasterRow(response)
        roi_gr.open("r")

        if lowmem is False:
            response_np = np.array(roi_gr)
        else:
            response_np = np.memmap(
                tempfile.NamedTemporaryFile(),
                dtype="float32",
                mode="w+",
                shape=(current.rows, current.cols),
            )
            response_np[:] = np.array(roi_gr)[:]
    else:
        gs.fatal("GRASS GIS response raster map <%s> does not exist" % response)

    # determine number of predictor rasters
    n_features = len(predictors)

    # check to see if all predictors exist
    for i in range(n_features):
        if RasterRow(predictors[i]).exist() is not True:
            gs.fatal("GRASS raster " + predictors[i] + " does not exist.... exiting")

    # check if any of those pixels are labelled (not equal to nodata)
    # can use even if roi is FCELL because nodata will be nan
    is_train = np.nonzero(response_np > -2147483648)
    training_labels = response_np[is_train]
    n_labels = np.array(is_train).shape[1]

    # Create a zero numpy array of len training labels
    if lowmem is False:
        training_data = np.zeros((n_labels, n_features))
    else:
        training_data = np.memmap(
            tempfile.NamedTemporaryFile(),
            dtype="float32",
            mode="w+",
            shape=(n_labels, n_features),
        )

    # Loop through each raster and sample pixel values at training indexes
    if lowmem is True:
        feature_np = np.memmap(
            tempfile.NamedTemporaryFile(),
            dtype="float32",
            mode="w+",
            shape=(current.rows, current.cols),
        )

    for f in range(n_features):
        predictor_gr = RasterRow(predictors[f])
        predictor_gr.open("r")

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
        if np.isnan(training_data).any():
            gs.message(
                "Removing samples with NaN values in the raster feature variables..."
            )
        training_labels = training_labels[~np.isnan(training_data).any(axis=1)]
        is_train = is_train[~np.isnan(training_data).any(axis=1)]
        training_data = training_data[~np.isnan(training_data).any(axis=1)]

    return (training_data, training_labels, is_train)


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

    from grass.pygrass.vector import VectorTopo
    from grass.pygrass.utils import get_raster_for_points

    # open grass vector
    points = VectorTopo(gvector.split("@")[0])
    points.open("r")

    # create link to attribute table
    points.dblinks.by_name(name=gvector)

    # extract table field to numpy array
    table = points.table
    cur = table.execute(
        "SELECT {field} FROM {name}".format(field=field, name=table.name)
    )
    y = np.array([np.isnan if c is None else c[0] for c in cur])
    y = np.array(y, dtype="float")

    # extract raster data
    X = np.zeros((points.num_primitives()["point"], len(grasters)), dtype=float)
    for i, raster in enumerate(grasters):
        rio = RasterRow(raster)
        if rio.exist() is False:
            gs.fatal("Raster {x} does not exist....".format(x=raster))
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
        y = np.asarray(y, dtype="int")

    # close
    points.close()

    # remove samples containing NaNs
    if na_rm is True:
        if np.isnan(X).any():
            gs.message(
                "Removing samples with NaN values in the raster feature variables..."
            )

        y = y[~np.isnan(X).any(axis=1)]
        coordinates = coordinates[~np.isnan(X).any(axis=1)]
        X = X[~np.isnan(X).any(axis=1)]

    return (X, y, coordinates)


def predict(
    estimator,
    predictors,
    output,
    predict_type="raw",
    index=None,
    class_labels=None,
    overwrite=False,
    rowincr=25,
    n_jobs=-2,
):
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

    from joblib import Parallel, delayed
    from grass.pygrass.raster import numpy2raster

    # TODO
    # better memory efficiency and use of memmap for parallel
    # processing
    # from sklearn.externals.joblib.pool import has_shareable_memory

    # first unwrap the estimator from any potential pipelines or gridsearchCV
    if type(estimator).__name__ == "Pipeline":
        clf_type = estimator.named_steps["classifier"]
    else:
        clf_type = estimator

    if (
        type(clf_type).__name__ == "GridSearchCV"
        or type(clf_type).__name__ == "RandomizedSearchCV"
    ):
        clf_type = clf_type.best_estimator_

    # check name against already multithreaded classifiers
    if type(clf_type).__name__ in [
        "RandomForestClassifier",
        "RandomForestRegressor",
        "ExtraTreesClassifier",
        "ExtraTreesRegressor",
        "KNeighborsClassifier",
    ]:
        n_jobs = 1

    # convert potential single index to list
    if isinstance(index, int):
        index = [index]

    # open predictors as list of rasterrow objects
    current = Region()

    # create lists of row increments
    row_mins, row_maxs = [], []
    for row in range(0, current.rows, rowincr):
        if row + rowincr > current.rows:
            rowincr = current.rows - row
        row_mins.append(row)
        row_maxs.append(row + rowincr)

    # perform predictions on lists of row increments in parallel
    prediction = Parallel(n_jobs=n_jobs, max_nbytes=None)(
        delayed(__predict_parallel2)(
            estimator, predictors, predict_type, current, row_min, row_max
        )
        for row_min, row_max in zip(row_mins, row_maxs)
    )
    prediction = np.vstack(prediction)

    # determine raster dtype
    if prediction.dtype == "float":
        ftype = "FCELL"
    else:
        ftype = "CELL"

    #  writing of predicted results for classification
    if predict_type == "raw":
        numpy2raster(array=prediction, mtype=ftype, rastname=output, overwrite=True)
        gs.raster_history(output)

    # writing of predicted results for probabilities
    if predict_type == "prob":

        # use class labels if supplied
        # else output predictions as 0,1,2...n
        if class_labels is None:
            class_labels = range(prediction.shape[2])

        # output all class probabilities if subset is not specified
        if index is None:
            index = class_labels

        # select indexes of predictions 3d numpy array to be exported to rasters
        selected_prediction_indexes = [
            i for i, x in enumerate(class_labels) if x in index
        ]

        # write each 3d of numpy array as a probability raster
        for pred_index, label in zip(selected_prediction_indexes, index):
            rastername = output + "_" + str(label)
            numpy2raster(
                array=prediction[:, :, pred_index],
                mtype="FCELL",
                rastname=rastername,
                overwrite=overwrite,
            )
            gs.raster_history(output)


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

    # initialize output
    result, mask = None, None

    # open grass rasters
    n_features = len(predictors)
    rasstack = [0] * n_features

    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() is True:
            rasstack[i].open("r")
        else:
            gs.fatal("GRASS raster " + predictors[i] + " does not exist.... exiting")

    # loop through each row, and each band and add to 2D img_np_row
    img_np_row = np.zeros((row_max - row_min, current.cols, n_features))
    for row in range(row_min, row_max):
        for band in range(n_features):
            img_np_row[row - row_min, :, band] = np.array(rasstack[band][row])

    # create mask
    img_np_row[img_np_row == -2147483648] = np.nan
    mask = np.zeros((img_np_row.shape[0], img_np_row.shape[1]))
    for feature in range(n_features):
        invalid_indexes = np.nonzero(np.isnan(img_np_row[:, :, feature]))
        mask[invalid_indexes] = np.nan

    # reshape each row-band matrix into a n*m array
    nsamples = (row_max - row_min) * current.cols
    flat_pixels = img_np_row.reshape((nsamples, n_features))

    # remove NaNs prior to passing to scikit-learn predict
    flat_pixels = np.nan_to_num(flat_pixels)

    # perform prediction for classification/regression
    if predict_type == "raw":
        result = estimator.predict(flat_pixels)
        result = result.reshape((row_max - row_min, current.cols))

        # determine nodata value and grass raster type
        if result.dtype == "float":
            nodata = np.nan
        else:
            nodata = -2147483648

        # replace NaN values so that the prediction does not have a border
        result[np.nonzero(np.isnan(mask))] = nodata

    # perform prediction for class probabilities
    if predict_type == "prob":
        result = estimator.predict_proba(flat_pixels)
        result = result.reshape((row_max - row_min, current.cols, result.shape[1]))
        result[np.nonzero(np.isnan(mask))] = np.nan

    # close maps
    for i in range(n_features):
        rasstack[i].close()

    return result


def specificity_score(y_true, y_pred):
    """
    Calculate specificity score

    Args
    ----
    y_true (1d numpy array): true values of class labels
    y_pred (1d numpy array): predicted class labels

    Returns
    -------
    specificity (float): specificity score
    """

    from sklearn.metrics import confusion_matrix

    cm = confusion_matrix(y_true, y_pred)
    tn = float(cm[0][0])
    fp = float(cm[0][1])

    return tn / (tn + fp)


def varimp_permutation(estimator, X, y, n_permutations, scorer, n_jobs, random_state):
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
    estimator (object): estimator that has been fitted to a training partition
    X, y: 2d and 1d numpy arrays of data and labels from a test partition
    n_permutations (integer): number of random permutations to apply
    scorer (object): scikit-learn metric function to use
    n_jobs (integer): integer, number of processing cores
    random_state (float): seed to pass to the numpy random.seed

    Returns
    -------
    scores (2d numpy array): scores for each predictor following permutation
    """

    from joblib import Parallel, delayed

    # calculate score on original variables without permutation
    # determine best metric type for binary/multiclass/regression scenarios
    y_pred = estimator.predict(X)
    best_score = scorer(y, y_pred)

    # repeated permutations and return difference from best score per predictor
    scores = Parallel(n_jobs=n_jobs)(
        delayed(__permute)(estimator, X, y, best_score, scorer, random_state)
        for n in range(n_permutations)
    )

    # average the repetitions
    scores = np.asarray(scores)
    scores = scores.mean(axis=0)

    return scores


def __permute(estimator, X, y, best_score, scorer, random_state):
    """
    Permute each predictor and measure difference from best score

    Args
    ----
    estimator (object): scikit learn estimator
    X, y: 2d and 1d numpy arrays data and labels from a test partition
    best_score (float): best scorer obtained on unperturbed data
    scorer (object): scoring method to use to measure importances
    random_state (float): random seed

    Returns
    -------
    scores (2D numpy array): scores for each predictor following permutation
    """

    from numpy.random import RandomState

    rstate = RandomState(random_state)

    # permute each predictor variable and assess difference in score
    scores = np.zeros(X.shape[1])

    for i in range(X.shape[1]):
        Xscram = np.copy(X)
        Xscram[:, i] = rstate.choice(X[:, i], X.shape[0])

        # fit the model on the training data and predict the test data
        y_pred = estimator.predict(Xscram)
        scores[i] = best_score - scorer(y, y_pred)
        if scores[i] < 0:
            scores[i] = 0

    return scores


def __parallel_fit(estimator, X, y, groups, train_indices, sample_weight):
    """
    Fit classifiers/regressors in parallel

    Args
    ----
    estimator (object): scikit learn estimator
    X, y: 2D and 1D numpy arrays of training data and labels
    groups (1D numpy array): of len(y) containing group labels
    train_indices, test_indices: 1D numpy arrays of indices to use for
        training/validation
    sample_weight (1D numpy array): of len(y) containing weights to use during
        fitting
    """
    from sklearn.pipeline import Pipeline

    rs_estimator = deepcopy(estimator)

    # create training and test folds
    X_train, y_train = X[train_indices], y[train_indices]

    if groups is not None:
        groups_train = groups[train_indices]
    else:
        groups_train = None

    # subset training and test fold sample_weight
    if sample_weight is not None:
        weights = sample_weight[train_indices]

    # specify fit_params for sample_weights if required
    if isinstance(estimator, Pipeline) and sample_weight is not None:
        fit_params = {"classifier__sample_weight": weights}
    elif not isinstance(estimator, Pipeline) and sample_weight is not None:
        fit_params = {"sample_weight": weights}
    else:
        fit_params = {}

    # fit estimator with/without groups
    if groups is not None and type(estimator).__name__ in [
        "RandomizedSearchCV",
        "GridSearchCV",
    ]:
        rs_estimator.fit(X_train, y_train, groups=groups_train, **fit_params)
    else:
        rs_estimator.fit(X_train, y_train, **fit_params)

    return rs_estimator


def cross_val_scores(
    estimator,
    X,
    y,
    groups=None,
    sample_weight=None,
    cv=3,
    scoring="accuracy",
    feature_importances=False,
    n_permutations=25,
    random_state=None,
    n_jobs=-1,
):
    """
    Stratified Kfold and GroupFold cross-validation using multiple
    scoring metrics and permutation feature importances

    Args
    ----
    estimator (object): Scikit learn estimator
    X, y: 2D and 1D numpy array of training data and labels
    groups (1D numpy array): group labels
    sample_weight (1D numpy array[n_samples,]): sample weights per sample
    cv (integer or object): Number of cross-validation folds or
        sklearn.model_selection object
    scoring (list): List of performance metrics to use
    feature_importances (boolean): option to perform permutation-based importances
    n_permutations (integer): Number of permutations during feature importance
    random_state (float): Seed to pass to the random number generator

    Returns
    -------
    scores (dict): Containing lists of scores per cross-validation fold
    byclass_scores (dict): Containing scores per class
    fimp (2D numpy array): permutation feature importances per feature
    clf_resamples (list): List of fitted estimators
    predictions (2d numpy array): with y_true, y_pred, fold
    """

    from sklearn import metrics
    from sklearn.model_selection import StratifiedKFold
    from joblib import Parallel, delayed

    # first unwrap the estimator from any potential pipelines or gridsearchCV
    if type(estimator).__name__ == "Pipeline":
        clf_type = estimator.named_steps["classifier"]
    else:
        clf_type = estimator

    if (
        type(clf_type).__name__ == "GridSearchCV"
        or type(clf_type).__name__ == "RandomizedSearchCV"
    ):
        clf_type = clf_type.best_estimator_

    # check name against already multithreaded classifiers
    if type(clf_type).__name__ in [
        "RandomForestClassifier",
        "RandomForestRegressor",
        "ExtraTreesClassifier",
        "ExtraTreesRegressor",
        "KNeighborsClassifier",
    ]:
        n_jobs = 1

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
    scores = {key: [] for key, value in scores.items()}
    scoring_methods = {
        "accuracy": metrics.accuracy_score,
        "balanced_accuracy": metrics.recall_score,
        "average_precision": metrics.average_precision_score,
        "brier_loss": metrics.brier_score_loss,
        "kappa": metrics.cohen_kappa_score,
        "f1": metrics.f1_score,
        "fbeta": metrics.fbeta_score,
        "hamming_loss": metrics.hamming_loss,
        "jaccard_similarity": metrics.jaccard_score,
        "log_loss": metrics.log_loss,
        "matthews_corrcoef": metrics.matthews_corrcoef,
        "precision": metrics.precision_score,
        "recall": metrics.recall_score,
        "specificity": specificity_score,
        "roc_auc": metrics.roc_auc_score,
        "zero_one_loss": metrics.zero_one_loss,
        "r2": metrics.r2_score,
        "explained_variance": metrics.explained_variance_score,
        "neg_mean_absolute_error": metrics.mean_absolute_error,
        "neg_mean_squared_error": metrics.mean_squared_error,
        "neg_mean_squared_log_error": metrics.mean_squared_log_error,
        "neg_median_absolute_error": metrics.median_absolute_error,
    }

    byclass_methods = {
        "f1": metrics.f1_score,
        "fbeta": metrics.fbeta_score,
        "precision": metrics.precision_score,
        "recall": metrics.recall_score,
    }

    # create dict to store byclass metrics results
    n_classes = len(np.unique(y))
    labels = np.unique(y)
    byclass_scores = dict.fromkeys(byclass_methods)
    byclass_scores = {
        key: np.zeros((0, n_classes)) for key, value in byclass_scores.items()
    }

    # remove any byclass_scorers that are not in the scoring list
    byclass_scores = {
        key: value for key, value in byclass_scores.items() if key in scores
    }

    # check if remaining scorers are valid sklearn metrics
    for i in scores.keys():
        try:
            list(scoring_methods.keys()).index(i)
        except:
            gs.fatal(
                (
                    "Scoring ",
                    i,
                    " is not a valid scoring method",
                    os.linesep,
                    "Valid methods are: ",
                    scoring_methods.keys(),
                )
            )

    # set averaging type for global binary or multiclass scores
    if len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
        average = "binary"
    else:
        average = "macro"

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
        delayed(__parallel_fit)(clf, X, y, groups, train_indices, sample_weight)
        for train_indices in trains
    )

    # -------------------------------------------------------------------------
    # loop through each fold and calculate performance metrics
    # -------------------------------------------------------------------------

    # store predictions and indices
    predictions = np.zeros((len(y), 3))  # y_true, y_pred, fold

    fold = 0
    for train_indices, test_indices in zip(trains, tests):

        # create training and test folds
        X_test, y_test = X[test_indices], y[test_indices]

        # prediction of test fold
        y_pred = clf_resamples[fold].predict(X_test)
        predictions[test_indices, 0] = y_test
        predictions[test_indices, 1] = y_pred
        predictions[test_indices, 2] = fold

        # calculate global performance metrics
        for m in scores.keys():
            # metrics that require probabilties
            if m == "brier_loss" or m == "roc_auc":
                y_prob = clf_resamples[fold].predict_proba(X_test)[:, 1]
                scores[m] = np.append(scores[m], scoring_methods[m](y_test, y_prob))

            # metrics that have no averaging for multiclass
            elif (
                m == "kappa"
                or m == "specificity"
                or m == "accuracy"
                or m == "hamming_loss"
                or m == "jaccard_similarity"
                or m == "log_loss"
                or m == "zero_one_loss"
                or m == "matthews_corrcoef"
                or m == "r2"
                or m == "explained_variance"
                or m == "neg_mean_absolute_error"
                or m == "neg_mean_squared_error"
                or m == "neg_mean_squared_log_error"
                or m == "neg_median_absolute_error"
            ):
                scores[m] = np.append(scores[m], scoring_methods[m](y_test, y_pred))

            # balanced accuracy
            elif m == "balanced_accuracy":
                scores[m] = np.append(
                    scores[m], scoring_methods[m](y_test, y_pred, average="macro")
                )

            # metrics that have averaging for multiclass
            else:
                scores[m] = np.append(
                    scores[m], scoring_methods[m](y_test, y_pred, average=average)
                )

        # calculate per-class performance metrics
        for key in byclass_scores.keys():
            byclass_scores[key] = np.vstack(
                (
                    byclass_scores[key],
                    byclass_methods[key](y_test, y_pred, labels=labels, average=None),
                )
            )

        # feature importances using permutation
        if feature_importances is True:
            fimp[fold, :] = varimp_permutation(
                clf_resamples[fold],
                X_test,
                y_test,
                n_permutations,
                scoring_methods[scoring[0]],
                n_jobs,
                random_state,
            )
        fold += 1

    return (scores, byclass_scores, fimp, clf_resamples, predictions)


tmp_rast = []


def cleanup():
    for rast in tmp_rast:
        gs.run_command("g.remove", name=rast, type="raster", flags="f", quiet=True)


def warn(*args, **kwargs):
    pass


import warnings

warnings.warn = warn


def main():
    try:
        import joblib
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import (
            GridSearchCV,
            GroupShuffleSplit,
            ShuffleSplit,
            StratifiedKFold,
            GroupKFold,
            KFold,
        )
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.pipeline import Pipeline
        from sklearn.utils import shuffle
        from sklearn import metrics
        from sklearn.metrics import make_scorer
    except:
        gs.fatal("Package python3-scikit-learn 0.18 or newer is not installed")

    try:
        import pandas as pd
    except:
        gs.fatal("Pandas is not installed ")

    # required gui section
    group = options["group"]
    trainingmap = options["trainingmap"]
    trainingpoints = options["trainingpoints"]
    field = options["field"]
    output = options["output"]

    # classifier gui section
    classifier = options["classifier"]
    grid_search = options["grid_search"]
    hyperparams = {
        "C": options["c"],
        "min_samples_split": options["min_samples_split"],
        "min_samples_leaf": options["min_samples_leaf"],
        "n_estimators": options["n_estimators"],
        "learning_rate": options["learning_rate"],
        "subsample": options["subsample"],
        "max_depth": options["max_depth"],
        "max_features": options["max_features"],
        "max_degree": options["max_degree"],
        "n_neighbors": options["n_neighbors"],
        "weights": options["weights"],
    }

    # cross validation
    cv = int(options["cv"])
    cvtype = options["cvtype"]
    group_raster = options["group_raster"]
    n_partitions = int(options["n_partitions"])
    tune_only = flags["t"]
    predict_resamples = flags["r"]
    importances = flags["f"]
    n_permutations = int(options["n_permutations"])
    errors_file = options["errors_file"]
    preds_file = options["preds_file"]
    fimp_file = options["fimp_file"]
    param_file = options["param_file"]

    # general options
    norm_data = flags["s"]
    categorymaps = options["categorymaps"]
    model_only = flags["m"]
    probability = flags["p"]
    prob_only = flags["z"]
    random_state = int(options["random_state"])
    model_save = options["save_model"]
    model_load = options["load_model"]
    load_training = options["load_training"]
    save_training = options["save_training"]
    indexes = options["indexes"]
    rowincr = int(options["rowincr"])
    n_jobs = int(options["n_jobs"])
    lowmem = flags["l"]
    balance = flags["b"]

    # fetch individual raster names from group
    maplist = gs.read_command("i.group", group=group, flags="g").split(os.linesep)[:-1]
    # map_names = [i.split('@')[0] for i in maplist]

    # extract indices of category maps
    if categorymaps.strip() == "":
        categorymaps = None
    else:
        # split string into list
        if "," in categorymaps is False:
            categorymaps = [categorymaps]
        else:
            categorymaps = categorymaps.split(",")

        cat_indexes = []

        # check that each category map is also in the imagery group
        for cat in categorymaps:
            try:
                cat_indexes.append(maplist.index(cat))
            except:
                gs.fatal("Category map {0} not in the imagery group".format(cat))
        categorymaps = cat_indexes

    # convert class probability indexes to list
    if "," in indexes:
        indexes = [int(i) for i in indexes.split(",")]
    else:
        indexes = int(indexes)
    if indexes == -1:
        indexes = None

    # error checking
    # remove @ from output in case overwriting result
    if "@" in output:
        output = output.split("@")[0]

    # feature importances selected but no cross-validation scheme used
    if importances is True and cv == 1:
        gs.fatal("Feature importances require cross-validation cv > 1")

    # error file selected but no cross-validation scheme used
    if errors_file:
        if cv <= 1:
            gs.fatal(
                "Output of cross-validation global accuracy requires cross-validation cv > 1"
            )
        if not os.path.exists(os.path.dirname(errors_file)):
            gs.fatal("Directory for output file {} does not exist".format(errors_file))

    # feature importance file selected but no cross-validation scheme used
    if fimp_file:
        if cv <= 1:
            gs.fatal("Output of feature importance requires cross-validation cv > 1")
        if not os.path.exists(os.path.dirname(fimp_file)):
            gs.fatal("Directory for output file {} does not exist".format(fimp_file))

    # predictions file selected but no cross-validation scheme used
    if preds_file:
        if cv <= 1:
            gs.fatal(
                "Output of cross-validation predictions requires cross-validation cv > 1"
            )
        if not os.path.exists(os.path.dirname(preds_file)):
            gs.fatal("Directory for output file {} does not exist".format(preds_file))

    # output map has not been entered and model_only is not set to True
    if output == "" and model_only is not True:
        gs.fatal("No output map specified")

    # perform prediction only for class probabilities but probability flag
    # is not set to True
    if prob_only is True:
        probability = True

    # check for field attribute if trainingpoints are used
    if trainingpoints != "" and field == "":
        gs.fatal("No attribute column specified for training points")

    # check that valid combination of training data input is present
    if (
        trainingpoints == ""
        and trainingmap == ""
        and load_training == ""
        and model_load == ""
    ):
        gs.fatal("No training vector, raster or tabular data is present")

    # make dicts for hyperparameters, datatypes and parameters for tuning
    hyperparams_type = dict.fromkeys(hyperparams, int)
    hyperparams_type["C"] = float
    hyperparams_type["learning_rate"] = float
    hyperparams_type["subsample"] = float
    hyperparams_type["weights"] = str
    param_grid = deepcopy(hyperparams_type)
    param_grid = dict.fromkeys(param_grid, None)

    for key, val in hyperparams.items():
        # split any comma separated strings and add them to the param_grid
        if "," in val:
            param_grid[key] = [
                hyperparams_type[key](i) for i in val.split(",")
            ]  # add all vals to param_grid
            hyperparams[key] = [hyperparams_type[key](i) for i in val.split(",")][
                0
            ]  # use first param for default
        # else convert the single strings to int or float
        else:
            hyperparams[key] = hyperparams_type[key](val)

    if hyperparams["max_depth"] == 0:
        hyperparams["max_depth"] = None
    if hyperparams["max_features"] == 0:
        hyperparams["max_features"] = "auto"
    param_grid = {k: v for k, v in param_grid.items() if v is not None}

    # retrieve sklearn classifier object and parameters
    clf, mode = model_classifiers(
        classifier, random_state, n_jobs, hyperparams, balance
    )

    # remove dict keys that are incompatible for the selected classifier
    clf_params = clf.get_params()
    param_grid = {key: value for key, value in param_grid.items() if key in clf_params}

    # scoring metrics
    if mode == "classification":
        scoring = [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "kappa",
            "balanced_accuracy",
        ]
        search_scorer = make_scorer(metrics.matthews_corrcoef)
    else:
        scoring = [
            "r2",
            "explained_variance",
            "neg_mean_absolute_error",
            "neg_mean_squared_error",
            "neg_mean_squared_log_error",
            "neg_median_absolute_error",
        ]
        search_scorer = "r2"

    # -------------------------------------------------------------------------
    # Extract training data
    # -------------------------------------------------------------------------

    if model_load == "":

        # Sample training data and group id
        if load_training != "":
            X, y, group_id, sample_coords = load_training_data(load_training)
        else:
            gs.message("Extracting training data")

            # generate spatial clump/patch partitions
            # clump the labelled pixel raster and set the group_raster
            # to the clumped raster
            if trainingmap != "" and cvtype == "clumped" and group_raster == "":
                clumped_trainingmap = "tmp_clumped_trainingmap"
                tmp_rast.append(clumped_trainingmap)
                r.clump(
                    input=trainingmap,
                    output=clumped_trainingmap,
                    overwrite=True,
                    quiet=True,
                )
                group_raster = clumped_trainingmap
            elif trainingmap == "" and cvtype == "clumped":
                gs.fatal(
                    "Cross-validation using clumped training areas ",
                    "requires raster-based training areas",
                )

            # append spatial clumps or group raster to the predictors
            if group_raster != "":
                maplist2 = deepcopy(maplist)
                maplist2.append(group_raster)
            else:
                maplist2 = maplist

            # extract training data
            if trainingmap != "":
                X, y, sample_coords = extract_pixels(
                    response=trainingmap, predictors=maplist2, lowmem=lowmem, na_rm=True
                )
            elif trainingpoints != "":
                X, y, sample_coords = extract_points(
                    trainingpoints, maplist2, field, na_rm=True
                )
            group_id = None

            if len(y) < 1 or X.shape[0] < 1:
                gs.fatal(
                    "There are too few training features to perform classification"
                )

            # take group id from last column and remove from predictors
            if group_raster != "":
                group_id = X[:, -1]
                X = np.delete(X, -1, axis=1)

            if cvtype == "kmeans":
                clusters = KMeans(
                    n_clusters=n_partitions, random_state=random_state, n_jobs=n_jobs
                )
                clusters.fit(sample_coords)
                group_id = clusters.labels_

            # check for labelled pixels and training data
            if y.shape[0] == 0 or X.shape[0] == 0:
                gs.fatal(
                    "No training pixels or pixels in imagery group "
                    "...check computational region"
                )

            # shuffle data
            if group_id is None:
                X, y, sample_coords = shuffle(
                    X, y, sample_coords, random_state=random_state
                )
            if group_id is not None:
                X, y, sample_coords, group_id = shuffle(
                    X, y, sample_coords, group_id, random_state=random_state
                )

            # optionally save extracted data to .csv file
            if save_training != "":
                save_training_data(X, y, group_id, sample_coords, save_training)

        # ---------------------------------------------------------------------
        # define the inner search resampling method
        # ---------------------------------------------------------------------

        if any(param_grid) is True and cv == 1 and grid_search == "cross-validation":
            gs.fatal("Hyperparameter search using cross validation requires cv > 1")

        # define inner resampling using cross-validation method
        elif any(param_grid) is True and grid_search == "cross-validation":
            if group_id is None and mode == "classification":
                inner = StratifiedKFold(n_splits=cv, random_state=random_state)
            elif group_id is None and mode == "regression":
                inner = KFold(n_splits=cv, random_state=random_state)
            else:
                inner = GroupKFold(n_splits=cv)

        # define inner resampling using the holdout method
        elif any(param_grid) is True and grid_search == "holdout":
            if group_id is None:
                inner = ShuffleSplit(
                    n_splits=1, test_size=0.33, random_state=random_state
                )
            else:
                inner = GroupShuffleSplit(
                    n_splits=1, test_size=0.33, random_state=random_state
                )
        else:
            inner = None

        # ---------------------------------------------------------------------
        # define the outer search resampling method
        # ---------------------------------------------------------------------
        if cv > 1:
            if group_id is None and mode == "classification":
                outer = StratifiedKFold(n_splits=cv, random_state=random_state)
            elif group_id is None and mode == "regression":
                outer = KFold(n_splits=cv, random_state=random_state)
            else:
                outer = GroupKFold(n_splits=cv)

        # ---------------------------------------------------------------------
        # define sample weights for gradient boosting classifiers
        # ---------------------------------------------------------------------

        # classifiers that take sample_weights
        if (
            balance is True
            and mode == "classification"
            and classifier in ("GradientBoostingClassifier", "GaussianNB")
        ):
            from sklearn.utils import compute_class_weight

            class_weights = compute_class_weight(
                class_weight="balanced", classes=(y), y=y
            )
        else:
            class_weights = None

        # ---------------------------------------------------------------------
        # define the preprocessing pipeline
        # ---------------------------------------------------------------------
        # standardization
        if norm_data is True and categorymaps is None:
            clf = Pipeline([("scaling", StandardScaler()), ("classifier", clf)])

        # onehot encoding
        if categorymaps is not None and norm_data is False:
            enc = OneHotEncoder(categorical_features=categorymaps)
            enc.fit(X)
            clf = Pipeline(
                [
                    (
                        "onehot",
                        OneHotEncoder(
                            categorical_features=categorymaps,
                            n_values=enc.n_values_,
                            handle_unknown="ignore",
                            sparse=False,
                        ),
                    ),  # dense because not all clf can use sparse
                    ("classifier", clf),
                ]
            )

        # standardization and onehot encoding
        if norm_data is True and categorymaps is not None:
            enc = OneHotEncoder(categorical_features=categorymaps)
            enc.fit(X)
            clf = Pipeline(
                [
                    (
                        "onehot",
                        OneHotEncoder(
                            categorical_features=categorymaps,
                            n_values=enc.n_values_,
                            handle_unknown="ignore",
                            sparse=False,
                        ),
                    ),
                    ("scaling", StandardScaler()),
                    ("classifier", clf),
                ]
            )

        # ---------------------------------------------------------------------
        # create the hyperparameter grid search method
        # ---------------------------------------------------------------------

        # check if dict contains and keys - perform GridSearchCV
        if any(param_grid) is True:

            # if Pipeline then change param_grid keys to named_step
            if isinstance(clf, Pipeline):
                for key in param_grid.keys():
                    newkey = "classifier__" + key
                    param_grid[newkey] = param_grid.pop(key)

            # create grid search method
            clf = GridSearchCV(
                estimator=clf,
                param_grid=param_grid,
                scoring=search_scorer,
                n_jobs=n_jobs,
                cv=inner,
            )

        # ---------------------------------------------------------------------
        # classifier training
        # ---------------------------------------------------------------------

        gs.message(os.linesep)
        gs.message(("Fitting model using " + classifier))

        # fitting ensuring that all options are passed
        if (
            classifier in ("GradientBoostingClassifier", "GausianNB")
            and balance is True
        ):
            if isinstance(clf, Pipeline):
                fit_params = {"classifier__sample_weight": class_weights}
            else:
                fit_params = {"sample_weight": class_weights}
        else:
            fit_params = {}

        if isinstance(inner, (GroupKFold, GroupShuffleSplit)):
            clf.fit(X, y, groups=group_id, **fit_params)
        else:
            clf.fit(X, y, **fit_params)

        # message best hyperparameter setup and optionally save using pandas
        if any(param_grid) is True:
            gs.message(os.linesep)
            gs.message("Best parameters:")
            gs.message(str(clf.best_params_))
            if param_file != "":
                param_df = pd.DataFrame(clf.cv_results_)
                param_df.to_csv(param_file)

        # ---------------------------------------------------------------------
        # cross-validation
        # ---------------------------------------------------------------------

        # If cv > 1 then use cross-validation to generate performance measures
        if cv > 1 and tune_only is not True:
            if (
                mode == "classification"
                and cv > np.histogram(y, bins=np.unique(y))[0].min()
            ):
                gs.message(os.linesep)
                gs.message(
                    "Number of cv folds is greater than number of "
                    "samples in some classes. Cross-validation is being"
                    " skipped"
                )
            else:
                gs.message(os.linesep)
                gs.message("Cross validation global performance measures......:")

                # add auc and mcc as scorer if classification is binary
                if (
                    mode == "classification"
                    and len(np.unique(y)) == 2
                    and all([0, 1] == np.unique(y))
                ):
                    scoring.append("roc_auc")
                    scoring.append("matthews_corrcoef")

                # perform the cross-validatation
                scores, cscores, fimp, models, preds = cross_val_scores(
                    clf,
                    X,
                    y,
                    group_id,
                    class_weights,
                    outer,
                    scoring,
                    importances,
                    n_permutations,
                    random_state,
                    n_jobs,
                )

                # from sklearn.model_selection import cross_validate
                # scores = cross_validate(clf, X, y, group_id, scoring, outer, n_jobs, fit_params=fit_params)
                # test_scoring = ['test_' + i for i in scoring]
                # gs.message(os.linesep)
                # gs.message(('Metric \t Mean \t Error'))
                # for sc in test_scoring:
                #     gs.message(sc + '\t' + str(scores[sc].mean()) + '\t' + str(scores[sc].std()))

                preds = np.hstack((preds, sample_coords))

                for method, val in scores.items():
                    gs.message(
                        method + ":\t%0.3f\t+/-SD\t%0.3f" % (val.mean(), val.std())
                    )

                # individual class scores
                if mode == "classification" and len(np.unique(y)) != 2:
                    gs.message(os.linesep)
                    gs.message("Cross validation class performance measures......:")
                    gs.message("Class \t" + "\t".join(map(str, np.unique(y))))

                    for method, val in cscores.items():
                        mat_cscores = np.matrix(val)
                        gs.message(
                            method
                            + ":\t"
                            + "\t".join(
                                map(str, np.round(mat_cscores.mean(axis=0), 2)[0])
                            )
                        )
                        gs.message(
                            method
                            + " std:\t"
                            + "\t".join(
                                map(str, np.round(mat_cscores.std(axis=0), 2)[0])
                            )
                        )

                # write cross-validation results for csv file
                if errors_file != "":
                    errors = pd.DataFrame(scores)
                    errors.to_csv(errors_file, mode="w")

                # write cross-validation predictions to csv file
                if preds_file != "":
                    preds = pd.DataFrame(preds)
                    preds.columns = ["y_true", "y_pred", "fold", "x", "y"]
                    preds.to_csv(preds_file, mode="w")
                    text_file = open(preds_file + "t", "w")
                    text_file.write('"Integer","Real","Real","integer","Real","Real"')
                    text_file.close()

                # feature importances
                if importances is True:
                    gs.message(os.linesep)
                    gs.message("Feature importances")
                    gs.message("id" + "\t" + "Raster" + "\t" + "Importance")

                    # mean of cross-validation feature importances
                    for i in range(len(fimp.mean(axis=0))):
                        gs.message(
                            str(i)
                            + "\t"
                            + maplist[i]
                            + "\t"
                            + str(round(fimp.mean(axis=0)[i], 4))
                        )

                    if fimp_file != "":
                        np.savetxt(
                            fname=fimp_file,
                            X=fimp,
                            delimiter=",",
                            header=",".join(maplist),
                            comments="",
                        )
    else:
        # load a previously fitted train object
        if model_load != "":
            # load a previously fitted model
            X, y, sample_coords, group_id, clf = joblib.load(model_load)
            clf.fit(X, y)

    # Optionally save the fitted model
    if model_save != "":
        joblib.dump((X, y, sample_coords, group_id, clf), model_save)

    # -------------------------------------------------------------------------
    # prediction on grass imagery group
    # -------------------------------------------------------------------------

    if model_only is not True:
        gs.message(os.linesep)

        # predict classification/regression raster
        if prob_only is False:
            gs.message("Predicting classification/regression raster...")
            predict(
                estimator=clf,
                predictors=maplist,
                output=output,
                predict_type="raw",
                overwrite=gs.overwrite(),
                rowincr=rowincr,
                n_jobs=n_jobs,
            )

            if predict_resamples is True:
                for i in range(cv):
                    resample_name = output + "_Resample" + str(i)
                    predict(
                        estimator=models[i],
                        predictors=maplist,
                        output=resample_name,
                        predict_type="raw",
                        overwrite=gs.overwrite(),
                        rowincr=rowincr,
                        n_jobs=n_jobs,
                    )

        # predict class probabilities
        if probability is True:
            gs.message("Predicting class probabilities...")
            predict(
                estimator=clf,
                predictors=maplist,
                output=output,
                predict_type="prob",
                index=indexes,
                class_labels=np.unique(y),
                overwrite=gs.overwrite(),
                rowincr=rowincr,
                n_jobs=n_jobs,
            )

            if predict_resamples is True:
                for i in range(cv):
                    resample_name = output + "_Resample" + str(i)
                    predict(
                        estimator=models[i],
                        predictors=maplist,
                        output=resample_name,
                        predict_type="prob",
                        class_labels=np.unique(y),
                        index=indexes,
                        overwrite=gs.overwrite(),
                        rowincr=rowincr,
                        n_jobs=n_jobs,
                    )
    else:
        gs.message("Model built and now exiting")


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
