## DESCRIPTION

*r.learn.assembly* combines several machine learning algorithms from the
scikit-learn package into a single ensemble model and trains it on the predictor
rasters of an imagery group, using labelled pixels or training points as the
response. It is a companion to *r.learn.train*, which trains one estimator at a
time. The fitted ensemble model can be used in *r.learn.predict* like a model
from *r.learn.train*. 

Two ensemble strategies are supported through the **ensemble_type** option:

- **voting** combines predictions from multiple base models using fixed weights
  (equal by default, or specified by the user). For classification,
  voting='soft' averages the predicted class probabilities, while voting='hard'
  selects the class receiving the most (weighted) votes. For regression, a
  (weighted) average of the model predictions is used.
- **stacking** combines predictions from the base models into a single
  prediction. A second-level model (meta-learner) is trained on their
  cross-validated predictions to learn how best to combine them. This approach
  aims to exploit the strengths of different models and improve overall
  predictive performance. For more information, see
  [Stacked generalization](https://scikit-learn.org/stable/modules/ensemble.html#stacking).
  The meta-model coefficients reported after training are the fitted
  coefficients of the meta-learner, not normalized per-model weights: a base
  model can contribute several inputs (one per class in multiclass problems)
  and the coefficients can be negative, so they are not directly comparable to
  the fixed voting weights.

Both strategies work for classification and for regression, as long as every
base model in the configuration is of the same kind (all classifiers or all
regressors). Note that soft voting requires classifiers that support probability
predictions (predict_proba), ideally with well-calibrated probabilities.

### Two-step workflow

The base models and their parameters are supplied in a JSON configuration file,
while the shared settings (ensemble type, weighting, cross-validation,
preprocessing) are module options. A typical run therefore has two steps.

1. **Write a configuration template.** Select the base models with the
   **models** option and a path with **write_config**. The module writes a
   JSON file with one entry per model, each listing the estimator's parameters
   filled with their scikit-learn default values, and exits:

   ```sh
   r.learn.assembly models=RandomForestClassifier,SVC,KNeighborsClassifier \
       write_config=ensemble.json
   ```

2. **Edit and run.** Adjust the parameters and (for voting) the weights in
   `ensemble.json`, then pass it back with the **config** option together with
   the training data and the shared settings:

   ```sh
   r.learn.assembly config=ensemble.json group=predictors \
       training_points=training_pts field=class ensemble_type=stacking \
       cv=5 inner_cv=5 save_model=ensemble.gz
   ```

### Configuration file format

The configuration is a JSON object with one entry per base model. Each key is
a free label used to identify the model in the ensemble and in the report;
each value gives the estimator name, an optional voting **weight**, and the
estimator parameters. For example:

```json
{
  "rf":  {"estimator": "RandomForestClassifier", "weight": 2.0,
          "params": {"n_estimators": 500, "max_features": "sqrt"}},
  "svc": {"estimator": "SVC", "weight": 1.0,
          "params": {"C": 10.0, "kernel": "rbf"}},
  "knn": {"estimator": "KNeighborsClassifier", "weight": 1.0,
          "params": {"n_neighbors": 7}}
}
```

Parameters that are not listed keep the estimator's default; parameters not
valid for an estimator are ignored with a warning. The `weight` field is used
only for voting ensembles and ignored for stacking. The seed (**random_state**)
and the number of cores (**n_jobs**) are taken from the module options and
should not be set in the file.

### Cross-validation

Two independent cross-validation settings are offered:

- **cv** is the *outer* cross-validation that reports the performance of the
  whole ensemble. With **cv** greater than 1, the module prints global accuracy
  measures, a per-class report (classification), and the cross-validated score
  of each base model on its own, so the ensemble can be compared with its
  members. The per-class report and the cross-validation predictions can be
  written to CSV with **classif_file** and **preds_file**.
- **inner_cv** is used only by stacking, as the internal cross-validation that
  produces the out-of-fold base-model predictions on which the meta-model is
  trained. It has no effect for the voting.

When a **group_raster** is provided by the user, samples sharing a group id are
kept together in the same cross-validation fold. This allows for spatial
cross-validation, which provides a more robust estimate of the predictive
performance of the (ensemble) model. Note that grouping is applied only to the
**outer** cross-validation (**cv**). The internal stacking cross-validation
(**inner_cv**) does not currently keep groups together, so the meta-model is
trained on out-of-fold predictions that may share spatial groups across folds.

## NOTES

Base-model hyperparameters are taken as given from the configuration file. There
is no option to tune them using gridsearch. To choose good values, tune each
candidate model on its own with *r.learn.train*, which performs a grid search
when a hyperparameter is given a comma-separated list of values, and reports the
best combination. The recommended workflow is:

1. tune each candidate with *r.learn.train*, e.g.
   `r.learn.train ... model_name=RandomForestClassifier n_estimators=100,300,500 max_depth=5,10,20 param_file=rf.csv`,
   and note the reported best parameters;
2. write a template with `r.learn.assembly models=... write_config=ensemble.json`;
3. transcribe the tuned values into `ensemble.json`;
4. train the ensemble with `r.learn.assembly config=ensemble.json ...`.

*r.learn.predict* can output class probabilities, which requires the model to
provide `predict_proba`. Hard voting does not, so use soft voting or stacking
if probability output is needed.

The **-b** flag balances imbalanced classes by weighting samples inversely to
their class frequencies (classification only). The weights are passed to every
base model during fitting, so it can only be used when all base models support
sample weights. The module checks this and reports any that do not. Estimators
such as *KNeighborsClassifier*, *LinearDiscriminantAnalysis*,
*QuadraticDiscriminantAnalysis* and *MLPClassifier* do not support sample
weights.

The **-f** flag computes permutation feature importances of the fitted
ensemble, saved to **fimp_file** and usable by *r.learn.report*. As in
*r.learn.train*, importances are computed on the training data (not an
independent validation set) using the tuning score (Matthews correlation
coefficient for classification, R-squared for regression), so they describe how
the model uses each predictor rather than how it generalizes.

## EXAMPLES

Train a stacking classifier from three base models and apply it to the
imagery group:

```sh
# 1. write a template for the chosen base models
r.learn.assembly models=RandomForestClassifier,SVC,KNeighborsClassifier \
    write_config=ensemble.json

# 2. (edit ensemble.json), then train with 5-fold outer cross-validation
r.learn.assembly config=ensemble.json group=predictors \
    training_points=training_pts field=class ensemble_type=stacking \
    cv=5 inner_cv=5 classif_file=report.csv save_model=ensemble.gz

# 3. apply the fitted ensemble to the rasters
r.learn.predict group=predictors load_model=ensemble.gz output=classification
```

Train a weighted voting regressor, standardizing the predictors first (the
**voting** option applies to classification only and is ignored for
regression, where the predictions are averaged):

```sh
r.learn.assembly config=ensemble_reg.json group=predictors \
    training_points=training_pts field=measurement ensemble_type=voting \
    cv=5 save_model=ensemble_reg.gz -s
```

## REFERENCES

Buitinck, L., Louppe, G., Blondel, M., Pedregosa, F., Mueller, A., Grisel, O.,
Niculae, V., Prettenhofer, P., Gramfort, A., Grobler, J., Layton, R.,
VanderPlas, J., Joly, A., Holt, B., & Varoquaux, G. (2013). API design for
machine learning software: Experiences from the scikit-learn project. ECML PKDD
Workshop: Languages for Data Mining and Machine Learning, 108–122.

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O.,
Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos,
A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011).
Scikit-learn: Machine Learning in Python. Journal of Machine Learning Research,
12(Oct), 2825–2830.


## SEE ALSO

*[r.learn.ml2](r.learn.ml2.md)*,
*[r.learn.predict](r.learn.predict.md)*,
*[r.learn.train](r.learn.train.md)*

scikit-learn documentation on
[ensemble methods](https://scikit-learn.org/stable/modules/ensemble.html).

## AUTHORS

[Paulo van Breugel](https://ecodiv.earth), [HAS green
academy](https://has.nl), [Innovative Biomonitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/),
[Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)

Built on the *r.learn.ml2* toolset by Steven Pawley.
