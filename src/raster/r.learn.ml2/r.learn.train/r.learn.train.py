#!/usr/bin/env python3

############################################################################
# MODULE:        r.learn.train
# AUTHOR:        Steven Pawley
# PURPOSE:       Supervised classification and regression of GRASS rasters
#                using the python scikit-learn package
#
# COPYRIGHT: (c) 2017-2020 Steven Pawley, and the GRASS Development Team
#                This program is free software under the GNU General Public
#                for details.
#
#############################################################################
# July, 2017. Jaan Janno, Mait Lang. Bugfixes concerning crossvalidation failure
# when class numeric ID-s were not continous increasing +1 each.
# Bugfix for processing index list of nominal layers.

# %module
# % description: Supervised classification and regression of GRASS rasters using the python scikit-learn package.
# % keyword: raster
# % keyword: classification
# % keyword: regression
# % keyword: machine learning
# % keyword: scikit-learn
# % keyword: training
# % keyword: parallel
# %end

# %option G_OPT_I_GROUP
# % key: group
# % label: Group of raster layers to be classified
# % description: GRASS imagery group of raster maps representing predictor variables to be used in the machine learning model
# % required: yes
# % multiple: no
# %end

# %option G_OPT_R_INPUT
# % key: training_map
# % label: Labelled pixels
# % description: Raster map with labelled pixels for training
# % required: no
# % guisection: Required
# %end

# %option G_OPT_V_INPUT
# % key: training_points
# % label: Vector map with training samples
# % description: Vector points map where each point is used as training sample
# % required: no
# % guisection: Required
# %end

# %option G_OPT_DB_COLUMN
# % key: field
# % label: Response attribute column
# % description: Name of attribute column in training_points table containing response values
# % required: no
# % guisection: Required
# %end

# %option G_OPT_F_OUTPUT
# % key: save_model
# % label: Save model to file (for compression use e.g. '.gz' extension)
# % description: Name of file to store model results using python joblib
# % required: yes
# % guisection: Required
# %end

# %option string
# % key: model_name
# % label: model_name
# % description: Supervised learning model to use
# % answer: RandomForestClassifier
# % options: LogisticRegression,LinearRegression,SGDClassifier,SGDRegressor,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,KNeighborsClassifier,KNeighborsRegressor,GaussianNB,DecisionTreeClassifier,DecisionTreeRegressor,RandomForestClassifier,RandomForestRegressor,ExtraTreesClassifier,ExtraTreesRegressor,GradientBoostingClassifier,GradientBoostingRegressor,HistGradientBoostingClassifier,HistGradientBoostingRegressor,SVC,SVR,MLPClassifier,MLPRegressor
# % guisection: Estimator settings
# % required: no
# % multiple: no
# %end

# %option string
# % key: penalty
# % label: The regularization method
# % description: The regularization method to be used for the SGDClassifier and SGDRegressor
# % answer: l2
# % options: l1,l2,elasticnet
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: alpha
# % type: double
# % label: Constant that multiplies the regularization term
# % description: Constant that multiplies the regularization term for SGDClassifier/SGDRegressor/MLPClassifier/MLPRegressor
# % answer: 0.0001
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: l1_ratio
# % type: double
# % label: The Elastic Net mixing parameter
# % description: The Elastic Net mixing parameter for SGDClassifier/SGDRegressor
# % answer: 0.15
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: c
# % type: double
# % label: Inverse of regularization strength
# % description: Inverse of regularization strength (LogisticRegression and SVC/SVR)
# % answer: 1.0
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: epsilon
# % type: double
# % label: Epsilon in the SVR model
# % description: Epsilon in the SVR model
# % answer: 0.1
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: max_features
# % type: integer
# % label: Number of features available during node splitting; zero uses estimator defaults
# % description: Number of features available during node splitting (tree-based classifiers and regressors)
# % answer:0
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: max_depth
# % type: integer
# % label: Maximum tree depth; zero uses estimator defaults
# % description: Maximum tree depth for tree-based method; zero uses estimator defaults (full-growing for Decision trees and Randomforest, 3 for GBM)
# % answer:0
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: min_samples_leaf
# % type: integer
# % label: The minimum number of samples required to form a leaf node
# % description: The minimum number of samples required to form a leaf node in tree-based estimators
# % answer: 1
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: n_estimators
# % type: integer
# % label: Number of estimators
# % description: Number of estimators (trees) in ensemble tree-based estimators
# % answer: 100
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: learning_rate
# % type: double
# % label: learning rate
# % description: learning rate (also known as shrinkage) for gradient boosting methods
# % answer: 0.1
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: subsample
# % type: double
# % label: The fraction of samples to be used for fitting
# % description: The fraction of samples to be used for fitting, controls stochastic behaviour of gradient boosting methods
# % answer: 1.0
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option
# % key: n_neighbors
# % type: integer
# % label: Number of neighbors to use
# % description: Number of neighbors to use
# % answer: 5
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option string
# % key: hidden_units
# % label: Number of neurons to use in the hidden layers
# % description: Number of neurons to use in each layer, i.e. (100;50) for two layers
# % answer: (100;100)
# % multiple: yes
# % guisection: Estimator settings
# %end

# %option string
# % key: weights
# % label: weight function
# % description: Distance weight function for k-nearest neighbours model prediction
# % answer: uniform
# % options: uniform,distance
# % multiple: yes
# % guisection: Estimator settings
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
# % label: Number of cross-validation folds
# % description: Number of cross-validation folds
# % answer: 1
# % guisection: Cross validation
# %end

# %flag
# % key: f
# % label: Compute Feature importances
# % description: Compute feature importances using permutation
# % guisection: Estimator settings
# %end

# %option G_OPT_F_OUTPUT
# % key: preds_file
# % label: Save cross-validation predictions to csv
# % description: Name of output file in which to save the cross-validation predictions
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: classif_file
# % label: Save classification report to csv
# % description: Name of output file to save the classification report
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_R_INPUT
# % key: category_maps
# % required: no
# % multiple: yes
# % label: Names of categorical rasters within the imagery group
# % description: Names of categorical rasters within the imagery group that will be one-hot encoded. Leave empty if none.
# % guisection: Optional
# %end

# %option G_OPT_F_OUTPUT
# % key: fimp_file
# % label: Save feature importances to csv
# % descriptions: Name of file to save the permutation feature importance results
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: param_file
# % label: Save hyperparameter search scores to csv
# % description: Name of file to save the hyperparameter tuning results
# % required: no
# % guisection: Cross validation
# %end

# %option
# % key: random_state
# % type: integer
# % label: Seed to use for random state
# % description: Seed to use for random state to enable reproducible results for estimators that have stochastic components
# % answer: 1
# % guisection: Optional
# %end

# %option
# % key: n_jobs
# % type: integer
# % label: Number of cores for multiprocessing
# % description: Number of cores for multiprocessing, -2 is n_cores-1
# % answer: -2
# % guisection: Optional
# %end

# %flag
# % key: s
# % label: Standardization preprocessing
# % description: Standardize feature variables (convert values the get zero mean and unit variance)
# % guisection: Optional
# %end

# %flag
# % key: b
# % label: Balance training data using class weights
# % description: Automatically adjust weights inversely proportional to class frequencies
# % guisection: Optional
# %end

# %option G_OPT_F_OUTPUT
# % key: save_training
# % label: Save training data to csv
# % description: Name of output file to save training data in comma-delimited format
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_F_INPUT
# % key: load_training
# % label: Load training data from csv
# % description: Load previously extracted training data from a csv file
# % required: no
# % guisection: Optional
# %end

# %rules
# % required: training_map,training_points,load_training
# % exclusive: training_map,training_points,load_training
# % exclusive: load_training,save_training
# % requires: training_points,field
# %end

import atexit
import os
import re
import warnings
from copy import deepcopy

import grass.script as gs
import numpy as np
from grass.pygrass.raster import RasterRow

gs.utils.set_path(modulename="r.learn.ml2", dirname="rlearnlib", path="..")

tmp_rast = []


def cleanup():
    """Remove any intermediate rasters if execution fails"""
    for rast in tmp_rast:
        gs.run_command("g.remove", name=rast, type="raster", flags="f", quiet=True)


def warn(*args, **kwargs):
    """Hide warnings"""
    pass


warnings.warn = warn


def wrap_named_step(param_grid):
    """Function to rename the keys of a parameter grid dict after it is used in
    a Pipeline"""
    translate = {}

    for k, v in param_grid.items():
        newkey = "estimator__" + k
        translate[k] = newkey

    for old, new in translate.items():
        param_grid[new] = param_grid.pop(old)

    return param_grid


def process_hidden(val):
    """Process the syntax for multiple hidden layers in the
    MLPClassifier/MLPRegressor"""
    val = re.sub(r"[\(\)]", "", val)
    val = [int(i.strip()) for i in val.split(";")]
    return val


def process_param_grid(hyperparams):
    """Process the GRASS options for hyperparameters by assigning default
    parameters to the hyperparams dict, and splitting any comma-separated lists
    into the param_grid dict
    """
    hyperparams_type = dict.fromkeys(hyperparams, int)
    hyperparams_type["penalty"] = str
    hyperparams_type["alpha"] = float
    hyperparams_type["l1_ratio"] = float
    hyperparams_type["C"] = float
    hyperparams_type["epsilon"] = float
    hyperparams_type["learning_rate"] = float
    hyperparams_type["subsample"] = float
    hyperparams_type["weights"] = str
    hyperparams_type["hidden_layer_sizes"] = tuple
    param_grid = deepcopy(hyperparams_type)
    param_grid = dict.fromkeys(param_grid, None)

    for key, val in hyperparams.items():
        if "," in val:
            values = val.split(",")

            if key == "hidden_layer_sizes":
                values = [process_hidden(i) for i in values]

            param_grid[key] = [hyperparams_type[key](i) for i in values]
            hyperparams[key] = [hyperparams_type[key](i) for i in values][0]
        else:
            if key == "hidden_layer_sizes":
                hyperparams[key] = hyperparams_type[key](process_hidden(val))
            else:
                hyperparams[key] = hyperparams_type[key](val)

    if hyperparams["max_depth"] == 0:
        hyperparams["max_depth"] = None
    if hyperparams["max_features"] == 0:
        hyperparams["max_features"] = "sqrt"
    param_grid = {k: v for k, v in param_grid.items() if v is not None}

    return hyperparams, param_grid


def main():
    # Lazy import libraries
    from rlearnlib.utils import (
        predefined_estimators,
        load_training_data,
        save_training_data,
        option_to_list,
        scoring_metrics,
        check_class_weights,
    )
    from rlearnlib.raster import RasterStack

    try:
        import sklearn

        if sklearn.__version__ < "1.2.2":
            gs.fatal("Package python3-scikit-learn 1.2.2 or newer is not installed")

    except ImportError:
        gs.fatal("Package python3-scikit-learn 1.2.2 or newer is not installed")

    try:
        import pandas as pd

    except ImportError:
        gs.fatal("Package python3-pandas 0.25 or newer is not installed")

    # parser options ----------------------------------------------------------
    group = options["group"]
    training_map = options["training_map"]
    training_points = options["training_points"]
    field = options["field"]
    model_save = options["save_model"]
    model_name = options["model_name"]
    hyperparams = {
        "penalty": options["penalty"],
        "alpha": options["alpha"],
        "l1_ratio": options["l1_ratio"],
        "C": options["c"],
        "epsilon": options["epsilon"],
        "min_samples_leaf": options["min_samples_leaf"],
        "n_estimators": options["n_estimators"],
        "learning_rate": options["learning_rate"],
        "subsample": options["subsample"],
        "max_depth": options["max_depth"],
        "max_features": options["max_features"],
        "n_neighbors": options["n_neighbors"],
        "weights": options["weights"],
        "hidden_layer_sizes": options["hidden_units"],
    }
    cv = int(options["cv"])
    group_raster = options["group_raster"]
    importances = flags["f"]
    preds_file = options["preds_file"]
    classif_file = options["classif_file"]
    fimp_file = options["fimp_file"]
    param_file = options["param_file"]
    norm_data = flags["s"]
    random_state = int(options["random_state"])
    load_training = options["load_training"]
    save_training = options["save_training"]
    n_jobs = int(options["n_jobs"])
    balance = flags["b"]
    category_maps = option_to_list(options["category_maps"])

    # define estimator --------------------------------------------------------
    hyperparams, param_grid = process_param_grid(hyperparams)
    estimator, mode = predefined_estimators(
        model_name, random_state, n_jobs, hyperparams
    )

    # remove dict keys that are incompatible for the selected estimator
    estimator_params = estimator.get_params()
    param_grid = {
        key: value for key, value in param_grid.items() if key in estimator_params
    }
    scoring, search_scorer = scoring_metrics(mode)

    # checks of input options -------------------------------------------------
    if (
        mode == "classification"
        and balance is True
        and model_name not in check_class_weights()
    ):
        gs.warning(model_name + " does not support class weights")
        balance = False

    if mode == "regression" and balance is True:
        gs.warning("Balancing of class weights is only possible for classification")
        balance = False

    if classif_file:
        if cv <= 1:
            gs.fatal(
                "Output of cross-validation global accuracy requires "
                "cross-validation cv > 1"
            )

        if not os.path.exists(os.path.dirname(classif_file)):
            gs.fatal("Directory for output file {} does not exist".format(classif_file))

    # feature importance file selected but no cross-validation scheme used
    if importances:
        if sklearn.__version__ < "0.22":
            gs.fatal(
                "Feature importances calculation requires scikit-learn "
                "version >= 0.22"
            )

    if fimp_file:
        if importances is False:
            gs.fatal('Output of feature importance requires the "f" flag to be set')

        if not os.path.exists(os.path.dirname(fimp_file)):
            gs.fatal("Directory for output file {} does not exist".format(fimp_file))

    # predictions file selected but no cross-validation scheme used
    if preds_file:
        if cv <= 1:
            gs.fatal(
                "Output of cross-validation predictions requires "
                "cross-validation cv > 1"
            )

        if not os.path.exists(os.path.dirname(preds_file)):
            gs.fatal("Directory for output file {} does not exist".format(preds_file))

    # define RasterStack ------------------------------------------------------
    stack = RasterStack(group=group)

    if category_maps is not None:
        stack.categorical = category_maps

    # extract training data ---------------------------------------------------
    if load_training != "":
        gs.message("Loading training data ...")

        X, y, cat, class_labels, group_id = load_training_data(load_training)

        if class_labels is not None:
            a = pd.DataFrame({"response": y, "labels": class_labels})
            a = a.drop_duplicates().values
            class_labels = {k: v for (k, v) in a}

    else:
        gs.message("Extracting training data")

        if group_raster != "":
            stack.append(group_raster)

        if training_map != "":
            X, y, cat = stack.extract_pixels(training_map)
            y = y.flatten()

            with RasterRow(training_map) as src:
                if mode == "classification":
                    src_cats = {v: k for (k, v, m) in src.cats}
                    class_labels = {k: k for k in np.unique(y)}
                    class_labels.update(src_cats)
                else:
                    class_labels = None

        elif training_points != "":
            X, y, cat = stack.extract_points(training_points, field)
            y = y.flatten()

            if y.dtype in (np.object_, object):
                from sklearn.preprocessing import LabelEncoder

                le = LabelEncoder()
                y = le.fit_transform(y)
                class_labels = {k: v for (k, v) in enumerate(le.classes_)}
            else:
                class_labels = None

        # take group id from last column and remove from predictors
        if group_raster != "":
            group_id = X[:, -1]
            X = np.delete(X, -1, axis=1)
            stack.drop(group_raster)
        else:
            group_id = None

        # check for labelled pixels and training data
        if y.shape[0] == 0 or X.shape[0] == 0:
            gs.fatal(
                "No training pixels or pixels in imagery group ...check "
                "computational region"
            )

        from sklearn.utils import shuffle

        if group_id is None:
            X, y, cat = shuffle(X, y, cat, random_state=random_state)
        else:
            X, y, cat, group_id = shuffle(
                X, y, cat, group_id, random_state=random_state
            )

        if save_training != "":
            save_training_data(
                save_training, X, y, cat, class_labels, group_id, stack.names
            )

    # cross validation settings -----------------------------------------------
    # inner resampling method (cv=2)
    from sklearn.model_selection import GridSearchCV, StratifiedKFold, GroupKFold, KFold

    if any(param_grid) is True:
        if group_id is None and mode == "classification":
            inner = StratifiedKFold(n_splits=3)
        elif group_id is None and mode == "regression":
            inner = KFold(n_splits=3)
        else:
            inner = GroupKFold(n_splits=3)
    else:
        inner = None

    # outer resampling method (cv=cv)
    if cv > 1:
        if group_id is None and mode == "classification":
            outer = StratifiedKFold(n_splits=cv)
        elif group_id is None and mode == "regression":
            outer = KFold(n_splits=cv)
        else:
            outer = GroupKFold(n_splits=cv)

    # modify estimators that take sample_weights ------------------------------
    if balance is True:
        from sklearn.utils import compute_class_weight

        class_weights = compute_class_weight(class_weight="balanced", classes=(y), y=y)
        fit_params = {"sample_weight": class_weights}

    else:
        class_weights = None
        fit_params = {}

    # preprocessing -----------------------------------------------------------
    from sklearn.pipeline import Pipeline
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder

    # standardization
    if norm_data is True and category_maps is None:
        scaler = StandardScaler()
        trans = ColumnTransformer(
            remainder="passthrough",
            transformers=[("scaling", scaler, np.arange(0, stack.count))],
        )

    # one-hot encoding
    elif norm_data is False and category_maps is not None:
        enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        trans = ColumnTransformer(
            remainder="passthrough", transformers=[("onehot", enc, stack.categorical)]
        )

    # standardization and one-hot encoding
    elif norm_data is True and category_maps is not None:
        scaler = StandardScaler()
        enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        trans = ColumnTransformer(
            remainder="passthrough",
            transformers=[
                ("onehot", enc, stack.categorical),
                (
                    "scaling",
                    scaler,
                    np.setxor1d(range(stack.count), stack.categorical).astype("int"),
                ),
            ],
        )

    # combine transformers
    if norm_data is True or category_maps is not None:
        estimator = Pipeline([("preprocessing", trans), ("estimator", estimator)])
        param_grid = wrap_named_step(param_grid)
        fit_params = wrap_named_step(fit_params)

    if any(param_grid) is True:
        estimator = GridSearchCV(
            estimator=estimator,
            param_grid=param_grid,
            scoring=search_scorer,
            n_jobs=n_jobs,
            cv=inner,
        )

    # estimator training ------------------------------------------------------
    gs.message(os.linesep)
    gs.message(("Fitting model using " + model_name))
    if balance is True and group_id is not None:
        estimator.fit(X, y, groups=group_id, **fit_params)
    elif balance is True and group_id is None:
        estimator.fit(X, y, **fit_params)
    else:
        estimator.fit(X, y)

    # message best hyperparameter setup and optionally save using pandas
    if any(param_grid) is True:
        gs.message(os.linesep)
        gs.message("Best parameters:")

        optimal_pars = [
            (k.replace("estimator__", "").replace("selection__", "") + " = " + str(v))
            for (k, v) in estimator.best_params_.items()
        ]

        for i in optimal_pars:
            gs.message(i)

        if param_file != "":
            param_df = pd.DataFrame(estimator.cv_results_)
            param_df.to_csv(param_file)

    # cross-validation --------------------------------------------------------
    if cv > 1:
        from sklearn.metrics import classification_report
        from sklearn import metrics

        if (
            mode == "classification"
            and cv > np.histogram(y, bins=np.unique(y))[0].min()
        ):
            gs.message(os.linesep)
            gs.fatal(
                "Number of cv folds is greater than number of samples in "
                "some classes "
            )

        gs.message(os.linesep)
        gs.message("Cross validation global performance measures......:")

        if (
            mode == "classification"
            and len(np.unique(y)) == 2
            and all([0, 1] == np.unique(y))
        ):
            scoring["roc_auc"] = metrics.roc_auc_score

        from sklearn.model_selection import cross_val_predict

        preds = cross_val_predict(
            estimator=estimator,
            X=X,
            y=y,
            groups=group_id,
            cv=outer,
            n_jobs=n_jobs,
            fit_params=fit_params,
        )

        test_idx = [test for train, test in outer.split(X, y)]
        n_fold = np.zeros((0,))

        for fold in range(outer.get_n_splits()):
            n_fold = np.hstack((n_fold, np.repeat(fold, test_idx[fold].shape[0])))

        preds = {"y_pred": preds, "y_true": y, "cat": cat, "fold": n_fold}

        preds = pd.DataFrame(data=preds, columns=["y_pred", "y_true", "cat", "fold"])
        gs.message(os.linesep)
        gs.message("Global cross validation scores...")
        gs.message(os.linesep)
        gs.message("Metric \t Mean \t Error")

        for name, func in scoring.items():
            score_mean = (
                preds.groupby("fold")
                .apply(lambda x: func(x["y_true"], x["y_pred"]))
                .mean()
            )

            score_std = (
                preds.groupby("fold")
                .apply(lambda x: func(x["y_true"], x["y_pred"]))
                .std()
            )

            gs.message(f"{name}\t{score_mean:.3}\t{score_std:.3}")

        if mode == "classification":
            gs.message(os.linesep)
            gs.message("Cross validation class performance measures......:")

            report_str = classification_report(
                y_true=preds["y_true"],
                y_pred=preds["y_pred"],
                sample_weight=class_weights,
                output_dict=False,
            )

            report = classification_report(
                y_true=preds["y_true"],
                y_pred=preds["y_pred"],
                sample_weight=class_weights,
                output_dict=True,
            )
            report = pd.DataFrame(report)

            gs.message(report_str)

            if classif_file != "":
                report.to_csv(classif_file, mode="w", index=True)

        # write cross-validation predictions to csv file
        if preds_file != "":
            preds.to_csv(preds_file, mode="w", index=False)
            text_file = open(preds_file + "t", "w")
            text_file.write('"Real", "Real", "integer", "integer"')
            text_file.close()

    # feature importances -----------------------------------------------------
    if importances is True:
        from sklearn.inspection import permutation_importance

        fimp = permutation_importance(
            estimator,
            X,
            y,
            scoring=search_scorer,
            n_repeats=5,
            n_jobs=n_jobs,
            random_state=random_state,
        )

        feature_names = deepcopy(stack.names)
        feature_names = [i.split("@")[0] for i in feature_names]

        fimp = pd.DataFrame(
            {
                "feature": feature_names,
                "importance": fimp["importances_mean"],
                "std": fimp["importances_std"],
            }
        )

        gs.message(os.linesep)
        gs.message("Feature importances")
        gs.message("Feature" + "\t" + "Score")

        for index, row in fimp.iterrows():
            gs.message(
                row["feature"] + "\t" + str(row["importance"]) + "\t" + str(row["std"])
            )

        if fimp_file != "":
            fimp.to_csv(fimp_file, index=False)

    # save the fitted model
    import joblib

    joblib.dump((estimator, y, class_labels), model_save)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
