## DESCRIPTION

*v.class.mlR* is a wrapper module that uses the R caret package for
machine learning in R to classify objects using training features by
supervised learning.

The user provides a set of objects (or segments) to be classified,
including all feature variables describing these object, and a set of
objects to be used as training data, including the same feature
variables as those describing the unknown objects, plus one additional
column indicating the class each training falls into. The training data
can, but does not have to be, a subset of the set of objects to be
classified.

The user can provide input either as vector maps (*segments\_map* and
*training\_map*, or as csv files (*segments\_file* and *training file*,
or a combination of both. Csv files have to be formatted in line with
the default output of [v.db.select](v.db.select.md), i.e. with a header.
The field separator can be set with the *separator* parameter. Output
can consist of either additional columns in the vector input map of
features, a text file (*classification\_results*) or reclassed raster
maps (*classified\_map*).

When using text file input, the training data should not contain an id
column. The object data (i.e., full set of data to be classified) should
have the ids in the first column.

The user has to provide the name of the column in the training data that
contains the class values (*train\_class\_column*), the prefix of the
columns that will contain the final class after classification
(*output\_class\_column*) as well as the prefix of the columns that will
contain the probability values linked to these classifications
(*output\_prob\_column* - see below).

Different classifiers are proposed *classifiers*: k-nearest neighbor
(knn), support vector machine with a radial kernel (svmRadial), support
vector machine with a linear kernel (svmLinear), random forest (rf),
C5.0 (C5.0) and XGBoost (xgbTree) decision trees and recursive
partitioning (rpart). Each of these classifiers is tuned automatically
through repeated cross-validation. Caret will automatically determine a
reasonable set of values for tuning. See the [caret
webpage](http://topepo.github.io/caret/modelList.html) for more
information about the tuning parameters for each classifier, and more
generally for the information about how caret works. By default, the
module creates 10 5-fold partitions for cross-validation and tests 10
possible values of the tuning parameters. These values can be changed
using, repectively, the *partitions*, *folds* and *tunelength*
parameters.

The user can define a customized tunegrid for each classifier, using the
*tunegrids* parameter. Any customized tunegrid has to be defined as a
Python dictionary, with the classifiers as keys, and the input to
expand.grid() as content as defined [in the caret
documentation](https://topepo.github.io/caret/model-training-and-tuning.html#alternate-tuning-grids).

For example, to define customized tuning grids for svmRadial and
RandomForest, the user can define the paramter as:  

```python
tunegrids="{'svmRadial': 'sigma=c(0.01,0.05,0.1), C=c(1,16,128)', 'rf': 'mtry=c(3,10,20)'}"
```

Tuning is potentially very time consuming. Using only a subset of the
training data for tuning can thus speed up the process significantly,
without losing much quality in the tuning results. For training,
depending on the number of features used, some R functions can reach
their capacity limit. The user can, therefore, define a maximum size of
samples per class both for tuning (*tuning\_sample\_size*) and for
training (*training\_sample\_size*).

Classifying using too many features (i.e. variables describing the
objects to be classified) as input can have negative effects on
classification accuracy (Georganos et al, 2018). The module therefore
provides the possibility to run a feature selection algorithm on the
training data in order to identify those features that are the most
efficient for classification. Using less features also speeds up the
tuning, training and classification processes. To activate feature
selection, the user has to set the *max\_features* parameter to the
maximum number of features that the model should select. Often, less
than this maximum will be selected. The method used for feature
selection is recursive feature elimination based on a random forest
model. Note thus that feature selection might be sub-optimal for other
classifiers, notably non tree-based.

The module can be run only for tuning and training a model, but without

Optionally, the module can be run for tuning and training only, i.e., no
prediction (*-t flag*). Any trained model can be saved to a file
(*output\_model\_file*) which can then be read into the module at a
later stage for the prediction step (*input\_model\_file*). This can be
particularly useful for cluster computing approaches where a trained
model can be applied to different datasets in parallel.

The module can run the model tuning using parallel processing. In order
for this to work, the R-package *doParallel* has to be installed. The
*processes* parameter allows to chose the number of processes to run.

The user can chose to include the individual classifiers results in the
output (the attributes and/or the raster maps) using the *i* flag, but
by default the output will be the result of a voting scheme merging the
results of the different classifiers. Votes can be weighted according to
a user-defined mode (*weighting\_mode*): simple majority vote without
weighting, i.e. all weights are equal (smv), simple weighted majority
vote (swv), best-worst weighted vote (bwwv) and quadratic best-worst
weighted vote (qbwwv). For more details about these voting modes see
Moreno-Seco et al (2006). By default, the weights are calculated based
on the accuracy metric, but the user can chose the kappa value as an
alternative (*weighting\_metric*).

In the output (as attribute columns or text file) each weighting schemes
result is provided accompanied by a value that can be considered as an
estimation of the probability of the classification after weighted vote,
based on equation (2) in Moreno et al (2006), page 709. At this stage,
this estimation does not, however, take into account the probabilities
determined individually by each classifier.

Optional output of the module include detailed information about the
different classifier models and their cross-validation results
*model\_details* (for details of these results see the train, resamples
and confusionMatrix.train functions in the caret package), a
box-and-whisker plot indicating the resampling variance based on the
cross-validation for each classifier (*bw\_plot\_file*), a csv file
containing accuracy measures (overall accuracy and kappa) for each
classifier (*accuracy\_file*), and a file containing variable importance
as determined by the classifier (for those classifiers that allow such
calculation). When the *-p* flag is given, the module also provides
probabilities per class for each classifier (at least for those where
caret can calculate such probabilities). This allows to evaluate the
confidence of classification of each object. The user can also chose to
write the R script constructed and used internally to a text file for
study or further modification.

## NOTES

The module can be used in a tool chain together with
[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html)
and the addon *i.segment.stats* for object-based classification of
satellite imagery.

*WARNING:* The option output files are created by R and currently no
checking is done of whether files of the same name already exist. If
they exist, they are silently overwritten, regardless of whether the
GRASS GIS *--o* flag is set or not.

The module makes no effort to check the input data for NA values or
anything else that might perturb the analyses. It is up to the user to
proceed to relevant checks before launching the module.

## DEPENDENCIES

This module uses R. It is the user's responsibility to make sure R is
installed and can be called from the environment this module is running
in. See the relevant [wiki
page](https://grasswiki.osgeo.org/wiki/R_statistics/Installation) for
more information. The module tries to install necessary R packages
automatically if necessary. These include : 'caret', 'kernlab', 'e1071',
'randomForest', and 'rpart'. Other packages can be necessary such as
'ggplot2', 'lattice' (for the plots), and 'doParallel' (if parallel
processing is desired).

## TODO

- Check for existing file created by R as no overwrite check is done
    in R
- Use class probabilities determined by individual classifiers to
    calculate overall class probabilities

## EXAMPLE

Using existing vector maps as input and writing the output to the
attribute table of the segments map, including the individual classifier
results:

```sh
v.class.mlR segments_map=seg training_map=training train_class_column=class weighting_mode=smv,swv,qbwwv -i
```

Using text files with segment characteristics as input and writing
output to raster files and a csv file

```sh
v.class.mlR segments_file=segstats.csv training_file=training.csv train_class_column=class weighting_mode=smv,swv,qbwwv raster_segments_map=seg classified_map=vote classification_results=class_results.csv
```

## REFERENCES

- Moreno-Seco, F. et al. (2006), Comparison of Classifier Fusion
    Methods for Classification in Pattern Recognition Tasks. In D.-Y.
    Yeung et al., eds. Structural, Syntactic, and Statistical Pattern
    Recognition. Lecture Notes in Computer Science. Springer Berlin
    Heidelberg, pp. 705–713, <https://doi.org/10.1007/11815921_77>.
- Georganos, S. et al (2018), Less is more: optimizing classification
    performance through feature selection in a very-high-resolution
    remote sensing object-based urban application, GIScience and Remote
    Sensing, 55:2, 221-242, DOI: 10.1080/15481603.2017.1408892

## SEE ALSO

*[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html),
[r.object.activelearning](r.object.activelearning.md),
[r.learn.ml](r.learn.ml.md)*

## AUTHOR

Moritz Lennert, Université Libre de Bruxelles (ULB) based on an initial
R-script by Ruben Van De Kerchove, also ULB at the time
