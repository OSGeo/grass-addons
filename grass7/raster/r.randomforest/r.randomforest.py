#!/usr/bin/env python
############################################################################
# MODULE:        r.randomforest
# AUTHOR:        Steven Pawley
# PURPOSE:       Supervised classification and regression of GRASS rasters
#                using the python scikit-learn package
#
# COPYRIGHT: (c) 2016 Steven Pawley, and the GRASS Development Team
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

#%module
#% description: Supervised classification and regression of GRASS rasters using the python scikit-learn package
#% keyword: classification
#% keyword: regression
#% keyword: machine learning
#% keyword: scikit-learn
#%end

#%option G_OPT_I_GROUP
#% key: igroup
#% label: Imagery group to be classified
#% description: Series of raster maps to be used in the random forest classification
#% required: yes
#% multiple: no
#%end

#%option G_OPT_R_INPUT
#% key: roi
#% label: Labelled pixels
#% description: Raster map with labelled pixels
#% required: no
#% guisection: Required
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% required: yes
#% label: Output Map
#% description: Prediction surface result from classification or regression model
#%end

#%option string
#% key: model
#% required: yes
#% label: Classifier
#% description: Supervised learning model to use
#% answer: RandomForestClassifier
#% options: LogisticRegression,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,GaussianNB,DecisionTreeClassifier,DecisionTreeRegressor,RandomForestClassifier,RandomForestRegressor,GradientBoostingClassifier,GradientBoostingRegressor,SVC
#%end

#%option double
#% key: c
#% description: Inverse of regularization strength (logistic regresson and SVC)
#% answer: 1.0
#% guisection: Classifier Parameters
#%end

#%option
#% key: max_features
#% type: integer
#% description: Number of features to consider during splitting for tree-based classifiers. Default -1 is sqrt(n_features) for classification, and n_features for regression
#% answer: -1
#% guisection: Classifier Parameters
#%end

#%option
#% key: max_depth
#% type: integer
#% description: Maximum tree depth for tree-based classifiers. Value of -1 uses classifier defaults
#% answer: -1
#% guisection: Classifier Parameters
#%end

#%option
#% key: min_samples_split
#% type: integer
#% description: The minimum number of samples required for node splitting in tree-based classifiers
#% answer: 2
#% guisection: Classifier Parameters
#%end

#%option
#% key: min_samples_leaf
#% type: integer
#% description: The minimum number of samples required to form a leaf node for tree-based classifiers
#% answer: 1
#% guisection: Classifier Parameters
#%end

#%option
#% key: n_estimators
#% type: integer
#% description: Number of estimators for tree-based classifiers
#% answer: 500
#% guisection: Classifier Parameters
#%end

#%option
#% key: learning_rate
#% type: double
#% description: learning rate for gradient boosting
#% answer: 0.1
#% guisection: Classifier Parameters
#%end

#%option
#% key: subsample
#% type: double
#% description: The fraction of samples to be used for fitting for gradient boosting
#% answer: 1.0
#% guisection: Classifier Parameters
#%end

# General options

#%flag
#% key: l
#% label: Use memory swap
#% guisection: Optional
#%end

#%flag
#% key: s
#% label: Standardization preprocessing
#% guisection: Optional
#%end

#%option
#% key: cv
#% type: integer
#% description: Number of cross-validation folds to perform in cv > 1
#% answer: 1
#% guisection: Optional
#%end

#%option string
#% key: cvtype
#% required: no
#% label: Non-spatial or spatial cross-validation
#% description: Non-spatial, clumped or clustered k-fold cross-validation
#% answer: Non-spatial
#% options: non-spatial,clumped,kmeans
#%end

#%option G_OPT_F_OUTPUT
#% key: errors_file
#% label: Save cross-validation global accuracy results to csv
#% required: no
#% guisection: Optional
#%end

#%option
#% key: random_state
#% type: integer
#% description: Seed to pass onto the random state for reproducible results
#% answer: 1
#% guisection: Optional
#%end

#%option
#% key: lines
#% type: integer
#% description: Processing block size in terms of number of rows
#% answer: 25
#% guisection: Optional
#%end

#%flag
#% key: p
#% label: Output class membership probabilities
#% guisection: Optional
#%end

#%flag
#% key: m
#% description: Build model only - do not perform prediction
#% guisection: Optional
#%end

#%flag
#% key: f
#% description: Calculate feature importances using bagging or univariate methods
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: fimp_file
#% label: Save feature importances to csv
#% required: no
#% guisection: Optional
#%end

#%flag
#% key: b
#% description: Balance number of observations by weighting for logistic regression, CART and RF methods
#% guisection: Optional
#%end

#%flag
#% key: h
#% description: Perform parameter tuning on a split of the training data
#% guisection: Optional
#%end

#%option
#% key: ratio
#% type: double
#% description: Percentage of training data to use for model development and tuning
#% answer: 0.25
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: save_training
#% label: Save training data to csv
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_INPUT
#% key: load_training
#% label: Load training data from csv
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: save_model
#% label: Save model from file
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_INPUT
#% key: load_model
#% label: Load model from file
#% required: no
#% guisection: Optional
#%end

#%rules
#% exclusive: roi,load_model
#% exclusive: save_training,load_training
#%end

# import standard modules
import atexit
import os
import numpy as np
from subprocess import PIPE

import grass.script as grass
from grass.pygrass.modules.shortcuts import imagery as im

from grass.pygrass.utils import set_path
set_path('r.randomforest')
from ml_utils import *
from ml_classifiers import model_classifiers

try:
    import pandas as pd
except:
    grass.fatal("Pandas not installed")

try:
    import sklearn
    from sklearn.externals import joblib
    from sklearn import metrics
    from sklearn import preprocessing

except:
    grass.fatal("Scikit learn is not installed")

# check for sklearn version
if (sklearn.__version__) < 0.18:
    grass.fatal("Scikit learn 0.18 or newer is required")


def cleanup():

    grass.run_command("g.remove", name='tmp_clfmask',
                      flags="f", type="raster", quiet=True)
    grass.run_command("g.remove", name='tmp_roi_clumped',
                      flags="f", type="raster", quiet=True)


def main():

    """
    GRASS options and flags
    -----------------------
    """

    # General options and flags
    igroup = options['igroup']
    roi = options['roi']
    output = options['output']
    model = options['model']
    norm_data = flags['s']
    cv = int(options['cv'])
    cvtype = options['cvtype']
    modelonly = flags['m']
    probability = flags['p']
    rowincr = int(options['lines'])
    random_state = int(options['random_state'])
    model_save = options['save_model']
    model_load = options['load_model']
    load_training = options['load_training']
    save_training = options['save_training']
    importances = flags['f']
    tuning = flags['h']
    lowmem = flags['l']
    ratio = float(options['ratio'])
    errors_file = options['errors_file']
    fimp_file = options['fimp_file']

    if flags['b'] is True:
        class_weight = 'balanced'
    else:
        class_weight = None

    # classifier options
    C = float(options['c'])
    min_samples_split = int(options['min_samples_split'])
    min_samples_leaf = int(options['min_samples_leaf'])
    n_estimators = int(options['n_estimators'])
    learning_rate = float(options['learning_rate'])
    subsample = float(options['subsample'])
    max_depth = int(options['max_depth'])
    max_features = int(options['max_features'])

    if max_features == -1:
        max_features = str('auto')
    if max_depth == -1:
        max_depth = None
        
    """
    Obtain information about GRASS rasters to be classified
    -------------------------------------------------------
    """

    Id = None

    # fetch individual raster names from group
    groupmaps = im.group(group=igroup, flags="g",
                         quiet=True, stdout_=PIPE).outputs.stdout

    maplist = groupmaps.split(os.linesep)
    maplist = maplist[0:len(maplist)-1]
    n_features = len(maplist)

    # Error checking for m_features settings
    if max_features > n_features:
        max_features = n_features

    """
    Sample training data using training ROI
    ---------------------------------------
    """

    # load or sample training data
    X, y, Id, clf = sample_training_data(roi, maplist, cv, cvtype, model_load,
                                         model_save, load_training,
                                         save_training, lowmem, random_state)
                            
                                         
    # determine the number of class labels using np.unique
    labels = np.unique(y)

    """
    Data preprocessing
    --------------------
    """
    if norm_data is True:
        scaler = preprocessing.StandardScaler().fit(X)
        X = scaler.transform(X)
    else:
        scaler = None

    """
    Train the classifier
    --------------------
    """

    # define classifier unless model is to be loaded from file
    if model_load == '':

        grass.message("Model=" + model)
        clf, param_grid, mode =\
            model_classifiers(model, random_state,
                              class_weight, C, max_depth,
                              max_features, min_samples_split,
                              min_samples_leaf, n_estimators,
                              subsample, learning_rate)

        # data splitting for automatic parameter tuning
        if tuning is True:
            X, X_devel, y, y_devel, Id, Id_devel, clf = \
                tune_split(X, y, Id, clf, param_grid, ratio, random_state)

            grass.message('\n')
            grass.message('Searched parameters:')
            grass.message(str(clf.param_grid))
            grass.message('\n')
            grass.message('Best parameters:')
            grass.message(str(clf.best_params_))

            clf = clf.best_estimator_

        """
        Cross Validation
        ----------------
        """

        # If cv > 1 then use cross-validation to generate performance measures
        if cv > 1:

            grass.message('\r\n')
            grass.message(
                "Cross validation global performance measures......:")

            # get metrics from kfold cross validation
            scores, y_test, y_pred = cross_val_classification(
                clf, X, y, Id, cv, random_state)

            if mode == 'classification':

                grass.message(
                    "Accuracy:\t%0.2f\t+/-SD\t%0.2f" %
                    (scores['accuracy'].mean(), scores['accuracy'].std()))

                # test for if binary and classes equal 0,1
                if len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
                    grass.message(
                        "ROC AUC :\t%0.2f\t+/-SD\t%0.2f" %
                        (scores['auc'].mean(), scores['auc'].std()))

                # classification report
                grass.message("\n")
                grass.message("Classification report:")
                grass.message(metrics.classification_report(y_test, y_pred))

                if errors_file != '':
                    errors = pd.DataFrame({'accuracy': scores['accuracy']})
                    errors.to_csv(errors_file, mode='w')

            else:
                grass.message("R2:\t%0.2f\t+/-\t%0.2f" %
                              (scores['r2'].mean(), scores['r2'].std()))

                if errors_file != '':
                    errors = pd.DataFrame({'r2': scores['accuracy']})
                    errors.to_csv(errors_file, mode='w')

        # train classifier
        clf.fit(X, y)
        y_pred = clf.predict(X)

        # check that all classes can be predicted
        # otherwise update labels with only predictable classes
        # otherwise the predicted probabilties will fail
        test = len(np.unique(y_pred)) == len(labels)
        if test is False:
            labels = np.unique(y_pred)

        """
        Feature Importances
        -------------------
        """

        if importances is True:

            clfimp = feature_importances(clf, X, y)

            # output to GRASS message
            grass.message("\r\n")
            grass.message("Normalized feature importances")
            grass.message("id" + "\t" + "Raster" + "\t" + "Importance")

            for i in range(len(clfimp)):
                grass.message(
                    str(i) + "\t" + maplist[i] +
                    "\t" + str(round(clfimp[i], 4)))

            if fimp_file != '':
                fimp_output = pd.DataFrame(
                    {'grass raster': maplist, 'importance': clfimp})
                fimp_output.to_csv(
                    path_or_buf=fimp_file,
                    header=['grass raster', 'importance'])

        """
        Save the fitted model
        ---------------------
        """

        if model_save != '':
            joblib.dump(clf, model_save + ".pkl")

        if modelonly is True:
            grass.fatal("Model built and now exiting")

    """
    Prediction on the rest of the GRASS rasters in the imagery group
    ----------------------------------------------------------------
    """

    prediction(clf, labels, maplist, scaler, probability,
               rowincr, output, mode)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
