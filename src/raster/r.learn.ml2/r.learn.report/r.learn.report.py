#!/usr/bin/env python3

############################################################################
# MODULE:        r.learn.report
# AUTHOR:        Paulo van Breugel
# PURPOSE:       Creates a report from the outputs of r.learn.train
#                and r.learn.assembly: a saved model and the optional cross-
#                validation, feature-importance and hyperparameter CSV files.
#                The report is written as Markdown with short explanations,
#                tables and figures.
#
# COPYRIGHT: (c) 2026 Paulo van Breugel, and the GRASS Development Team
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Build a readable report from r.learn.train or r.learn.assembly outputs.
# % keyword: raster
# % keyword: classification
# % keyword: regression
# % keyword: machine learning
# % keyword: scikit-learn
# % keyword: report
# %end

# %option G_OPT_F_BIN_INPUT
# % key: load_model
# % label: Fitted model file
# % description: Model saved by r.learn.train or r.learn.assembly
# % required: no
# % guisection: Inputs
# %end

# %option G_OPT_F_BIN_INPUT
# % key: classif_file
# % label: Classification report csv
# % description: Per-class metrics csv written by r.learn.train or r.learn.assembly
# % required: no
# % guisection: Inputs
# %end

# %option G_OPT_F_BIN_INPUT
# % key: preds_file
# % label: Cross-validation predictions csv
# % description: Cross-validation predictions csv written by r.learn.train or r.learn.assembly
# % required: no
# % guisection: Inputs
# %end

# %option G_OPT_F_BIN_INPUT
# % key: fimp_file
# % label: Feature importances csv
# % description: Permutation feature importances csv written by r.learn.train
# % required: no
# % guisection: Inputs
# %end

# %option G_OPT_F_BIN_INPUT
# % key: param_file
# % label: Hyperparameter search csv
# % description: Hyperparameter tuning results csv written by r.learn.train
# % required: no
# % guisection: Inputs
# %end

# %option G_OPT_F_BIN_INPUT
# % key: training_file
# % label: Training data csv
# % description: Extracted training data csv written with the save_training option of r.learn.train or r.learn.assembly; needed, together with load_model, for the response curves
# % required: no
# % guisection: Inputs
# %end

# %option G_OPT_F_BIN_OUTPUT
# % key: output
# % label: Output report file
# % description: Path to write the Markdown report
# % guisection: Output
# % required: yes
# %end

# %option
# % key: title
# % type: string
# % label: Report title
# % description: Title shown at the top of the report
# % answer: Machine learning model report
# % required: no
# %end

# %option
# % key: mode
# % type: string
# % label: Problem type
# % description: Whether the model is a classification or regression model; 'auto' detects it from the model or, failing that, from the predictions
# % answer: auto
# % options: auto,classification,regression
# % required: no
# %end

# %option
# % key: curves
# % type: string
# % label: Response-curve content
# % description: Median with 25-75 and 10-90 percentile bands (band), individual conditional expectation (ICE) curves (pdp_ice), or the mean curve only (pdp)
# % answer: band
# % options: band,pdp_ice,pdp
# % required: no
# % guisection: Output
# %end

# %option G_OPT_M_NPROCS
# % key: nprocs
# % label: Number of processor threads to use
# % description: Number of cores used to compute the response curves, -2 is n_cores-1
# % answer: -2
# % guisection: Output
# %end

# %flag
# % key: c
# % label: Also add centered response curves
# % description: Add a second set of centered curves (each shifted to start at zero) alongside the normal ones, so the spread shows how differently the predictor affects individual samples, that is, interaction (band and pdp_ice only)
# % guisection: Output
# %end

# %rules
# % required: load_model,classif_file,preds_file,fimp_file,param_file
# %end

import math
import os
from datetime import datetime

import grass.script as gs

gs.utils.set_path(modulename="r.learn.ml2", dirname="rlearnlib", path="..")

# Partial-dependence is computed by the "brute" method for ensembles, whose cost
# scales with the number of training rows; a random subsample keeps it fast
# while giving essentially the same curves. The grid resolution is the number of
# points each predictor is evaluated at.
PDP_MAX_SAMPLES = 500
PDP_GRID_RESOLUTION = 50


def md_table(frame, index_label=""):
    """Render a pandas DataFrame as a GitHub-flavoured Markdown table.

    Float values are shown with three significant digits; the index is
    included as the first column with the given label.
    """

    def fmt(value):
        if isinstance(value, float):
            return f"{value:.3g}"
        return str(value)

    header = [index_label, *[str(c) for c in frame.columns]]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for idx, row in frame.iterrows():
        cells = [str(idx), *[fmt(v) for v in row]]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def unwrap_estimator(estimator):
    """Return the final estimator, unwrapping a preprocessing Pipeline."""
    steps = getattr(estimator, "named_steps", None)
    if steps is not None and "estimator" in steps:
        return steps["estimator"]
    return estimator


def model_overview(model_file):
    """Return a Markdown section describing the fitted model."""
    import joblib
    from sklearn.base import is_classifier

    loaded = joblib.load(model_file)
    if isinstance(loaded, tuple):
        estimator = loaded[0]
        class_labels = loaded[2] if len(loaded) > 2 else None
    else:
        estimator = loaded
        class_labels = None

    inner = unwrap_estimator(estimator)
    mode = "classification" if is_classifier(inner) else "regression"

    lines = ["## Model", ""]
    lines.append(
        "This report describes a {} model of type `{}`.".format(
            mode, type(inner).__name__
        )
    )

    n_features = getattr(estimator, "n_features_in_", None)
    if n_features is not None:
        lines.append("")
        lines.append("Number of predictor features: {}.".format(n_features))

    if estimator is not inner:
        lines.append("")
        lines.append(
            "Predictors are preprocessed before fitting (e.g. standardization "
            "or one-hot encoding) as part of a pipeline."
        )

    # ensemble members, if any
    base_estimators = getattr(inner, "estimators", None)
    if base_estimators is not None:
        import pandas as pd

        weights = getattr(inner, "weights", None)
        rows = {}
        for i, (name, est) in enumerate(base_estimators):
            entry = {"type": type(est).__name__}
            if weights is not None and weights[i] is not None:
                entry["weight"] = weights[i]
            rows[name] = entry
        table = pd.DataFrame.from_dict(rows, orient="index")
        lines.append("")
        lines.append(
            "The model is an ensemble that combines the following base models:"
        )
        lines.append("")
        lines.append(md_table(table, index_label="model"))

        final = getattr(inner, "final_estimator_", None)
        if final is not None:
            lines.append("")
            lines.append(
                "The base model predictions are combined by a `{}` meta-model "
                "(stacking).".format(type(final).__name__)
            )
            coef = getattr(final, "coef_", None)
            if coef is not None:
                import numpy as np

                lines.append("")
                lines.append(
                    "Learned meta-model coefficients: `{}`.".format(
                        np.round(np.asarray(coef), 3).tolist()
                    )
                )
                lines.append("")
                lines.append(
                    "These are the fitted coefficients of the meta-model, not "
                    "normalized per-model weights: a base model can contribute "
                    "several inputs (one per class in multiclass problems), the "
                    "values can be negative, and they depend on the scale of the "
                    "base predictions. Read them as the meta-model's reliance on "
                    "each input, not as a ranking of base-model importance."
                )
        elif weights is not None:
            lines.append("")
            lines.append(
                "The base models are combined by weighted voting with the fixed "
                "weights given in the configuration."
            )

    if class_labels:
        lines.append("")
        labels = ", ".join(str(v) for v in class_labels.values())
        lines.append("Classes: {}.".format(labels))

    return mode, "\n".join(lines)


def infer_mode_from_preds(preds):
    """Guess classification vs regression from the cross-validation predictions."""
    y_true = preds["y_true"]
    unique = y_true.dropna().unique()
    looks_integer = all(float(v).is_integer() for v in unique)
    if looks_integer and len(unique) <= 20:
        return "classification"
    return "regression"


def cv_performance(preds_file, mode, plots_dir, plots_rel, make_plots):
    """Return a Markdown section with global cross-validation scores and a
    diagnostic figure."""
    import pandas as pd
    from rlearnlib.utils import scoring_metrics

    preds = pd.read_csv(preds_file)
    if mode is None:
        mode = infer_mode_from_preds(preds)
        gs.warning(
            _(
                "Problem type was guessed as '{}' from the predictions; set the "
                "mode option explicitly if this is wrong."
            ).format(mode)
        )

    scoring, _search_scorer = scoring_metrics(mode)

    rows = {}
    # select the score columns so the "fold" grouping column is not passed to
    # the scoring function (avoids a pandas FutureWarning without changing the
    # result)
    grouped = preds.groupby("fold")[["y_true", "y_pred"]]
    for name, func in scoring.items():
        per_fold = grouped.apply(lambda x: func(x["y_true"], x["y_pred"]))
        rows[name] = {"mean": per_fold.mean(), "std": per_fold.std()}
    table = pd.DataFrame.from_dict(rows, orient="index")

    lines = ["## Cross-validation performance", ""]
    lines.append(
        "Scores are computed per cross-validation fold and summarized as the "
        "mean and standard deviation across folds. They estimate how the model "
        "performs on data not used for training."
    )
    lines.append("")
    lines.append(md_table(table, index_label="metric"))
    lines.append("")
    if mode == "classification":
        lines.append(
            "The confusion matrix below summarises the cross-validation "
            "predictions. Each row is an observed (true) class and each "
            "column a predicted class. So counts on the diagonal are "
            "correct predictions and off-diagonal cells show which classes "
            "are confused with which. A strong diagonal indicates good "
            "agreement. Clusters off the diagonal point to systematic "
            "confusion between specific classes."
        )
    else:
        lines.append(
            "The plot below compares predicted values against observed "
            "values from the cross-validation. Each point is a sample, "
            "and the dashed line marks perfect prediction (predicted = observed)."
            " Points close to that line are accurate; systematic departure from "
            "it indicates bias (consistent over- or under-prediction), while "
            "vertical scatter around it reflects the size of the prediction error."
        )
    lines.append("")
    if make_plots:
        figure = _cv_figure(preds, mode, plots_dir)
        if figure is not None:
            caption = (
                "Confusion matrix of the cross-validation predictions."
                if mode == "classification"
                else "Predicted versus observed values of the cross-validation "
                "predictions."
            )
            lines.append("")
            lines.append("![{}]({})".format(caption, plots_rel + "/" + figure))
            lines.append("")
            lines.append("*{}*".format(caption))

    return "\n".join(lines)


def _cv_figure(preds, mode, plots_dir):
    """Create and save the cross-validation diagnostic figure, returning its
    file name (or None on failure)."""
    import matplotlib.pyplot as plt

    try:
        fig, name = _build_cv_figure(preds, mode)
        fig.savefig(os.path.join(plots_dir, name), dpi=100)
        plt.close(fig)
        return name
    except Exception as e:
        gs.warning(_("Could not create cross-validation figure: {}").format(e))
        return None


def _build_cv_figure(preds, mode):
    """Build the cross-validation diagnostic figure, returning it together with
    the file name to save it under."""
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay, PredictionErrorDisplay

    fig, ax = plt.subplots(figsize=(3, 3))
    if mode == "classification":
        ConfusionMatrixDisplay.from_predictions(
            preds["y_true"], preds["y_pred"], ax=ax, colorbar=False
        )
        ax.set_title("Cross-validation confusion matrix")
        name = "confusion_matrix.png"
    else:
        PredictionErrorDisplay.from_predictions(
            preds["y_true"],
            preds["y_pred"],
            kind="actual_vs_predicted",
            ax=ax,
        )
        ax.set_title("Cross-validation predicted vs observed")
        name = "predicted_vs_observed.png"
    fig.tight_layout()
    return fig, name


def classification_table(classif_file):
    """Return a Markdown section with the per-class metrics table."""
    import pandas as pd

    report = pd.read_csv(classif_file, index_col=0)
    lines = ["## Per-class performance", ""]
    lines.append(
        "Precision, recall and F1-score for each class, from the "
        "cross-validation predictions. Support is the number of samples of "
        "each class (a sum of sample weights if class balancing was used "
        "during training)."
    )
    lines.append("")

    # classification_report stores overall accuracy as a single scalar, which
    # pandas broadcast across every metric row when the report was written.
    # Show it on its own rather than as a misleading per-class column.
    accuracy = None
    if "accuracy" in report.columns:
        accuracy = report["accuracy"].iloc[0]
        report = report.drop(columns="accuracy")

    lines.append(md_table(report, index_label="metric"))
    if accuracy is not None:
        lines.append("")
        lines.append("Overall accuracy: {:.3g}.".format(accuracy))
    return "\n".join(lines)


def feature_importances(fimp_file, plots_dir, plots_rel, make_plots):
    """Return a Markdown section with the feature-importance table and chart."""
    import pandas as pd

    fimp = pd.read_csv(fimp_file)
    fimp = fimp.sort_values("importance", ascending=False)

    lines = ["## Variable contributions", ""]
    lines.append(
        "Permutation feature importance: the drop in model performance when "
        "each predictor in turn is randomly shuffled. Larger values indicate "
        "predictors the model relies on more. Interpret with caution when "
        "predictors are correlated."
    )
    lines.append("")
    lines.append(
        "In *r.learn.train* and *r.learn.assembly* these importances are "
        "computed on the training data, not on an independent validation set, "
        "so they describe how the fitted model uses each predictor rather than "
        "generalization. The "
        "performance drop is measured with the model's tuning score (Matthews "
        "correlation coefficient for classification, R-squared for regression)."
    )
    lines.append("")
    lines.append(md_table(fimp.set_index("feature"), index_label="feature"))

    if make_plots:
        figure = _importance_figure(fimp, plots_dir)
        if figure is not None:
            caption = "Permutation feature importance (mean +/- standard deviation)."
            lines.append("")
            lines.append("![{}]({})".format(caption, plots_rel + "/" + figure))
            lines.append("")
            lines.append("*{}*".format(caption))

    return "\n".join(lines)


def _importance_figure(fimp, plots_dir):
    """Create and save the feature-importance bar chart, returning its file
    name (or None on failure)."""
    import matplotlib.pyplot as plt

    try:
        fig, name = _build_importance_figure(fimp)
        fig.savefig(os.path.join(plots_dir, name), dpi=120)
        plt.close(fig)
        return name
    except Exception as e:
        gs.warning(_("Could not create feature-importance figure: {}").format(e))
        return None


def _build_importance_figure(fimp):
    """Build the feature-importance bar chart, returning it together with the
    file name to save it under."""
    import matplotlib.pyplot as plt

    ordered = fimp.sort_values("importance")
    fig, ax = plt.subplots(figsize=(6, max(2, 0.4 * len(ordered) + 1)))
    xerr = ordered["std"] if "std" in ordered.columns else None
    ax.barh(ordered["feature"], ordered["importance"], xerr=xerr)
    ax.set_xlabel("importance")
    ax.set_title("Permutation feature importance")
    fig.tight_layout()
    return fig, "feature_importance.png"


def _feature_order(feature_names, fimp_file):
    """Return predictor column indices ordered most-important first.

    Ordering uses the feature-importance file when it is available and falls
    back to the order the predictors appear in the training data otherwise.
    """
    default = list(range(len(feature_names)))
    if not fimp_file:
        return default

    import pandas as pd

    try:
        fimp = pd.read_csv(fimp_file)
        ranked = list(fimp.sort_values("importance", ascending=False)["feature"])
    except Exception:
        return default

    index_of = {name: i for i, name in enumerate(feature_names)}
    order = [index_of[name] for name in ranked if name in index_of]
    order += [i for i in default if i not in order]
    return order


def response_curves(
    training_file,
    model_file,
    fimp_file,
    plots_dir,
    plots_rel,
    make_plots,
    curves,
    centered,
    nprocs,
):
    """Return a Markdown section with partial-dependence response curves.

    One panel per predictor shows how the predicted outcome changes as that
    predictor is varied across its range, with the other predictors
    marginalized over the training data. A multiclass model produces one
    figure per class.
    """
    import joblib
    import numpy as np
    import pandas as pd

    data = pd.read_csv(training_file)
    # save_training_data (rlearnlib.utils) writes the predictor columns first,
    # followed by these bookkeeping columns.
    meta_cols = ["response", "cat", "class_labels", "groups"]
    feature_cols = [c for c in data.columns if c not in meta_cols]
    if not feature_cols:
        gs.warning(
            _("No predictor columns found in {}; skipping response curves.").format(
                training_file
            )
        )
        return None
    predictors = data[feature_cols].to_numpy()
    # Partial dependence re-evaluates the model over every row, so cap the data
    # at a random subsample to keep it fast (the curves are essentially the
    # same). A fixed seed keeps the subsample reproducible.
    n_samples = predictors.shape[0]
    subsampled = n_samples > PDP_MAX_SAMPLES
    if subsampled:
        rng = np.random.default_rng(1)
        keep = rng.choice(n_samples, size=PDP_MAX_SAMPLES, replace=False)
        predictors = predictors[keep]
    # Strip any @mapset qualifier so the labels match the importance table.
    feature_names = [c.split("@")[0] for c in feature_cols]

    loaded = joblib.load(model_file)
    estimator = loaded[0] if isinstance(loaded, tuple) else loaded
    class_labels = loaded[2] if isinstance(loaded, tuple) and len(loaded) > 2 else None

    lines = ["## Response curves", ""]
    lines.append(
        "Partial-dependence curves show how the predicted outcome changes as "
        "one predictor is varied across its range (5th to 95th percentile), "
        "while the other predictors are marginalized over the training data. "
        "For a classification model the vertical axis is the predicted "
        "probability of the class; for a regression model it is the predicted "
        "value."
    )
    lines.append("")
    if curves == "pdp":
        lines.append("The line is the mean response (the partial-dependence curve).")
    elif curves == "band":
        lines.append(
            "The solid line is the median response across samples and the dashed "
            "line their mean; a gap between them points to a skewed or "
            "outlier-influenced spread. The shaded areas are the 25-75% and "
            "10-90% ranges of the per-sample responses."
        )
    else:  # pdp_ice
        lines.append(
            "The faint lines are individual conditional expectation (ICE) "
            "curves, one per sample; the solid line is their median and the "
            "dashed line their mean."
        )

    # centering adds a second set of curves (the interaction view) alongside the
    # normal ones, so both can be compared; it only applies where there is a
    # spread to center.
    show_centered = centered and curves in ("band", "pdp_ice")
    if centered and curves == "pdp":
        gs.warning(_("The -c flag has no effect with curves=pdp and is ignored."))

    if curves in ("band", "pdp_ice"):
        lines.append("")
        spread = (
            "A wide spread means the predicted outcome varies a lot across "
            "samples at a given predictor value, which reflects the influence of "
            "the other predictors. This is not in itself an interaction: even "
            "purely additive effects produce vertically shifted curves."
        )
        if not show_centered:
            spread += (
                " To read interaction, rerun with the -c flag, which adds "
                "centered curves where the spread shows how differently the "
                "predictor acts on individual samples."
            )
        lines.append(spread)

    lines.append("")
    data_note = "The curves are evaluated on the saved training data"
    if subsampled:
        data_note += " (a random subsample of {} of the {} rows)".format(
            PDP_MAX_SAMPLES, n_samples
        )
    lines.append(
        data_note + ". Where predictors are strongly correlated, parts of a "
        "curve can reach into predictor combinations that do not occur in the "
        "data, so read those regions with care."
    )

    if not make_plots:
        return "\n".join(lines)

    order = _feature_order(feature_names, fimp_file)
    # Multiclass models produce one figure per class; binary and regression
    # models have a single output. The output axis of the partial-dependence
    # result is ordered like estimator.classes_.
    classes = list(getattr(estimator, "classes_", []))
    is_classification = len(classes) > 0
    if len(classes) > 2:
        targets = [(c, i) for i, c in enumerate(classes)]
    else:
        targets = [(None, 0)]

    # Partial dependence is computed once for all predictors (one call returns
    # every class output) and reused for each class and for the normal and
    # centered figures.
    kind = "average" if curves == "pdp" else "both"
    try:
        results = _compute_pd(estimator, predictors, order, kind, nprocs)
    except Exception as e:
        gs.warning(_("Could not compute response curves: {}").format(e))
        lines.append("")
        lines.append(
            "Response curves could not be produced for this model. Partial "
            "dependence needs class probabilities, which some estimators (such "
            "as a hard-voting ensemble) do not provide."
        )
        return "\n".join(lines)

    centered_intro = (
        "The centered curves below start each sample at zero at the left of the "
        "predictor's range, so the spread shows how differently the predictor "
        "affects individual samples, that is, its interaction with the other "
        "predictors."
    )
    variants = [("Normal", False, None)]
    if show_centered:
        variants.append(("Centered", True, centered_intro))

    # When both variants are shown they get a group heading (### Normal / ###
    # Centered) and the per-class figures drop a level to ####; with a single
    # variant the per-class figures stay at ###.
    grouped = len(variants) > 1
    class_level = "####" if grouped else "###"

    for group_name, is_centered, intro in variants:
        if grouped:
            lines.append("")
            lines.append("### {} response curves".format(group_name))
        if intro:
            lines.append("")
            lines.append(intro)
        for target, target_idx in targets:
            name = _render_response_figure(
                results,
                order,
                feature_names,
                curves,
                is_centered,
                target,
                target_idx,
                is_classification,
                plots_dir,
            )
            prefix = (
                "Centered response curves"
                if is_centered
                else "Partial-dependence response curves"
            )
            if target is None:
                caption = prefix + "."
            else:
                # fall back to the raw class value when there is no label
                label = class_labels.get(target, target) if class_labels else target
                caption = "{} for class {}.".format(prefix, label)
                lines.append("")
                lines.append("{} Class {}".format(class_level, label))
            lines.append("")
            lines.append("![{}]({})".format(caption, plots_rel + "/" + name))
            lines.append("")
            lines.append("*{}*".format(caption))

    return "\n".join(lines)


def _compute_pd(estimator, X, features, kind, n_jobs):
    """Compute partial dependence once per predictor (one call returns every
    class output), parallelized across predictors since the low-level function
    is not parallel on its own. Raises if the estimator cannot be evaluated
    (e.g. a hard-voting ensemble with no probabilities)."""
    from joblib import Parallel, delayed
    from sklearn.inspection import partial_dependence

    return Parallel(n_jobs=n_jobs)(
        delayed(partial_dependence)(
            estimator, X, features=[f], kind=kind, grid_resolution=PDP_GRID_RESOLUTION
        )
        for f in features
    )


def _render_response_figure(
    results,
    features,
    feature_names,
    curves,
    centered,
    target,
    target_idx,
    is_classification,
    plots_dir,
):
    """Render and save one response-curve figure (one panel per predictor) from
    precomputed partial-dependence results, returning its file name. Each panel
    shows the mean curve (pdp), the ICE curves plus median and mean (pdp_ice),
    or the median with 25-75 and 10-90 percentile bands and the mean (band).
    When *centered*, each curve is shifted to start at zero."""
    import matplotlib.pyplot as plt
    import numpy as np

    n_cols = min(3, len(features))
    n_rows = math.ceil(len(features) / n_cols)
    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(n_cols * 3.0, n_rows * 2.8), squeeze=False
    )
    flat = axes.ravel()

    for panel, (f, res) in enumerate(zip(features, results)):
        ax = flat[panel]
        grid = np.asarray(res["grid_values"][0])
        avg = np.asarray(res["average"])[target_idx]
        if centered:
            avg = avg - avg[0]

        if curves == "pdp":
            ax.plot(grid, avg, color="C0", lw=2.0, label="mean")
        else:
            # per-sample ICE values for the target output
            ind = np.asarray(res["individual"])[target_idx]
            if centered:
                ind = ind - ind[:, [0]]
            median = np.median(ind, axis=0)
            mean = ind.mean(axis=0)

            if curves == "pdp_ice":
                ax.plot(grid, ind.T, color="0.6", lw=0.3, alpha=0.3)
            else:  # band
                p10, p90 = np.percentile(ind, [10, 90], axis=0)
                p25, p75 = np.percentile(ind, [25, 75], axis=0)
                ax.fill_between(grid, p10, p90, color="C0", alpha=0.15, label="10-90%")
                ax.fill_between(grid, p25, p75, color="C0", alpha=0.30, label="25-75%")

            ax.plot(grid, median, color="C0", lw=2.0, label="median")
            ax.plot(grid, mean, color="C3", lw=1.3, ls="--", label="mean")

        ax.set_xlabel(feature_names[f])
        if panel % n_cols == 0:
            base = "predicted probability" if is_classification else "predicted value"
            ax.set_ylabel(("change in " if centered else "") + base)

    for extra in range(len(features), len(flat)):
        flat[extra].set_visible(False)

    handles, labels = flat[0].get_legend_handles_labels()
    if handles:
        flat[0].legend(handles, labels, fontsize="small", framealpha=0.6)

    fig.tight_layout()
    suffix = "_centered" if centered else ""
    cls = "" if target is None else "_class_{}".format(target)
    name = "response_curves{}{}.png".format(suffix, cls)
    fig.savefig(os.path.join(plots_dir, name), dpi=110)
    plt.close(fig)
    return name


def hyperparameter_search(param_file):
    """Return a Markdown section summarizing the hyperparameter search."""
    import pandas as pd

    results = pd.read_csv(param_file)
    if "mean_test_score" not in results.columns:
        return None

    param_cols = [c for c in results.columns if c.startswith("param_")]
    keep = param_cols + ["mean_test_score", "std_test_score"]
    keep = [c for c in keep if c in results.columns]
    table = results[keep].sort_values("mean_test_score", ascending=False)

    lines = ["## Hyperparameter search", ""]
    lines.append(
        "Mean cross-validated score for each evaluated hyperparameter "
        "combination, best first. These are the results of the grid search "
        "performed during training. The best combination is the one with the "
        "highest `mean_test_score` (the tuning metric is Matthews correlation "
        "coefficient for classification and R-squared for regression; higher "
        "is better for both)."
    )
    lines.append("")
    best = table.iloc[0]
    best_params = ", ".join(
        "{} = {}".format(c.replace("param_", ""), best[c]) for c in param_cols
    )
    if best_params:
        lines.append("Best combination: {}.".format(best_params))
        lines.append("")
    ranked = table.head(10).reset_index(drop=True)
    ranked.index = ranked.index + 1
    lines.append(md_table(ranked, index_label="rank"))
    return "\n".join(lines)


def main():
    load_model = options["load_model"]
    classif_file = options["classif_file"]
    preds_file = options["preds_file"]
    fimp_file = options["fimp_file"]
    param_file = options["param_file"]
    training_file = options["training_file"]
    output = options["output"]
    title = options["title"]
    mode_option = options["mode"]
    curves = options["curves"]
    nprocs = int(options["nprocs"])
    centered = flags["c"]

    for path, key in (
        (load_model, "load_model"),
        (classif_file, "classif_file"),
        (preds_file, "preds_file"),
        (fimp_file, "fimp_file"),
        (param_file, "param_file"),
        (training_file, "training_file"),
    ):
        if path and not os.path.exists(path):
            gs.fatal(_("Input file for {} does not exist: {}").format(key, path))

    out_dir = os.path.dirname(output) or "."
    if not os.path.isdir(out_dir):
        gs.fatal(_("Directory for output file {} does not exist").format(output))

    stem = os.path.splitext(os.path.basename(output))[0]
    plots_rel = stem + "_plots"
    plots_dir = os.path.join(out_dir, plots_rel)

    try:
        import matplotlib as mpl

        mpl.use("Agg")
        make_plots = True
    except ImportError:
        gs.warning(
            _("matplotlib is not installed; the report will not include figures")
        )
        make_plots = False

    if make_plots:
        os.makedirs(plots_dir, exist_ok=True)

    sections = [
        "# {}".format(title),
        "",
        "Generated by *r.learn.report* on {}.".format(
            datetime.now().strftime("%Y-%m-%d %H:%M")
        ),
    ]

    # resolve the problem type: an explicit mode wins; otherwise take it from
    # the model, and fall back to the classification report or prediction
    # inference inside cv_performance.
    mode = None if mode_option == "auto" else mode_option

    if load_model:
        gs.message(_("Reading model ..."))
        detected, section = model_overview(load_model)
        sections.append(section)
        if mode is None:
            mode = detected
        elif mode != detected:
            gs.warning(
                _(
                    "Requested mode '{}' differs from the model type '{}'; "
                    "using the requested mode."
                ).format(mode, detected)
            )

    if mode is None and classif_file:
        mode = "classification"

    if preds_file:
        gs.message(_("Summarizing cross-validation performance ..."))
        sections.append(
            cv_performance(preds_file, mode, plots_dir, plots_rel, make_plots)
        )

    if classif_file:
        gs.message(_("Adding classification report ..."))
        sections.append(classification_table(classif_file))

    if fimp_file:
        gs.message(_("Adding feature importances ..."))
        sections.append(
            feature_importances(fimp_file, plots_dir, plots_rel, make_plots)
        )

    if training_file:
        if not load_model:
            gs.warning(
                _(
                    "training_file was given without load_model; response curves "
                    "need the fitted model and are skipped."
                )
            )
        else:
            gs.message(
                _(
                    "Computing response curves (this can be slow for large "
                    "ensembles) ..."
                )
            )
            section = response_curves(
                training_file,
                load_model,
                fimp_file,
                plots_dir,
                plots_rel,
                make_plots,
                curves,
                centered,
                nprocs,
            )
            if section is not None:
                sections.append(section)

    if param_file:
        gs.message(_("Summarizing hyperparameter search ..."))
        section = hyperparameter_search(param_file)
        if section is not None:
            sections.append(section)

    markdown_text = "\n\n".join(sections) + "\n"

    with open(output, "w") as fh:
        fh.write(markdown_text)

    gs.message(_("Report written to {}").format(output))
    if make_plots and os.listdir(plots_dir):
        gs.message(_("Figures written to {}").format(plots_dir))


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
