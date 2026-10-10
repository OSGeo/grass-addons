#!/usr/bin/env python3

############################################################################
# MODULE:        r.learn.assembly
# AUTHOR:        Paulo van Breugel
# PURPOSE:       Combine several scikit-learn estimators into a voting or
#                stacking ensemble and train it on GRASS rasters. Base models
#                and their parameters are described in a JSON configuration
#                file; shared settings are passed through the module options.
#
# COPYRIGHT: (c) 2026 Paulo van Breugel, and the GRASS Development Team
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Train a voting or stacking ensemble of scikit-learn estimators on GRASS rasters.
# % keyword: raster
# % keyword: classification
# % keyword: regression
# % keyword: machine learning
# % keyword: scikit-learn
# % keyword: ensemble
# % keyword: parallel
# %end

# %option G_OPT_I_GROUP
# % key: group
# % label: Group of raster layers used as predictors
# % description: GRASS imagery group of raster maps representing predictor variables to be used in the ensemble model
# % required: no
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
# % description: Name of file to store the fitted ensemble using python joblib
# % required: no
# % guisection: Required
# %end

# %option
# % key: models
# % type: string
# % label: Base models to include in a configuration template
# % description: Write a JSON configuration template for the selected estimators and exit. Use with write_config.
# % multiple: yes
# % required: no
# % options: LogisticRegression,SGDClassifier,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,KNeighborsClassifier,GaussianNB,DecisionTreeClassifier,RandomForestClassifier,ExtraTreesClassifier,GradientBoostingClassifier,HistGradientBoostingClassifier,SVC,MLPClassifier,LinearRegression,SGDRegressor,KNeighborsRegressor,DecisionTreeRegressor,RandomForestRegressor,ExtraTreesRegressor,GradientBoostingRegressor,HistGradientBoostingRegressor,SVR,MLPRegressor
# % guisection: Template
# %end

# %option G_OPT_F_OUTPUT
# % key: write_config
# % label: Write a JSON configuration template to this file
# % description: Path to write a JSON ensemble configuration template for the selected models
# % required: no
# % guisection: Template
# %end

# %option G_OPT_F_INPUT
# % key: config
# % label: Ensemble configuration file
# % description: JSON file describing the base models, their parameters and (for voting) their weights
# % required: no
# % guisection: Ensemble
# %end

# %option
# % key: ensemble_type
# % type: string
# % label: Type of ensemble
# % description: Combine the base models by voting (fixed weights) or stacking (a meta-model learns the combination)
# % answer: stacking
# % options: voting,stacking
# % required: no
# % guisection: Ensemble
# %end

# %option
# % key: voting
# % type: string
# % label: Voting strategy
# % description: Hard voting uses predicted class labels, soft voting averages predicted probabilities (classification only, voting ensembles only)
# % answer: soft
# % options: soft,hard
# % required: no
# % guisection: Ensemble
# %end

# %option
# % key: final_estimator
# % type: string
# % label: Meta-model for stacking
# % description: Estimator that combines the base model predictions (stacking only). The default is to use LogisticRegression for classification and RidgeCV for regression
# % answer: default
# % options: default,LogisticRegression,RandomForestClassifier,RidgeCV,LinearRegression,RandomForestRegressor
# % required: no
# % guisection: Ensemble
# %end

# %option
# % key: cv
# % type: integer
# % label: Number of outer cross-validation folds
# % description: Number of cross-validation folds used to report the performance of the whole ensemble (1 disables cross-validation)
# % answer: 1
# % guisection: Cross validation
# %end

# %option
# % key: inner_cv
# % type: integer
# % label: Number of inner cross-validation folds (stacking)
# % description: Number of folds stacking uses internally to generate out-of-fold predictions for the meta-model (ignored for voting)
# % answer: 5
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: classif_file
# % label: Save classification report to csv
# % description: Name of output file to save the classification report (requires cv > 1)
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: preds_file
# % label: Save cross-validation predictions to csv
# % description: Name of output file in which to save the cross-validation predictions (requires cv > 1)
# % required: no
# % guisection: Cross validation
# %end

# %option G_OPT_F_OUTPUT
# % key: fimp_file
# % label: Save feature importances to csv
# % description: Name of file to save the permutation feature importance results (requires the -f flag)
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_R_INPUT
# % key: group_raster
# % label: Custom group ids for training samples from GRASS raster
# % description: GRASS raster containing group ids for training samples. Samples with the same group id will not be split between training and test cross-validation folds
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
# % description: Standardize feature variables (zero mean and unit variance)
# % guisection: Optional
# %end

# %flag
# % key: f
# % label: Compute feature importances
# % description: Compute permutation-based feature importances of the fitted ensemble
# % guisection: Optional
# %end

# %flag
# % key: b
# % label: Balance training data using class weights
# % description: Weight samples inversely proportional to class frequencies (classification only; every base model must support sample weights)
# % guisection: Optional
# %end

# %rules
# % required: config,models
# % exclusive: config,models
# % requires: models,write_config
# % requires: write_config,models
# % exclusive: write_config,config
# %end

import atexit
import json
import os

import grass.script as gs
import numpy as np
from grass.pygrass.raster import RasterRow

gs.utils.set_path(modulename="r.learn.ml2", dirname="rlearnlib", path="..")

tmp_rast = []

# Parameters whose values are managed by the module options. They are
# stripped from the written template and module options are written
# at build time.
MANAGED_PARAMS = ("random_state", "n_jobs", "verbose")

# Configuration parameters that scikit-learn expects as a tuple but that JSON
# can only represent as a list, so they are restored to tuples on read.
TUPLE_PARAMS = ("hidden_layer_sizes",)


def cleanup():
    """Remove any intermediate rasters if execution fails"""
    for rast in tmp_rast:
        gs.run_command("g.remove", name=rast, type="raster", flags="f", quiet=True)


def json_safe(value):
    """Return True if a value can be represented in JSON."""
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def restore_param_types(params):
    """Convert JSON lists back to the tuples scikit-learn expects for the
    parameters listed in TUPLE_PARAMS."""
    restored = dict(params)
    for key in TUPLE_PARAMS:
        if key in restored and isinstance(restored[key], list):
            restored[key] = tuple(restored[key])
    return restored


def write_template(models, path):
    """Write a JSON ensemble configuration template for the selected models.

    For each base model the scikit-learn defaults are included, and its
    parameters (minus the module-managed ones) are written as editable
    placeholders. Model keys are made unique when a model type is selected
    more than once.
    """
    from rlearnlib.utils import estimator_classes, estimator_family

    classes = estimator_classes()

    unknown = [m for m in models if m not in classes]
    if unknown:
        gs.fatal(_("Unknown model(s): {}").format(", ".join(unknown)))

    families = {estimator_family(m) for m in models}
    if len(families) > 1:
        gs.fatal(
            _(
                "The selected models mix classification and regression. "
                "Choose models of a single type."
            )
        )

    template = {}
    counts = {}
    for name in models:
        counts[name] = counts.get(name, 0) + 1
        key = name if counts[name] == 1 else "{}_{}".format(name, counts[name])

        params = classes[name]().get_params()
        for managed in MANAGED_PARAMS:
            params.pop(managed, None)
        params = {k: v for k, v in params.items() if json_safe(v)}

        template[key] = {"estimator": name, "weight": 1.0, "params": params}

    with open(path, "w") as fh:
        json.dump(template, fh, indent=2, sort_keys=False)

    gs.message(
        _(
            "Configuration template written to {}. Edit the parameters and "
            "weights, then rerun with config={}."
        ).format(path, path)
    )


def load_config(path):
    """Read and validate an ensemble configuration file.

    Returns a list of (key, estimator_name, params, weight) tuples and the
    detected mode ('classification' or 'regression').
    """
    from rlearnlib.utils import estimator_classes, estimator_family

    if not os.path.exists(path):
        gs.fatal(_("Configuration file {} does not exist").format(path))

    try:
        with open(path) as fh:
            config = json.load(fh)
    except (OSError, ValueError) as e:
        gs.fatal(_("Could not read configuration file {}: {}").format(path, e))

    if not isinstance(config, dict) or len(config) < 2:
        gs.fatal(_("The ensemble configuration must define at least two models"))

    classes = estimator_classes()
    members = []
    families = set()

    for key, entry in config.items():
        if not isinstance(entry, dict) or "estimator" not in entry:
            gs.fatal(_("Model '{}' must define an 'estimator'").format(key))

        name = entry["estimator"]
        if name not in classes:
            gs.fatal(_("Model '{}' uses unknown estimator '{}'").format(key, name))

        families.add(estimator_family(name))
        params = entry.get("params", {})
        if not isinstance(params, dict):
            gs.fatal(_("'params' for model '{}' must be an object").format(key))

        try:
            weight = float(entry.get("weight", 1.0))
        except (TypeError, ValueError):
            gs.fatal(_("'weight' for model '{}' must be a number").format(key))

        members.append((key, name, params, weight))

    if len(families) > 1:
        gs.fatal(
            _(
                "The configuration mixes classification and regression models. "
                "Use models of a single type."
            )
        )

    return members, families.pop()


def build_base_estimator(name, params, random_state, n_jobs, need_proba):
    """Instantiate a base estimator from the catalogue and apply the
    configuration parameters and the module-managed parameters."""
    from rlearnlib.utils import estimator_classes

    estimator = estimator_classes()[name]()
    valid = estimator.get_params().keys()

    params = restore_param_types(params)
    accepted = {k: v for k, v in params.items() if k in valid}
    ignored = [k for k in params if k not in valid]
    if ignored:
        gs.warning(
            _("Ignoring parameters not valid for {}: {}").format(
                name, ", ".join(ignored)
            )
        )
    estimator.set_params(**accepted)

    managed = {}
    if "random_state" in valid:
        managed["random_state"] = random_state
    if "n_jobs" in valid:
        managed["n_jobs"] = n_jobs
    if need_proba and "probability" in valid:
        # SVC needs probability=True to expose predict_proba for soft voting
        # and stacking.
        managed["probability"] = True
    estimator.set_params(**managed)

    return estimator


def build_final_estimator(name, mode, random_state):
    """Instantiate the stacking meta-model, resolving 'default' per mode."""
    from sklearn.linear_model import LogisticRegression, LinearRegression, RidgeCV
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from rlearnlib.utils import estimator_family

    if name == "default":
        name = "LogisticRegression" if mode == "classification" else "RidgeCV"

    if name == "RidgeCV":
        family = "regression"
    else:
        family = estimator_family(name)

    if family != mode:
        gs.fatal(_("final_estimator '{}' is not a {} model").format(name, mode))

    estimators = {
        "LogisticRegression": LogisticRegression,
        "RandomForestClassifier": RandomForestClassifier,
        "RidgeCV": RidgeCV,
        "LinearRegression": LinearRegression,
        "RandomForestRegressor": RandomForestRegressor,
    }
    estimator = estimators[name]()
    if "random_state" in estimator.get_params():
        estimator.set_params(random_state=random_state)

    return estimator


def build_ensemble(
    members,
    mode,
    ensemble_type,
    voting,
    final_estimator,
    inner_cv,
    random_state,
    n_jobs,
):
    """Construct a voting or stacking ensemble from the configured members."""
    from sklearn.ensemble import (
        VotingClassifier,
        VotingRegressor,
        StackingClassifier,
        StackingRegressor,
    )

    need_proba = ensemble_type == "stacking" or (
        ensemble_type == "voting" and voting == "soft"
    )

    estimators = [
        (
            key,
            build_base_estimator(name, params, random_state, n_jobs, need_proba),
        )
        for key, name, params, _weight in members
    ]

    if ensemble_type == "voting":
        weights = [weight for *_rest, weight in members]
        if mode == "classification":
            ensemble = VotingClassifier(
                estimators=estimators,
                voting=voting,
                weights=weights,
                n_jobs=n_jobs,
            )
        else:
            ensemble = VotingRegressor(
                estimators=estimators, weights=weights, n_jobs=n_jobs
            )
    else:
        final = build_final_estimator(final_estimator, mode, random_state)
        if mode == "classification":
            ensemble = StackingClassifier(
                estimators=estimators,
                final_estimator=final,
                cv=inner_cv,
                n_jobs=n_jobs,
            )
        else:
            ensemble = StackingRegressor(
                estimators=estimators,
                final_estimator=final,
                cv=inner_cv,
                n_jobs=n_jobs,
            )

    return ensemble


def build_preprocessor(norm_data, categorical, n_features):
    """Return a ColumnTransformer for standardization and/or one-hot encoding,
    or None when no preprocessing is requested. "categorical" is the list of
    categorical column indices (or None), and n_features the number of
    predictor columns. This is based on the preprocessing of r.learn.train."""
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import StandardScaler, OneHotEncoder

    if norm_data and categorical is None:
        return ColumnTransformer(
            remainder="passthrough",
            transformers=[("scaling", StandardScaler(), np.arange(0, n_features))],
        )

    if not norm_data and categorical is not None:
        return ColumnTransformer(
            remainder="passthrough",
            transformers=[
                (
                    "onehot",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    categorical,
                )
            ],
        )

    if norm_data and categorical is not None:
        return ColumnTransformer(
            remainder="passthrough",
            transformers=[
                (
                    "onehot",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    categorical,
                ),
                (
                    "scaling",
                    StandardScaler(),
                    np.setxor1d(range(n_features), categorical).astype("int"),
                ),
            ],
        )

    return None


def unsupported_sample_weight(members):
    """Return the names of configured base models that do not support sample
    weights. Voting and stacking can only use sample weights when every base
    model supports them."""
    from sklearn.utils.validation import has_fit_parameter
    from rlearnlib.utils import estimator_classes

    classes = estimator_classes()
    return [
        name
        for _key, name, _params, _weight in members
        if not has_fit_parameter(classes[name](), "sample_weight")
    ]


def unsupported_predict_proba(members, random_state, n_jobs):
    """Return the names of configured base models that cannot produce
    probabilities. Soft voting averages predicted probabilities, so every
    base model must provide predict_proba (e.g. SGDClassifier with its default
    hinge loss does not)."""
    bad = []
    for _key, name, params, _weight in members:
        estimator = build_base_estimator(
            name, params, random_state, n_jobs, need_proba=True
        )
        if not hasattr(estimator, "predict_proba"):
            bad.append(name)
    return bad


def sklearn_version():
    """Return the installed scikit-learn version as a (major, minor, micro)
    integer tuple, so versions such as 1.10.0 compare correctly."""
    import re
    import sklearn

    return tuple(int(x) for x in re.findall(r"\d+", sklearn.__version__)[:3])


def cv_fit_params(fit_params):
    """Return the keyword argument for passing fit parameters to the
    cross_val_* functions. scikit-learn 1.6 replaced the "fit_params"
    argument with "params". Nothing is passed when there are no fit
    parameters."""
    if not fit_params:
        return {}

    key = "params" if sklearn_version()[:2] >= (1, 6) else "fit_params"
    return {key: fit_params}


def main():
    from rlearnlib.utils import (
        load_training_data,
        save_training_data,
        option_to_list,
        scoring_metrics,
    )
    from rlearnlib.raster import RasterStack

    try:
        import sklearn  # noqa: F401

        if sklearn_version() < (1, 2, 2):
            gs.fatal(_("Package scikit-learn 1.2.2 or newer is not installed"))
    except ImportError:
        gs.fatal(_("Package scikit-learn 1.2.2 or newer is not installed"))

    try:
        import pandas as pd
    except ImportError:
        gs.fatal(_("Package pandas 0.25 or newer is not installed"))

    # template generation mode and exit
    models = option_to_list(options["models"])
    if models is not None:
        write_template(models, options["write_config"])
        return

    # run mode
    config = options["config"]
    group = options["group"]
    training_map = options["training_map"]
    training_points = options["training_points"]
    field = options["field"]
    model_save = options["save_model"]
    load_training = options["load_training"]
    save_training = options["save_training"]
    group_raster = options["group_raster"]
    category_maps = option_to_list(options["category_maps"])
    ensemble_type = options["ensemble_type"]
    voting = options["voting"]
    final_estimator = options["final_estimator"]
    cv = int(options["cv"])
    inner_cv = int(options["inner_cv"])
    classif_file = options["classif_file"]
    preds_file = options["preds_file"]
    fimp_file = options["fimp_file"]
    random_state = int(options["random_state"])
    n_jobs = int(options["n_jobs"])
    norm_data = flags["s"]
    balance = flags["b"]
    importances = flags["f"]

    if not model_save:
        gs.fatal(_("save_model is required when training an ensemble"))

    if load_training == "" and (
        group == "" or (training_map == "" and training_points == "")
    ):
        gs.fatal(
            _(
                "Provide training data through load_training, or through group "
                "together with training_map or training_points"
            )
        )

    members, mode = load_config(config)

    for output_file, label in (
        (classif_file, "classif_file"),
        (preds_file, "preds_file"),
    ):
        if output_file:
            if cv <= 1:
                gs.fatal(
                    _("Output of {} requires cross-validation cv > 1").format(label)
                )
            if not os.path.isdir(os.path.dirname(output_file) or "."):
                gs.fatal(
                    _("Directory for output file {} does not exist").format(output_file)
                )

    if fimp_file and not importances:
        gs.fatal(_("Output of feature importances requires the -f flag"))
    if fimp_file and not os.path.isdir(os.path.dirname(fimp_file) or "."):
        gs.fatal(_("Directory for output file {} does not exist").format(fimp_file))

    if classif_file and mode == "regression":
        gs.fatal(
            _("A classification report is only available for classification models")
        )

    if balance and mode == "regression":
        gs.warning(_("Balancing of class weights is only possible for classification"))
        balance = False

    if balance:
        unsupported = unsupported_sample_weight(members)
        if unsupported:
            gs.fatal(
                _(
                    "Class balancing (-b) requires every base model to support "
                    "sample weights, but these do not: {}"
                ).format(", ".join(unsupported))
            )

    if ensemble_type == "voting" and voting == "soft" and mode == "classification":
        no_proba = unsupported_predict_proba(members, random_state, n_jobs)
        if no_proba:
            gs.fatal(
                _(
                    "Soft voting requires every base model to produce "
                    "probabilities (predict_proba), but these do not: {}. "
                    "Use voting=hard or replace the model."
                ).format(", ".join(no_proba))
            )

    # extract training data
    if load_training != "":
        gs.message(_("Loading training data ..."))
        # RasterStack needs an imagery group or rasters, so it is not created
        # when the training data come from a file.
        stack = None
        if category_maps is not None:
            gs.warning(
                _("category_maps is ignored when loading training data from a file")
            )
            category_maps = None
        X, y, cat, class_labels, group_id = load_training_data(load_training)

        if class_labels is not None:
            a = pd.DataFrame({"response": y, "labels": class_labels})
            a = a.drop_duplicates().values
            class_labels = {k: v for (k, v) in a}
    else:
        gs.message(_("Extracting training data"))

        stack = RasterStack(group=group)
        if category_maps is not None:
            stack.categorical = category_maps

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

        if group_raster != "":
            group_id = X[:, -1]
            X = np.delete(X, -1, axis=1)
            stack.drop(group_raster)
        else:
            group_id = None

        if y.shape[0] == 0 or X.shape[0] == 0:
            gs.fatal(
                _(
                    "No training pixels or pixels in imagery group ...check "
                    "computational region"
                )
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

    scoring, search_scorer = scoring_metrics(mode)

    # build the ensemble and optional preprocessing pipeline
    from sklearn.pipeline import Pipeline

    ensemble = build_ensemble(
        members,
        mode,
        ensemble_type,
        voting,
        final_estimator,
        inner_cv,
        random_state,
        n_jobs,
    )

    categorical = (
        stack.categorical if (stack is not None and category_maps is not None) else None
    )
    preprocessor = build_preprocessor(norm_data, categorical, X.shape[1])

    def as_estimator(model):
        """Wrap an estimator in the preprocessing pipeline when requested."""
        if preprocessor is None:
            return model
        return Pipeline([("preprocessing", preprocessor), ("estimator", model)])

    estimator = as_estimator(ensemble)

    # balanced sample weights, routed to each base model's fit. When the
    # estimator is wrapped in a preprocessing pipeline the weights must target
    # its "estimator" step.
    class_weights = None
    fit_params = {}
    if balance:
        from sklearn.utils.class_weight import compute_sample_weight

        class_weights = compute_sample_weight("balanced", y)
        weight_key = (
            "estimator__sample_weight" if preprocessor is not None else "sample_weight"
        )
        fit_params = {weight_key: class_weights}

    # cross-validation splitter for the whole ensemble
    from sklearn.model_selection import StratifiedKFold, GroupKFold, KFold

    outer = None
    if cv > 1:
        if group_id is not None:
            outer = GroupKFold(n_splits=cv)
        elif mode == "classification":
            outer = StratifiedKFold(n_splits=cv)
        else:
            outer = KFold(n_splits=cv)

    # report the composition of the ensemble
    gs.message(os.linesep)
    gs.message(_("Ensemble composition"))
    gs.message(_("Type: {} ({} models)").format(ensemble_type, len(members)))
    for key, name, _params, weight in members:
        if ensemble_type == "voting":
            gs.message("  {} = {} (weight {:g})".format(key, name, weight))
        else:
            gs.message("  {} = {}".format(key, name))
    if ensemble_type == "stacking":
        resolved = final_estimator
        if resolved == "default":
            resolved = "LogisticRegression" if mode == "classification" else "RidgeCV"
        gs.message(_("Meta-model: {}").format(resolved))

    # fit the ensemble
    gs.message(os.linesep)
    gs.message(_("Fitting {} ensemble").format(ensemble_type))
    estimator.fit(X, y, **fit_params)

    # cross-validation of the whole ensemble
    if cv > 1:
        from sklearn.model_selection import cross_val_predict, cross_val_score
        from sklearn.metrics import classification_report

        if mode == "classification":
            class_counts = np.unique(y, return_counts=True)[1]
            if cv > class_counts.min():
                gs.fatal(
                    _(
                        "Number of cv folds is greater than number of samples "
                        "in some classes"
                    )
                )

        gs.message(os.linesep)
        gs.message(_("Cross validation global performance measures......:"))

        preds = cross_val_predict(
            estimator=estimator,
            X=X,
            y=y,
            groups=group_id,
            cv=outer,
            n_jobs=n_jobs,
            **cv_fit_params(fit_params),
        )

        # cross_val_predict returns predictions in the original sample order,
        # so each sample's fold id must be written at its own position rather
        # than concatenated in fold order (the test indices are not contiguous
        # for stratified or grouped splits).
        n_fold = np.empty(len(y), dtype=int)
        for fold, (_train, test) in enumerate(outer.split(X, y, group_id)):
            n_fold[test] = fold

        preds = {"y_pred": preds, "y_true": y, "cat": cat, "fold": n_fold}
        preds = pd.DataFrame(data=preds, columns=["y_pred", "y_true", "cat", "fold"])

        gs.message(os.linesep)
        gs.message(_("Global cross validation scores..."))
        gs.message(os.linesep)
        gs.message(_("Metric \t Mean \t Error"))

        for name, func in scoring.items():
            scores = preds.groupby("fold").apply(
                lambda x: func(x["y_true"], x["y_pred"])
            )
            gs.message(f"{name}\t{scores.mean():.3}\t{scores.std():.3}")

        # per-base-model cross-validation score, to show whether the ensemble
        # improves on its individual members
        gs.message(os.linesep)
        gs.message(_("Per-model cross validation score ({})...").format(search_scorer))
        for key, name, params, _weight in members:
            need_proba = ensemble_type == "stacking" or (
                ensemble_type == "voting" and voting == "soft"
            )
            base = as_estimator(
                build_base_estimator(name, params, random_state, n_jobs, need_proba)
            )
            base_scores = cross_val_score(
                base,
                X,
                y,
                groups=group_id,
                cv=outer,
                scoring=search_scorer,
                n_jobs=n_jobs,
                **cv_fit_params(fit_params),
            )
            gs.message(f"  {key}\t{base_scores.mean():.3}")

        if mode == "classification":
            gs.message(os.linesep)
            gs.message(_("Cross validation class performance measures......:"))
            if class_weights is not None:
                gs.message(
                    _(
                        "(class balancing is on: the per-class report below is "
                        "weighted, so support values are sums of sample weights, "
                        "while the global scores above are unweighted)"
                    )
                )

            report_str = classification_report(
                y_true=preds["y_true"],
                y_pred=preds["y_pred"],
                sample_weight=class_weights,
                output_dict=False,
            )
            report = pd.DataFrame(
                classification_report(
                    y_true=preds["y_true"],
                    y_pred=preds["y_pred"],
                    sample_weight=class_weights,
                    output_dict=True,
                )
            )
            gs.message(report_str)

            if classif_file != "":
                report.to_csv(classif_file, mode="w", index=True)

        if preds_file != "":
            preds.to_csv(preds_file, mode="w", index=False)
            text_file = open(preds_file + "t", "w")
            text_file.write('"Real", "Real", "integer", "integer"')
            text_file.close()

    # report the learned stacking weights when available
    if ensemble_type == "stacking":
        fitted = estimator
        if isinstance(fitted, Pipeline):
            fitted = fitted.named_steps["estimator"]
        final_fitted = getattr(fitted, "final_estimator_", None)
        coef = getattr(final_fitted, "coef_", None)
        if coef is not None:
            gs.message(os.linesep)
            gs.message(_("Learned meta-model weights (coefficients)..."))
            gs.message(str(np.round(np.asarray(coef), 3)))

    # permutation feature importances of the fitted ensemble, computed on the
    # training data (as in r.learn.train) using the tuning scorer
    if importances:
        from sklearn.inspection import permutation_importance

        result = permutation_importance(
            estimator,
            X,
            y,
            scoring=search_scorer,
            n_repeats=5,
            n_jobs=n_jobs,
            random_state=random_state,
        )

        if stack is not None:
            feature_names = [name.split("@")[0] for name in stack.names]
        else:
            feature_names = ["feature{}".format(i) for i in range(X.shape[1])]

        fimp = pd.DataFrame(
            {
                "feature": feature_names,
                "importance": result["importances_mean"],
                "std": result["importances_std"],
            }
        )

        gs.message(os.linesep)
        gs.message(_("Feature importances (permutation, on training data)"))
        gs.message(_("Feature\tImportance\tStd"))
        for _index, row in fimp.iterrows():
            gs.message(
                "{}\t{}\t{}".format(row["feature"], row["importance"], row["std"])
            )

        if fimp_file != "":
            fimp.to_csv(fimp_file, index=False)

    # save the fitted ensemble
    import joblib

    joblib.dump((estimator, y, class_labels), model_save)
    gs.message(os.linesep)
    gs.message(_("Ensemble model saved to {}").format(model_save))


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
