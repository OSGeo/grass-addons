## DESCRIPTION

*r.learn.report* creates a report using the outputs of *r.learn.train* and
*r.learn.assembly*. It takes a fitted model and the optional cross-validation,
feature-importance and hyperparameter CSV files that those tools can write, and
produces a single document with short explanations, summary tables and figures.

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
  combination and the ranked grid-search results.

## NOTES

The figures require *matplotlib* (see `requirements.txt`). If *matplotlib* is
missing, the report is still written with its tables but without figures.

Feature names for the *Variable contributions* section come from the
**fimp_file**, as the saved model does not retain them.

The problem type (classification or regression) is taken from the model when
**load_model** is given. Otherwise it is guessed from the predictions, which is
unreliable: a regression with few distinct integer responses can look like a
classification, and a classification with many classes like a regression. When
no model is supplied, set the **mode** option explicitly to avoid the wrong
metrics and figure being produced.

The permutation feature importances written by *r.learn.train* and
*r.learn.assembly* are computed on the training data, not on an independent
validation set, so they describe how the fitted model uses each predictor
rather than how it generalizes. The performance drop is measured with the
model's tuning metric (Matthews correlation coefficient for classification,
R-squared for regression).

A full description of the training workflow (all model parameters, preprocessing
settings, sample counts, random seed, class balancing, scikit-learn version)
cannot be reconstructed from the inputs alone; only what the fitted model and
CSV files record is included.

## EXAMPLES

Train a model and build a report from its outputs:

```sh
# train, writing the cross-validation and importance outputs
r.learn.train group=predictors training_points=training_pts field=class \
    model_name=RandomForestClassifier save_model=model.gz cv=5 \
    preds_file=preds.csv classif_file=classif.csv -f fimp_file=fimp.csv

# assemble the report
r.learn.report load_model=model.gz preds_file=preds.csv \
    classif_file=classif.csv fimp_file=fimp.csv output=report.md
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
