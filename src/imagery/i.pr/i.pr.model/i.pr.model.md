## DESCRIPTION

Create a classification model from a feature file. The type of model created
is chosen by setting one of the flags **g** (gaussian mixture),
**n** (nearest neighbor), **t** (classification trees), and **s** (support
vector machines). There are also general parameters such as the features
file (**features**), the name of the file produced containing the
model (**model**), the name of an additional features file
on which to calculate prediction values ​​during the training phase
(**validation**), the name of an additional features file on which
to calculate prediction values ​​in addition to the training set (**test**),
and the number of principal components to use in the model (**npc**) if
these are present in the features.

Then there are specific model parameters. None for the Gaussian mixture.
The number of neighbors per nearest neighbor (**nn\_k**), although this
parameter is only used for model evaluation since the model itself is
the data itself. For classification trees, you can decide whether to
create single-node trees (stamps) or not (**tree\_stamps**),
or decide how much data at least one node must contain to be split
(**tree\_minsize** parameter). Furthermore, the tree costs parameter
allows you to unbalance the classes (rpart style).

For support vector machines, the user must set the kernel type
(**svm\_kernel**, which can assume the values ​​*linear*, *gaussian*
and *2pbk*), the kernel size if it is gaussian (**svm\_kp**), the
regularization parameter (**svm\_c**), the convergence parameters
**svm\_eps**, tolerance (**svm\_tol**) and **svm\_maxloops**.
It is suggested not to modify the first two while the maximum number of
optimization loops can be modified (always with care). For support vector
machines, it is possible to calculate an estimate of the leave-one-out
model error using the parameter **svm\_l1o**. The output of the procedure
is a file containing the selected model. The standard output will
describe the performance of the model on the training set and optionally
on a test set. For support vector machines, an optional cross-validation
estimate is also available.

For classification trees and support vector machines, model combinations
(bagging and boosting). The number of models is chosen by the user
(bagging and boosting parameters respectively). A cost-sensitive version
is also available for boosting, with the cost boosting parameter. If
boosting is used, it is possible to obtain the dynamics of the boosted
weights using the weights boosting parameter. For tree boosting, it is
also possible to develop (this is experimental) a soft version of the
model with the soft margin boosting parameter.

A cost-sensitive version for the single support vector machine can be
obtained using the svm cost parameter. It is also possible to use a
regularized version of the AdaBoost algorithm by specifying the number of
intervals (**reg**) into which to divide the misclassification ratio
(hence the number of training sets generated). In this case, the
validation set is not available. Alternatively, it is possible to
manually choose the misclassification ratio value above which samples
are eliminated from the training set (misclass ratio parameter). For
some models, only binary classifications are implemented according to
the following list:

- gaussian mixture: multiclass
- nearest neighbor: multiclass
- classification trees: multiclass
- support vector machines: binary
- bagging classification trees: multiclass
- boosting classification trees: binary
- bagging support vector machines: binary
- boosting support vector machines: binary

## AUTHORS

Stefano Merler, FBK, Trento, Italy
