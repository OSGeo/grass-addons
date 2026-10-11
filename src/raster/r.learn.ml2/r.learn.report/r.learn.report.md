## DESCRIPTION

*r.learn.report* creates a report using the outputs of *r.learn.train* and
*r.learn.assembly*. It takes a fitted model and the optional cross-validation,
feature-importance and hyperparameter CSV files that those tools can write, and
produces a document with short explanations, summary tables and figures.

The report is written as Markdown. Figures are saved as PNG files in a
directory next to the report, named after it (for `report.md` the directory is
`report_plots`), and referenced from the document with relative paths, so the
report and its figure directory should be kept together.

Every input is optional; the report contains a section for each input that is
supplied, so the same tool serves a quick model summary and a full report:

- **load_model** adds a *Model* section describing the estimator, its
  predictors, and, for an ensemble from *r.learn.assembly*, the base models
  with their voting weights or the learned stacking coefficients.
- **preds_file** (cross-validation predictions) adds a *Cross-validation
  performance* section with per-fold score summaries and a confusion matrix
  (classification) or a predicted-versus-observed plot (regression).
- **classif_file** adds a *Per-class performance* table.
- **fimp_file** adds a *Variable contributions* section with a permutation
  feature-importance table and bar chart.
- **param_file** adds a *Hyperparameter search* section with the best
  combination and the ranked grid-search results (not available for
  r.learn.assembly).
- **training_file** adds a *Response curves* section with a partial-dependence
  panel per predictor, showing how the prediction changes as that predictor is
  varied. This also needs **load_model**.

## NOTES

The figures require *matplotlib* (see `requirements.txt`). If *matplotlib* is
missing, the report is still written with its tables but without figures.

Feature names for the *Variable contributions* section come from the
**fimp_file**, as the saved model does not retain them.

The type of model (classification or regression) is taken from the model when
**load_model** is given. When no model is supplied, it is guessed from the
predictions. As this is unreliable, it is better to set the **mode** option
explicitly.

The permutation feature importances written by *r.learn.train* and
*r.learn.assembly* are computed on the training data, not on an independent
validation set, so they describe how the fitted model uses each predictor
rather than how it generalizes. The performance drop is measured with the
model's tuning metric (Matthews correlation coefficient for classification,
R-squared for regression).

The *Response curves* section draws partial-dependence curves. For each
predictor, it uses the predicted outcome as that predictor is varied across its
range (5th to 95th percentile) while the other predictors are marginalized over
the training data. By default, each panel also shows the individual conditional
expectation (ICE) curves of the samples. If you only want the average curves,
set **curves** to `pdp`. The section needs both the fitted model
(**load_model**) and the extracted training data saved with the `save_training`
option of *r.learn.train* or *r.learn.assembly* (**training_file**). A
classification model produces one figure per class. Note that where predictors
are strongly correlated, parts of a curve can reach into predictor combinations
that do not occur in the data. So interpret those regions with care. Curves
cannot be drawn for an estimator that provides no class probabilities, such as a
hard-voting ensemble.

## EXAMPLES

Train a model and build a report from its outputs:

```sh
# train, writing the cross-validation, importance and training-data outputs
r.learn.train group=predictors training_points=training_pts field=class \
    model_name=RandomForestClassifier save_model=model.gz cv=5 \
    preds_file=preds.csv classif_file=classif.csv -f fimp_file=fimp.csv \
    save_training=training.csv

# assemble the report, including response curves from the training data
r.learn.report load_model=model.gz preds_file=preds.csv \
    classif_file=classif.csv fimp_file=fimp.csv training_file=training.csv \
    output=report.md
```

Report an ensemble model with a custom title:

```sh
r.learn.report load_model=ensemble.gz preds_file=preds.csv \
    classif_file=classif.csv output=report.md \
    title="Land cover ensemble"
```

## SEE ALSO

*[r.learn.assembly](r.learn.assembly.md)*,
*[r.learn.ml2](r.learn.ml2.md)*,
*[r.learn.predict](r.learn.predict.md)*,
*[r.learn.train](r.learn.train.md)*

## AUTHORS

[Paulo van Breugel](https://ecodiv.earth), [HAS green
academy](https://has.nl), [Innovative Biomonitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/),
[Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)

Built on the *r.learn.ml2* toolset by Steven Pawley.
