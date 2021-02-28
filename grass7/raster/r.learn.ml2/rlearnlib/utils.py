#!/usr/bin/env python
# -- coding: utf-8 --

"""The utils module contains functions to assist
with passing pre-defined scikit learn classifiers
and other utilities for loading/saving training data."""

import numpy as np
from grass.pygrass.utils import get_mapset_raster


def get_fullname(name):
    """
    Return a fullname for a raster if only a string with the mapname
    is provided.

    Parameters
    ----------
    name : str
        Name of a GRASS map

    Returns
    -------
    name : str
        Name of a GRASS map with the mapset appended as name@mapset is the
        mapset is not explicitly provided.
    """
    if "@" not in name:
        name = "@".join([name, get_mapset_raster(name)])

    return name

def option_to_list(x, dtype=None):
    """
    Parses a multiple choice option from into a list

    Parameters
    ----------
    x : str
        String with comma-separated values

    dtype : func, optional
        Optionally pass a function to coerce with list elements into a
        specific type, e.g. int

    Returns
    -------
    x : list
        List of parsed values
    """

    if x.strip() == "":
        x = None
    elif "," in x is False:
        x = [x]
    else:
        x = x.split(",")

    if dtype:
        x = [dtype(i) for i in x]

    if x is not None:

        if len(x) == 1 and x[0] == -1:
            x = None

    return x


def predefined_estimators(estimator, random_state, n_jobs, p):
    """
    Provides the classifiers and parameters using by the module

    Parameters
    -----------
    estimator : str
        Name of scikit learn estimator.

    random_state : Any number
        Seed to use in randomized components.

    n_jobs : int
        Number of processing cores to use.

    p : dict
        Classifier setttings (keys) and values.

    Returns
    -------
    clf : object
        Scikit-learn classifier object

    mode : str
        Flag to indicate whether classifier performs classification or
        regression.
    """
    try:
        from sklearn.experimental import enable_hist_gradient_boosting
    except ImportError:
        pass

    from sklearn.linear_model import (
        LogisticRegression,
        LinearRegression,
        SGDRegressor,
        SGDClassifier,
    )
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
    from sklearn.ensemble import (GradientBoostingClassifier,
                                  GradientBoostingRegressor)
    from sklearn.svm import SVC, SVR
    from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
    from sklearn.neural_network import MLPClassifier, MLPRegressor

    estimators = {
        "SVC": SVC(C=p["C"], probability=True, random_state=random_state),
        "SVR": SVR(C=p["C"], epsilon=p["epsilon"]),
        "LogisticRegression": LogisticRegression(
            C=p["C"],
            solver="liblinear",
            random_state=random_state,
            multi_class="auto",
            n_jobs=1,
            fit_intercept=True,
        ),
        "LinearRegression": LinearRegression(
            n_jobs=n_jobs, fit_intercept=True),
        "SGDClassifier": SGDClassifier(
            penalty=p["penalty"],
            alpha=p["alpha"],
            l1_ratio=p["l1_ratio"],
            n_jobs=n_jobs,
            random_state=random_state,
        ),
        "SGDRegressor": SGDRegressor(
            penalty=p["penalty"],
            alpha=p["alpha"],
            l1_ratio=p["l1_ratio"],
            random_state=random_state,
        ),
        "DecisionTreeClassifier": DecisionTreeClassifier(
            max_depth=p["max_depth"],
            max_features=p["max_features"],
            min_samples_leaf=p["min_samples_leaf"],
            random_state=random_state,
        ),
        "DecisionTreeRegressor": DecisionTreeRegressor(
            max_features=p["max_features"],
            min_samples_leaf=p["min_samples_leaf"],
            random_state=random_state,
        ),
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=p["n_estimators"],
            max_features=p["max_features"],
            min_samples_leaf=p["min_samples_leaf"],
            random_state=random_state,
            n_jobs=n_jobs,
            oob_score=True,
        ),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=p["n_estimators"],
            max_features=p["max_features"],
            min_samples_leaf=p["min_samples_leaf"],
            random_state=random_state,
            n_jobs=n_jobs,
            oob_score=True,
        ),
        "ExtraTreesClassifier": ExtraTreesClassifier(
            n_estimators=p["n_estimators"],
            max_features=p["max_features"],
            min_samples_leaf=p["min_samples_leaf"],
            random_state=random_state,
            n_jobs=n_jobs,
            bootstrap=True,
            oob_score=True,
        ),
        "ExtraTreesRegressor": ExtraTreesRegressor(
            n_estimators=p["n_estimators"],
            max_features=p["max_features"],
            min_samples_leaf=p["min_samples_leaf"],
            random_state=random_state,
            bootstrap=True,
            n_jobs=n_jobs,
            oob_score=True,
        ),
        "GradientBoostingClassifier": GradientBoostingClassifier(
            learning_rate=p["learning_rate"],
            n_estimators=p["n_estimators"],
            max_depth=p["max_depth"],
            min_samples_leaf=p["min_samples_leaf"],
            subsample=p["subsample"],
            max_features=p["max_features"],
            random_state=random_state,
        ),
        "GradientBoostingRegressor": GradientBoostingRegressor(
            learning_rate=p["learning_rate"],
            n_estimators=p["n_estimators"],
            max_depth=p["max_depth"],
            min_samples_leaf=p["min_samples_leaf"],
            subsample=p["subsample"],
            max_features=p["max_features"],
            random_state=random_state,
        ),
        "HistGradientBoostingClassifier": GradientBoostingClassifier(
            learning_rate=p["learning_rate"],
            n_estimators=p["n_estimators"],
            max_depth=p["max_depth"],
            min_samples_leaf=p["min_samples_leaf"],
            subsample=p["subsample"],
            max_features=p["max_features"],
            random_state=random_state,
        ),
        "HistGradientBoostingRegressor": GradientBoostingRegressor(
            learning_rate=p["learning_rate"],
            n_estimators=p["n_estimators"],
            max_depth=p["max_depth"],
            min_samples_leaf=p["min_samples_leaf"],
            subsample=p["subsample"],
            max_features=p["max_features"],
            random_state=random_state,
        ),
        "MLPClassifier": MLPClassifier(
            hidden_layer_sizes=p["hidden_layer_sizes"],
            alpha=p["alpha"],
            random_state=random_state,
        ),
        "MLPRegressor": MLPRegressor(
            hidden_layer_sizes=p["hidden_layer_sizes"],
            alpha=p["alpha"],
            random_state=random_state,
        ),
        "GaussianNB": GaussianNB(),
        "LinearDiscriminantAnalysis": LinearDiscriminantAnalysis(),
        "QuadraticDiscriminantAnalysis": QuadraticDiscriminantAnalysis(),
        "KNeighborsClassifier": KNeighborsClassifier(
            n_neighbors=p["n_neighbors"], weights=p["weights"], n_jobs=n_jobs
        ),
        "KNeighborsRegressor": KNeighborsRegressor(
            n_neighbors=p["n_neighbors"], weights=p["weights"], n_jobs=n_jobs
        ),
    }

    # define classifier
    model = estimators[estimator]

    # classification or regression
    if (
        estimator == "LogisticRegression"
        or estimator == "SGDClassifier"
        or estimator == "MLPClassifier"
        or estimator == "DecisionTreeClassifier"
        or estimator == "RandomForestClassifier"
        or estimator == "ExtraTreesClassifier"
        or estimator == "GradientBoostingClassifier"
        or estimator == "HistGradientBoostingClassifier"
        or estimator == "GaussianNB"
        or estimator == "LinearDiscriminantAnalysis"
        or estimator == "QuadraticDiscriminantAnalysis"
        or estimator == "SVC"
        or estimator == "KNeighborsClassifier"
    ):
        mode = "classification"
    else:
        mode = "regression"

    return (model, mode)


def check_class_weights():
    """
    Returns a list of scikit-learn models that support class weights
    in their fit methods
    """

    support = [
        "LogisticRegression",
        "SGDClassifier",
        "GaussianNB",
        "DecisionTreeClassifier",
        "RandomForestClassifier",
        "ExtraTreesClassifier",
        "GradientBoostingClassifier",
        "SVC",
    ]

    return support


def scoring_metrics(mode):
    """
    Simple helper function to return a suite of scoring methods depending on
    if classification or regression is required

    Parameters
    ----------
    mode : str
        'classification' or 'regression'

    Returns
    -------
    scoring : list
        List of sklearn scoring metrics

    search_scorer : func, or str
        Scoring metric to use for hyperparameter tuning
    """

    from sklearn import metrics
    from sklearn.metrics import make_scorer

    if mode == "classification":
        scoring = {
            "accuracy": metrics.accuracy_score,
            "balanced_accuracy": metrics.balanced_accuracy_score,
            "matthews_correlation_coefficient": metrics.matthews_corrcoef,
            "kappa": metrics.cohen_kappa_score,
        }

        search_scorer = make_scorer(metrics.matthews_corrcoef)

    else:
        scoring = {
            "r2": metrics.r2_score,
            "explained_variance": metrics.explained_variance_score,
            "mean_absolute_error": metrics.mean_absolute_error,
            "mean_squared_error": metrics.mean_squared_error,
        }

        search_scorer = make_scorer(metrics.r2_score)

    return scoring, search_scorer


def save_training_data(file, X, y, cat, class_labels=None, groups=None,
                       names=None):
    """
    Saves any extracted training data to a csv file.

    Training data is saved in the following format:
        col (0..n) : feature data
        col (n) : response data
        col (n+1): grass cat value
        col (n+2): group idx

    Parameters
    ----------
    file : str
        Path to a csv file to save data to

    X : ndarray
        2d numpy array containing predictor values

    y : ndarray
        1d numpy array containing labels

    cat : ndarray
        1d numpy array of GRASS key column

    class_labels : dict
        Dict of class index values as keys, and class labels as values

    groups :ndarray (opt)
        1d numpy array containing group labels

    names : list (opt)
        Optionally pass names of features to use as a heading
    """
    import pandas as pd

    if isinstance(names, str):
        names = list(names)

    if names is None:
        names = ["feature" + str(i) for i in range(X.shape[1])]

    # if there are no group labels, create a nan filled array
    if groups is None:
        groups = np.empty((y.shape[0]))
        groups[:] = np.nan

    if class_labels:
        labels_arr = np.asarray(
            [class_labels[yi] for yi in y]).astype(np.object)
    else:
        labels_arr = np.empty((y.shape[0]))
        labels_arr[:] = np.nan

    df = pd.DataFrame(X, columns=names)
    df["response"] = y
    df["cat"] = cat
    df["class_labels"] = labels_arr
    df["groups"] = groups

    df.to_csv(file, index=False)


def load_training_data(file):
    """
    Loads training data and labels from a csv file

    Parameters
    ----------
    file (string): Path to a csv file to save data to

    Returns
    -------
    X (2d numpy array): Numpy array containing predictor values
    y (1d numpy array): Numpy array containing labels
    cat (1d numpy array): Numpy array of GRASS key column
    class_labels (1d numpy array): Numpy array of labels
    groups (1d numpy array): Numpy array of group labels, or None
    """

    import pandas as pd

    training_data = pd.read_csv(file)

    groups = training_data.groups.values

    if bool(pd.isna(groups).all()) is True:
        groups = None

    class_labels = training_data.class_labels.values

    if bool(pd.isna(class_labels).all()) is True:
        class_labels = None

    cat = training_data.cat.values.astype(np.int64)
    y = training_data.response.values
    X = training_data.drop(
        columns=["groups", "class_labels", "cat", "response"]).values

    return X, y, cat, class_labels, groups
