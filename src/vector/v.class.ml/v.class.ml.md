## DESCRIPTION

**v.class.ml** uses machine-learning algorithms to classify a vector
maps based on the values of its attribute table. The module uses
different machine-learning libraries available for python at the moment
uses: [scikit-learn](https://scikit-learn.org/) (package name may be
"python-scikit-learn") and [MLPY](https://mlpy.sourceforge.net/), but
should be possible to add easily other python libraries. The module is
though to be use in a modular way, using the flags it is possible to
define which independent tasks should be execute.

### Flags:

- **-e**  
    Extract the training set from a vector map (vtraining).
- **-n**  
    Store: attribute table data, columns names, categories training
    data, training index to a numpy binary files.
- **-f**  
    Rank feature importances using a
    [ExtraTreesClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.ExtraTreesClassifier.html)
    algorithm.
- **-b**  
    Balance the training using the class with the minor number of
    training samples or the parameter set in n\_training.
- **-o**  
    Optimize a balanced training dataset using the class with the minor
    number of training samples or the parameter set in n\_training.
- **-c**  
    Classify the whole dataset.
- **-r**  
    Export machine-learning results to raster maps.
- **-t**  
    Test several machine-learning algorithms on your dataset.
- **-v**  
    Test also the bias variance.
- **-x**  
    Compute also extra parameters to evaluate different algorithms like:
    confusion matrix, ROC, PR.
- **-d**  
    Explore the Support Vector Classification (SVC) domain.

### Input parameters:

The *vector* parameter is the input vector map. The input vector map
must be prepared with
[v.category](https://grass.osgeo.org/grass-stable/manuals/grass.osgeo.org/grass-stable/manuals/v.category.html)
to copy the categories to all the layers that will be created.

The *vtraining* parameter is a vector input map that can be used to
select the training areas. Currently only supervised classification is
implemented so this parameter is mandatory. The training vector map can
be generated using the GRASS standard tool for supervised classification
[g.gui.iclass](https://grass.osgeo.org/grass-stable/manuals/g.gui.iclass.html).

The *vlayer* parameter is the layer name or number of the attribute
tables with the data that must be used as input for the machine-learning
algorithms.

The *tlayer* parameter is the layer name or number of the attribute
tables where are or will be stored the training data for the
machine-learning algorithms.

The *rlayer* parameter is the layer name or number the attribute tables
where will be stored the machine-learning results.

The *npy\_data* parameter is a string with the path to define where the
binary [numpy](http://www.numpy.org//) files containing the complete
dataset will be saved.

The *npy\_cats* parameter is a string with the path to define where the
binary numpy files containing the vector categories will be saved.

The *npy\_cols* parameter is a string with the path to define where the
binary numpy files containing the column names of the data attribute
table will be saved.

The *npy\_index* parameter is a string with the path to define where the
binary numpy files containing a boolean array to say if the category is
used or not as training.

The *npy\_tdata* parameter is a string with the path to define where the
binary numpy files containing a training data array will be saved.

The *npy\_tclasses* parameter is a string with the path to define where
the binary numpy files containing the training classes will be saved.

The *npy\_btdata* parameter as npy\_tdata but only for a balance
dataset.

The *npy\_btclasses* parameter as npy\_tclasses but only for a balance
dataset.

The *imp\_csv* parameter is a string with the path to define where a CSV
file containing the rank of the feature importances should be save.

The *imp\_fig* parameter is a string with the path to define where a
figure file containing the rank of the feature importances should be
save.

The *scalar* parameter is a string with scaler methods that will be
apply to pre-process the data. Two main methods are available:
with\_mean, with\_std. This is a quite common task therefore the default
parameter apply both methods.

The *decomposition* parameter is a string with scaler methods that will
be apply to pre-process the data. The main decomposition methods
available are:
[PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html),
[KernelPCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.KernelPCA.html),
[ProbabilisticPCA](https://web.archive.org/web/20150621181931/https://scikit-learn.org/0.14/modules/generated/sklearn.decomposition.ProbabilisticPCA.html),
[RandomizedPCA](https://scikit-learn.org/0.17/modules/generated/sklearn.decomposition.RandomizedPCA.html),
[FastICA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.FastICA.html),
[TruncatedSVD](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html).
Each of this methods could take several parameters. Use "|" as separator
between the decomposition method name and its options, using the "," to
separate the options. For examples imagine that we want to decompose
using the KernelPCA method with 10 number of components and using a
linear kernel, so the correct string is:
"KernelPCA|n\_components=10,kernel=linear"

The *n\_training* parameter is an integer with the number of training
that must be use per class. Some machine-learning methods are sensitive
if the training dataset is balanced or not. As default all the training
will be used.

The *pyclassifiers* parameter is a file path to a python file containing
a list of dictionary to define classifiers class and options. See an
example of the [default
classifiers](https://github.com/OSGeo/grass-addons/blob/grass8/src/vector/v.class.ml/ml_classifiers.py)
used by the **v.class.ml** module.

The *pyvar* parameter is a string with the python variable name defined
in the pyclassifiers file.

The *pyindx* parameter is a string with the indexes of the classifiers
that will be used. In the string you could define a range using the
minus character, or list the index usig the comma as separator, or
combine both options together. For example: '1-5,34-36,40' it means that
only classifiers with index: 1, 2, 3, 4, 5, 34, 35, 36 and 40 will be
used.

The *pyindx\_optimize* parameter is a integer with the classifier index
that will be used to optimize a balance training dataset. This option is
used only if optimize is true otherwise will be ignored.

The *nan* parameter is a string that allows user to define for each
column in the attribute table which value or function should be used to
substitute NaN values. The syntax could be: 'col0:9999,col1:9999'. The
column name could be also a pattern, so it is possible to define a rule
like: '\*\_mean:nanmean,\*\_max:nanmax' that substitute in all the
columns that finish with '\_mean' the mean value of the column and for
column that end with '\_max' the maximum value. This operation is needed
because machine-learning algorithms are not able to handle nan, inf,
neginf, and posinf values.

The *inf* parameter is similar to nan, but instead of substituting nan
values the rules will be applied for infinite values.

The *neginf* parameter is similar to nan, but instead of substituting
nan values the rules will be applied for negative infinite values.

The *posinf* parameter is similar to nan, but instead of substituting
nan values the rules will be applied for positive infinite values.

The *csv\_test\_cls* parameter is the file name/path where the results
of the classification test will be written.

The *report\_class* parameter is the file name/path where a summary for
each machine learning algorithms will be written.

The *svc\_c\_range* parameter is a range of C values that will be used
when exploring the domain of the Support Vector Machine algorithms.

The *svc\_gamma\_range* parameter is a range of gamma values that will
be used when exploring the domain of the Support Vector Machine
algorithms.

The *svc\_kernel\_range* parameter is a range of kernel values that will
be used when exploring the domain of the Support Vector Machine
algorithms.

The *svc\_n\_jobs* parameter is an integer with the number of process
that will be used during the domain exploration of Support Vector
Machine algorithms.

The *svc\_img* parameter is the file name/path pattern of the image that
will be generated from the domain exploration.

The *svc\_c* parameter is the definitive C value that will be used for
final classification.

The *svc\_gamma* parameter is the definitive gamma value that will be
used for final classification.

The *svc\_kernel* parameter is the definitive kernel value that will be
used for final classification.

The *rst\_names* parameter is the name pattern that will be use to
generate the output raster map for each algorithm.

## SEE ALSO

*[v.class.mlpy](v.class.mlpy.md)* (a simpler module for vector
classification which uses *mlpy*)

## AUTHOR

Pietro Zambelli, University of Trento
