## DESCRIPTION

*r.learn.train* performs training data extraction, supervised machine
learning and cross-validation using the python package *scikit learn*.
The choice of machine learning algorithm is set using the *model\_name*
parameter. For more details relating to the classifiers, refer to the
[scikit learn documentation](https://scikit-learn.org/stable/). The
training data can be provided either by a GRASS raster map containing
labelled pixels using the *training\_map* parameter, or a GRASS vector
dataset containing point geometries using the *training\_points*
parameter. If a vector map is used then the *field* parameter also needs
to indicate which column in the vector attribute table contains the
labels/values for training.

For regression models the *field* parameter must contain only numeric
values. For classification models the field can contain integer-encoded
labels, or it can represent text categories that will automatically be
encoded as integer values (in alphabetical order). These text labels
will also be applied as categories to the classification output when
using **r.learn.predict**. The vector map should also not contain
multiple geometries per attribute.

### Supervised Learning Algorithms

The following classification and regression methods are available:

| Model                                                                                                                | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| LogisticRegression, LinearRegression                                                                                 | Linear models for classification and regression                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| SGDClassifier, SGDRegressor                                                                                          | Linear models for classification and regression using stochastic gradient descent optimization suitable for large datasets. Supports l1, l2 and elastic net regularization                                                                                                                                                                                                                                                                                                                                                                                |
| LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis                                                            | Classifiers with linear and quadratic decision surfaces                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| KNeighborsClassifier, KNeighborsRegressor                                                                            | Local approximation methods for classification/regression that assign predictions to new observations based on the values assigned to the k-nearest observations in the training data feature space                                                                                                                                                                                                                                                                                                                                                       |
| GaussianNB                                                                                                           | Gaussian Naive Bayes algorithm and can be used for classification                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| DecisionTreeClassifier DecisionTreeRegressor                                                                         | Classification and regression tree models that map observations to a response variable using a hierarchy of splits and branches. The terminus of these branches, termed leaves, represent the prediction of the response variable. Decision trees are non-parametric and can model non-linear relationships between a response and predictor variables, and are insensitive the scaling of the predictors                                                                                                                                                 |
| RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier, ExtraTreesRegressor                             | Ensemble classification and regression tree methods. Each tree in the ensemble is based on a random subsample of the training data. Also, only a randomly-selected subset of the predictors are available during each node split. Each tree produces a prediction and the final result is obtained by averaging across all of the trees. The ExtraTreesClassifier and ExtraTreesRegressor are variant on random forests where during each node split, the splitting rule that is selected is based on the best of a several randomly-generated thresholds |
| GradientBoostingClassifier, GradientBoostingRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor | Ensemble tree models where learning occurs in an additive, forward step-wise fashion where each additional tree fits to the model residuals to gradually improve the model fit. HistGradientBoostingClassifier and HistGradientBoostingRegressor are the new scikit learn multithreaded implementations.                                                                                                                                                                                                                                                  |
| SVC, SVR                                                                                                             | Support Vector Machine classifiers and regressors. Only a linear kernel is enabled in r.learn.ml2 because non-linear kernels are too slow for most remote sensing and spatial datasets                                                                                                                                                                                                                                                                                                                                                                    |
| MLPClassifier, MLPRegressor                                                                                          | Multi-layer perceptron algorithm for classification or regression                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

### Hyperparameters

The estimator settings tab provides access to the most pertinent
parameters that affect the previously described algorithms. The
scikit-learn estimator defaults are generally supplied, and these
parameters can be tuned using a grid-search by inputting multiple
comma-separated parameters. The grid search is performed using a 3-fold
cross validation. This tuning can also be accomplished simultaneously
with nested cross-validation by settings the *cv* option to \> 1.

The following table summarizes the hyperparameter and which models they
apply to:

| Hyperparameter     | Description                                                                                                                                                                      | Method                                                                                                                                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| alpha              | The constrant used to multiply the regularization term                                                                                                                           | SGDClassifier, SGDRegressor, MLPClassifier, MLPRegressor                                                                                                                                                       |
| l1\_ratio          | The elastic net mixing ration between l1 and l2 regularization                                                                                                                   | SGDClassifier, SGDRegressor                                                                                                                                                                                    |
| c                  | Inverse of the regularization strength                                                                                                                                           | LogisticRegression, SVC, SVR                                                                                                                                                                                   |
| epsilon            | Width of the margin used to maximize the number of fitted observations                                                                                                           | SVR                                                                                                                                                                                                            |
| n\_estimators      | The number of trees                                                                                                                                                              | RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier, ExtraTreesRegressor, GradientBoostingClassifier, GradientBoostingRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor |
| max\_features      | The number of predictor variables that are randomly selected to be available at each node split                                                                                  | RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier, ExtraTreesRegressor, GradientBoostingClassifier, GradientBoostingRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor |
| min\_samples\_leaf | The number of samples required to split a node                                                                                                                                   | RandomForestClassifier, RandomForestRegressor, ExtraTreesClassifier, ExtraTreesRegressor, GradientBoostingClassifier, GradientBoostingRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor |
| learning\_rate     | Shrinkage parameter to control the contribution of each tree                                                                                                                     | GradientBoostingClassifier, GradientBoostingRegressor, HistGradientBoostingClassifier, HistGradientBoostingRegressor                                                                                           |
| hidden\_units      | The number of neurons in each hidden layer, e.g. (100;100) for 100 neurons in two hidden layers. Tuning can be performed using comma-separated values, e.g. (100;100),(200;200). | MLPClassifier, MLRRegressor                                                                                                                                                                                    |

### Preprocessing

Although tree-based classifiers are insensitive to the scaling of the
input data, other classifiers such as linear models may not perform
optimally if some predictors have variances that are orders of magnitude
larger than others. The *-s* flag adds a standardization preprocessing
step to the classification and prediction to reduce this effect.
Additionally, most of the classifiers do not perform well if there is a
large class imbalance in the training data. Using the *-b* flag balances
the training data by weighting of the minority classes relative to the
majority class. This does not apply to the Naive Bayes or
LinearDiscriminantAnalysis classifiers.

Scikit learn does not specifically recognize raster predictors that
represent non-ordinal, categorical values, for example if using a
landcover map as a predictor. Predictive performances may be improved if
the categories in these maps are one-hot encoded before training. The
parameter *categorical\_maps* can be used to select rasters that in
contained within the imagery group to apply one-hot encoding before
training.

### Feature Importances

In addition to model fitting and prediction, feature importances can be
generated using the **-f** flag. The feature importances method uses a
permutation-based method can be applied to all the estimators. The
feature importances represent the average decrease in performance of
each variable when permuted. For binary classifications, the AUC is used
as the metric. Multiclass classifications use accuracy, and regressions
use R2.

### Cross-Validation

Cross validation can be performed by setting the *cv* parameters to \>

1. Cross-validation is performed using stratified k-folds for
classification and k-folds for regression. Several global and per-class
accuracy measures are produced depending on whether the response
variable is binary or multiclass, or the classifier is for regression or
classification. Cross-validation can also be performed in groups by
supplying a raster containing the group\_ids of the partitions using the
*group\_raster* option. In this case, training samples with the same
group id as set by the group\_raster will never be split between
training and test partitions during cross-validation. This can reduce
problems with overly optimistic cross-validation scores if the training
data are strongly spatially correlated, i.e. the training data represent
rasterized polygons.

## NOTES

Many of the estimators involve a random process which can causes a small
amount of variation in the classification/regression results and and
feature importances. To enable reproducible results, a seed is supplied
to the estimator. This can be changed using the *randst* parameter.

For convenience when repeatedly training models on the same data, the
training data can be saved to a csv file using the *save\_training*
option. This data can then imported into subsequent classification runs,
saving time by avoiding the need to repeatedly query the predictors.

## EXAMPLE

Here we are going to use the GRASS GIS sample North Carolina data set as
a basis to perform a landsat classification. We are going to classify a
Landsat 7 scene from 2000, using training information from an older
(1996) land cover dataset.

Landsat 7 (2000) bands 7,4,2 color composite example:

![image-alt](lsat7_2000_b742.png)

Note that this example must be run in the "landsat" mapset of the North
Carolina sample data set location.

First, we are going to generate some training pixels from an older
(1996) land cover classification:

```sh
g.region raster=landclass96 -p
r.random input=landclass96 npoints=1000 raster=training_pixels
```

Then we can use these training pixels to perform a classification on the
more recently obtained landsat 7 image:

```sh
# train a random forest classification model using r.learn.train
r.learn.train group=lsat7_2000 training_map=training_pixels \
    model_name=RandomForestClassifier n_estimators=500 save_model=rf_model.gz

# perform prediction using r.learn.predict
r.learn.predict group=lsat7_2000 load_model=rf_model.gz output=rf_classification

# check raster categories - they are automatically applied to the classification output
r.category rf_classification

# copy color scheme from landclass training map to result
r.colors rf_classification raster=training_pixels
```

Random forest classification result:

![image-alt](rfclassification.png)

## SEE ALSO

[r.learn.ml2](r.learn.ml2.md) (overview),
[r.learn.predict](r.learn.predict.md)

## REFERENCES

Scikit-learn: Machine Learning in Python, Pedregosa et al., JMLR 12, pp.
2825-2830, 2011.

## AUTHOR

Steven Pawley
