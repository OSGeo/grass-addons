#!/usr/bin/env python
############################################################################
# MODULE:       r.randomforest
# AUTHOR:       Steven Pawley
# PURPOSE:      Supervised classification and regression of GRASS rasters using the 
#               python scikit-learn package
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
#% options: LogisticRegression,LinearDiscriminantAnalysis,QuadraticDiscriminantAnalysis,DecisionTreeClassifier,DecisionTreeRegressor,RandomForestClassifier,RandomForestRegressor,GradientBoostingClassifier,GradientBoostingRegressor,GaussianNB
#%end

# Logistic regression options

#%option double
#% key: c_lr
#% description: Inverse of regularization strength
#% answer: 1.0
#% guisection: Logistic Regression
#%end

#%flag
#% key: i
#% description: Fit intercept in logistic regression
#% guisection: Logistic Regression
#%end

# Decision tree options
#%option string
#% key: splitter_dt
#% description: The strategy used to choose the split at each node
#% answer: best
#% options: best,random
#% guisection: Decision Tree
#%end

#%option
#% key: m_features_dt
#% type: integer
#% description: The number of features to consider when looking for the best split. Default -1 is sqrt(n_features) for classification, and n_features for regression
#% answer: -1
#% guisection: Decision Tree
#%end

#%option
#% key: min_samples_split_dt
#% type: integer
#% description: The minimum number of samples required to split an internal node
#% answer: 2
#% guisection: Decision Tree
#%end

#%option
#% key: min_samples_leaf_dt
#% type: integer
#% description: The minimum number of samples required to be at a leaf node
#% answer: 1
#% guisection: Decision Tree
#%end

#%option
#% key: min_weight_fraction_leaf_dt
#% type: integer
#% description: The minimum weighted fraction of the input samples required to be at a leaf node
#% answer: 0
#% guisection: Decision Tree
#%end

# Random Forest Options

#%option
#% key: ntrees_rf
#% type: integer
#% description: Number of trees in the forest
#% answer: 500
#% guisection: Random Forest
#%end

#%option
#% key: m_features_rf
#% type: integer
#% description: The number of features allowed at each split. Default -1 is sqrt(n_features) for classification, and n_features for regression
#% answer: -1
#% guisection: Random Forest
#%end

#%option
#% key: minsplit_rf
#% type: integer
#% description: The minimum number of samples required to split a node
#% answer: 2
#% guisection: Random Forest
#%end

# Gradient tree boosting options

#%option
#% key: learning_rate_gtb
#% type: double
#% description: learning rate shrinks the contribution of each tree
#% answer: 0.1
#% guisection: Gradient Boosted Trees
#%end

#%option
#% key: n_estimators_gtb
#% type: integer
#% description: The number of boosting stages to perform
#% answer: 100
#% guisection: Gradient Boosted Trees
#%end

#%option
#% key: max_depth_gtb
#% type: integer
#% description: The maximum depth limits the number of nodes in the tree
#% answer: 3
#% guisection: Gradient Boosted Trees
#%end

#%option
#% key: min_samples_split_gtb
#% type: integer
#% description: The minimum number of samples required to split an internal node
#% answer: 2
#% guisection: Gradient Boosted Trees
#%end

#%option
#% key: min_samples_leaf_gtb
#% type: integer
#% description: The minimum number of samples required to be at a leaf node
#% answer: 1
#% guisection: Gradient Boosted Trees
#%end

#%option
#% key: min_weight_fraction_leaf_gtb
#% type: double
#% description: The minimum weighted fraction of the input samples required to be at a leaf node
#% answer: 0.
#% guisection: Gradient Boosted Trees
#%end

#%option
#% key: subsample_gtb
#% type: double
#% description: The fraction of samples to be used for fitting the individual base learners
#% answer: 1.0
#% guisection: Gradient Boosted Trees
#%end

#%option
#% key: max_features_gtb
#% type: integer
#% description: The number of features to consider during splitting. Default -1 is sqrt(n_features) for classification mode, and n_features for regression mode
#% answer: -1
#% guisection: Gradient Boosted Trees
#%end

# General options

#%option
#% key: cv
#% type: integer
#% description: Use k-fold cross-validation when cv > 1
#% answer: 1
#% guisection: Optional
#%end

#%option
#% key: randst
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

#%option
#% key: ncores
#% type: integer
#% description: Number of processing cores. Default -1 is all cores
#% answer: -1
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
#% description: Output feature importances for ensemble tree-based models
#% guisection: Optional
#%end

#%flag
#% key: b
#% description: Balance number of observations by weighting for logistic regression and tree-based classifiers
#% guisection: Optional
#%end

#%flag
#% key: l
#% description: Low memory version - samples predictors row-by-row (slower)
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: savefile
#% label: Save model from file
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_INPUT
#% key: loadfile
#% label: Load model from file
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_OUTPUT
#% key: save_training
#% label: Save training data to csv file
#% required: no
#% guisection: Optional
#%end

#%option G_OPT_F_INPUT
#% key: load_training
#% label: Load training data from file
#% required: no
#% guisection: Optional
#%end

#%rules
#% exclusive: roi,loadfile
#% exclusive: roi,load_training
#% exclusive: save_training,load_training
#%end



# import standard modules
import atexit, random, string, re, os
import numpy as np
from subprocess import PIPE

import grass.script as grass
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.modules.shortcuts import imagery as im



def cleanup():

    grass.run_command("g.remove", name='clfmasktmp', flags="f",
                      type="raster", quiet=True)



def sample_predictors_byrow(response, predictors):

    """
    Samples a list of GRASS rasters using a labelled raster
    Row-by-row sampling
    
    Parameters
    ----------
    response: String; GRASS raster with labelled pixels
    predictors: List of GRASS rasters containing explanatory variables

    Returns
    -------
    
    training_data: Numpy array of extracted raster values
    training_labels: Numpy array of labels
    
    """

    # create response rasterrow and open
    roi_raster = RasterRow(response)
    roi_raster.open('r')
    
    # create a list of rasterrow objects
    # Then each GRASS rasterrow can be referred to by rastack[band][row]:
    n_features = len(predictors)
    rasstack = [0] * n_features
    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() == True:
            rasstack[i].open('r')
        else:
            grass.fatal("GRASS raster " + maplist[i] +
                        " does not exist.... exiting")
        
    # use grass.pygrass.gis.region to get information about the current region
    current = Region()

    # determine cell storage type of training roi raster
    roi_type = grass.read_command("r.info", map=response, flags='g')
    roi_list = str(roi_type).split(os.linesep)
    dtype = roi_list[9].split('=')[1]

    # Count number of labelled pixels
    roi_stats = str(grass.read_command("r.univar", flags=("g"), map=response))
    roi_stats = roi_stats.split(os.linesep)[0]
    nlabel_pixels = int(str(roi_stats).split('=')[1])

    # Create a zero numpy array with the dimensions of the number of columns
    # and the number of bands plus an additional band to attach the labels
    tindex = 0
    training_labels = []
    training_data = np.zeros((nlabel_pixels, n_features+1))
    training_data[:] = np.NAN

    # Loop through each row of the raster
    for row in range(current.rows):
        # get the pixels from that row in the ROI raster
        roi_row_np = roi_raster[row]

        # check if any of those pixels are labelled (not equal to nodata)
        # can use even if roi is FCELL because nodata will be nan and this is

        # not returned anyway
        is_train = np.nonzero(roi_row_np > -2147483648)
        training_labels = np.append(training_labels, roi_row_np[is_train])
        nlabels_in_row = np.array(is_train).shape[1]

        # if there are any labelled pixels
        # loop through each imagery band for that row and put the data into

        # the img_row_band_np array
        if np.isnan(roi_row_np).all() != True:

            for band in range(n_features):
                imagerow_np = rasstack[band][row]

                # attach the label values onto the last column
                training_data[tindex : tindex+nlabels_in_row, band] =\
                    imagerow_np[is_train]

            tindex = tindex + nlabels_in_row

    # attach training label values onto last dimension of numpy array
    training_data[0:nlabel_pixels, n_features] = training_labels

    # convert any CELL maps no data vals to NaN in the training data
    for i in range(n_features):
        training_data[training_data[:, i] == -2147483648] = np.nan

    # Remove nan rows from training data
        training_data = training_data[~np.isnan(training_data).any(axis=1)]

    # Split the numpy array into training_labels and training_data arrays
    training_labels = training_data[:, n_features]
    training_data = training_data[:, 0:n_features]

    # close maps
    roi_raster.close()
    
    for i in range(n_features):
        rasstack[i].close()
    
    return(training_data, training_labels)



def sample_predictors(response, predictors):
    
    """
    Samples a list of GRASS rasters using a labelled raster
    Per raster sampling
    
    Parameters
    ----------
    response: String; GRASS raster with labelled pixels
    predictors: List of GRASS rasters containing explanatory variables

    Returns
    -------
    
    training_data: Numpy array of extracted raster values
    training_labels: Numpy array of labels
    
    """
    
    # open response raster as rasterrow and read as np array
    if RasterRow(response).exist() == True:
        roi_gr = RasterRow(response)
        roi_gr.open('r')
        response_np = np.array(roi_gr)
    else:
        grass.fatal("GRASS response raster does not exist.... exiting")

    # check to see if all predictors exist
    n_features = len(predictors)
    
    for i in range(n_features):
        if RasterRow(predictors[i]).exist() != True:
            grass.fatal("GRASS raster " + predictors[i]
                        + " does not exist.... exiting")

    # check if any of those pixels are labelled (not equal to nodata)
    # can use even if roi is FCELL because nodata will be nan and this is not
    # returned anyway
    is_train = np.nonzero(response_np > -2147483648)
    training_labels = response_np[is_train]
    n_labels = np.array(is_train).shape[1]

    # Create a zero numpy array of len training labels and n_features+1 for y
    training_data = np.zeros((n_labels, n_features+1))

    # Loop through each raster and sample pixel values at training indexes
    for f in range(n_features):
        predictor_gr = RasterRow(predictors[f])
        predictor_gr.open('r')
        feature_np = np.array(predictor_gr)
        training_data[0:n_labels, f] = feature_np[is_train]
        predictor_gr.close()
    
    # attach training labels to last column
    training_data[0:n_labels, n_features] = training_labels

    # convert any CELL maps no datavals to NaN in the training data
    for i in range(n_features):
        training_data[training_data[:, i] == -2147483648] = np.nan

    # Remove nan rows from training data
    training_data = training_data[~np.isnan(training_data).any(axis=1)]
    roi_gr.close()
    
    # return X and y data
    return(training_data[:, 0:n_features], training_data[:, n_features])



def prediction(clf, predictors, class_probabilities,
               rowincr, output, mode):
    
    """
    Prediction on list of GRASS rasters using a fitted scikit learn model
    
    Parameters
    ----------
    clf: Scikit learn estimator object
    predictors: List of paths to GDAL rasters that represent the predictor variables
    output: Name of GRASS raster to output classification results
    rowincr: Integer of raster rows to process at one time
    class_probabilties: Boolean of whether probabilities of each class should also be predicted
    mode: String, classification or regression mode
    labels: Numpy array of the labels used for the classification
    
    """
    
    # create a list of rasterrow objects for predictors
    n_features = len(predictors)
    rasstack = [0] * n_features
    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() == True:
            rasstack[i].open('r')
        else:
            grass.fatal("GRASS raster " + maplist[i]
                        + " does not exist.... exiting")
    
    # use grass.pygrass.gis.region to get information about the current region
    current = Region()
    
    # create a imagery mask
    # the input rasters might have different dimensions and non-value pixels.
    # r.series used to automatically create a mask by propagating the nulls
    clfmask = 'clfmasktmp'
    grass.run_command("r.series", output=clfmask,
                      input=predictors, method='count', flags='n')

    mask_raster = RasterRow(clfmask)
    mask_raster.open('r')
    
    # create and open RasterRow objects for classification
    classification = RasterRow(output)
    if mode == 'classification':
        ftype = 'CELL'
        nodata = -2147483648
    else:
        ftype = 'FCELL'
        nodata = np.nan
    classification.open('w', ftype, overwrite=True)
    
    # create and open RasterRow objects for  probabilities if enabled
    if class_probabilities == True:
        prob_out_raster = [0] * nclasses
        prob = [0] * nclasses
        for iclass in range(nclasses):
            prob_out_raster[iclass] = output + \
                '_classPr' + str(int(class_list[iclass]))
            prob[iclass] = RasterRow(prob_out_raster[iclass])
            prob[iclass].open('w', 'FCELL', overwrite=True)

    """
    Prediction using row blocks
    """
            
    for rowblock in range(0, current.rows, rowincr):
        # check that the row increment does not exceed the number of rows
        if rowblock+rowincr > current.rows:
            rowincr = current.rows - rowblock
        img_np_row = np.zeros((rowincr, current.cols, n_features))
        mask_np_row = np.zeros((rowincr, current.cols))

        # loop through each row, and each band

        # and add these values to the 2D array img_np_row
        for row in range(rowblock, rowblock+rowincr, 1):
            mask_np_row[row-rowblock, :] = np.array(mask_raster[row])
            for band in range(n_features):
                img_np_row[row-rowblock, :, band] = \
                    np.array(rasstack[band][row])

        mask_np_row[mask_np_row == -2147483648] = np.nan
        nanmask = np.isnan(mask_np_row) # True in the mask means invalid data

        # reshape each row-band matrix into a list
        nsamples = rowincr * current.cols
        flat_pixels = img_np_row.reshape((nsamples, n_features))

        # remove NaN values and perform the prediction
        flat_pixels = np.nan_to_num(flat_pixels)
        result = clf.predict(flat_pixels)
        result = result.reshape((rowincr, current.cols))

        # replace NaN values so that the prediction does not have a border
        result = np.ma.masked_array(result, mask=nanmask, fill_value=np.nan)

        # return a copy of result, with masked values filled with a value
        result = result.filled([nodata])

        # for each row we can perform computation, and write the result into
        for row in range(rowincr):
            newrow = Buffer((result.shape[1],), mtype=ftype)
            newrow[:] = result[row, :]
            classification.put_row(newrow)

        # same for probabilities
        if class_probabilities == True and mode == 'classification':
            result_proba = clf.predict_proba(flat_pixels)

            for iclass in range(result_proba.shape[1]):
                result_proba_class = result_proba[:, iclass]
                result_proba_class = \
                    result_proba_class.reshape((rowincr, current.cols))
                    
                result_proba_class = \
                    np.ma.masked_array(result_proba_class,
                                       mask=nanmask, fill_value=np.nan)
                result_proba_class = result_proba_class.filled([np.nan])

                for row in range(rowincr):
                    newrow = Buffer((result_proba_class.shape[1],),
                                     mtype='FCELL')
                    newrow[:] = result_proba_class[row, :]
                    prob[iclass].put_row(newrow)

    classification.close()
    mask_raster.close()

    if class_probabilities == True and mode == 'classification':
        for iclass in range(nclasses): prob[iclass].close()



def shuffle_data(X, y, rstate):

    """
    Uses scikit learn to shuffle data
    
    Parameters
    ----------
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    rstate: Seed for random generator
    
    Returns
    -------
    X: Numpy array containing predictor values
    y: Numpy array containing labels

    """

    from sklearn.utils import shuffle

    # combine XY data into a single numpy array
    XY = np.empty((X.shape[0], X.shape[1]+1))
    XY[:,0] = y
    XY[:,1:] = X
    
    XY = shuffle(XY, random_state=rstate)

    # split XY into train_xs and train_y
    X = XY[:,1:]
    y = XY[:,0]
    
    return(X, y)



def cross_val_classification(clf, X, y, cv, rstate):
    
    """
    Stratified Kfold cross-validation
    Generates several scoring_metrics without the need to repeatedly use cross_val_score
    Also produces by-class scores
    
    Parameters
    ----------
    clf: Scikit learn estimator object
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    cv: Integer of cross-validation folds
    rstate: Seed to pass to the random number generator
    
    Returns
    -------
    cmstats: Dictionary of global accuracy measures per fold
    byclass_metrics: Dictionary of by-class accuracy measures per fold

    """
    
    from sklearn import cross_validation, metrics
    
    class_list = np.unique(y)
    nclasses = len(np.unique(y))
    
    # Store performance measures per class
    byclass_metrics = {
        'precision': np.zeros((nclasses, cv)),
        'recall': np.zeros((nclasses, cv)),
        'f1': np.zeros((nclasses, cv))
    }
    
    # generate Kfold indices
    k_fold = cross_validation.StratifiedKFold(y, n_folds=cv,
                                              shuffle=False,
                                              random_state=rstate)

    # dictionary of lists to store metrics
    cmstats = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': [],
        'kappa': [],
        'auc': []
    }

    # loop through each fold
    fold=0
    for train_indices, test_indices in k_fold:

        X_train, X_test =  X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]

        # fit the model on the training data and predict the test data
        fit = clf.fit(X_train, y_train)
        y_pred = fit.predict(X_test)

        # calculate metrics
        cmstats['accuracy'] = np.append(cmstats['accuracy'],
                                        metrics.accuracy_score(y_test, y_pred))

        cmstats['precision'] = np.append(cmstats['precision'],
                                         metrics.precision_score(y_test,
                                                                 y_pred,
                                                                 average='weighted'))


        cmstats['recall'] = np.append(cmstats['recall'],
                                     metrics.recall_score(y_test, y_pred,
                                                          average='weighted'))

        cmstats['f1'] = np.append(cmstats['f1'],
                                  metrics.f1_score(y_test, y_pred,
                                                   average='weighted'))

        cmstats['kappa'] = np.append(cmstats['kappa'],
                                     metrics.cohen_kappa_score(y_test, y_pred))

        # test for if binary and classes equal 0,1
        if len(np.unique(y)) == 2 and all ([0,1] == np.unique(y)):
            
            stat_method = "binary"
            
            y_pred_proba = fit.predict_proba(X_test)[:,1]
            cmstats['auc'] = np.append(cmstats['auc'],
                                       metrics.roc_auc_score(y_test,
                                                             y_pred_proba))
        else:
            stat_method = "micro"
        
        # Get performance measures by class     
        for cindex in range(nclasses):
            byclass_metrics['recall'][cindex, fold] = \
                metrics.recall_score(y_test, y_pred, labels =
                                    [class_list[cindex]],
                                    pos_label=class_list[cindex], average = stat_method)

            byclass_metrics['precision'][cindex, fold] = \
                metrics.precision_score(y_test, y_pred, labels =
                                        [class_list[cindex]],
                                        pos_label=class_list[cindex], average = stat_method)

            byclass_metrics['f1'][cindex, fold] = \
                metrics.f1_score(y_test, y_pred, labels =
                                [class_list[cindex]],
                                pos_label=class_list[cindex], average = stat_method)
        fold+=1
        
    return(cmstats, byclass_metrics)

def save_training_data(X, y, file):

    """
    Saves any extracted training data to a csv file
    
    Parameters
    ----------
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    file: Path to a csv file to save data to

    """

    training_data = np.zeros((y.shape[0], X.shape[1]+1))
    training_data[:, 0:X.shape[1]] = X
    training_data[:, X.shape[1]] = y
    np.savetxt(file, training_data, delimiter = ',')



def load_training_data(file):
    
    """
    Loads training data and labels from a csv file
    
    Parameters
    ----------
    file: Path to a csv file to save data to
    
    Returns
    -------
    X: Numpy array containing predictor values
    y: Numpy array containing labels

    """
    
    training_data = np.loadtxt(file, delimiter = ',')
    n_features = training_data.shape[1]
    X = training_data[:, 0:n_features-1]
    y = training_data[:, n_features-1]
    
    return(X, y)

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
    cv = int(options['cv'])
    modelonly = flags['m']
    class_probabilities = flags['p']
    rowincr = int(options['lines'])
    randst = int(options['randst'])
    model_save = options['savefile']
    model_load = options['loadfile']
    save_training = options['save_training']
    load_training = options['load_training']
    importances = flags['f']
    weighting = flags['b']
    lowmem = flags['l']
    ncores = int(options['ncores'])

    # logistic regression
    c_lr = float(options['c_lr'])
    fi = flags['i']
    
    # decision trees
    splitter_dt = options['splitter_dt']
    m_features_dt = int(options['m_features_dt'])
    min_samples_split_dt = int(options['min_samples_split_dt'])
    min_samples_leaf_dt = int(options['min_samples_leaf_dt'])
    min_weight_fraction_leaf_dt = float(options['min_weight_fraction_leaf_dt'])
    
    # random forests
    ntrees_rf = int(options['ntrees_rf'])
    m_features_rf = int(options['m_features_rf'])
    minsplit_rf = int(options['minsplit_rf'])
    
    # gradient tree boosting
    learning_rate_gtb = float(options['learning_rate_gtb'])
    n_estimators_gtb = int(options['n_estimators_gtb'])
    max_depth_gtb = int(options['max_depth_gtb'])
    min_samples_split_gtb = int(options['min_samples_split_gtb'])
    min_samples_leaf_gtb = int(options['min_samples_leaf_gtb'])
    min_weight_fraction_leaf_gtb = float(options['min_weight_fraction_leaf_gtb'])
    subsample_gtb = float(options['subsample_gtb'])
    max_features_gtb = int(options['max_features_gtb'])
    
    # classification or regression
    if model == 'LogisticRegression' \
    or model == 'DecisionTreeClassifier' \
    or model == 'RandomForestClassifier' \
    or model == 'GradientBoostingClassifier' \
    or model == 'GaussianNB' \
    or model == 'LinearDiscriminantAnalysis' \
    or model == 'QuadraticDiscriminantAnalysis':
        mode = 'classification'
    else:
        mode = 'regression'


    """
    Error checking for valid input parameters
    -----------------------------------------
    """

    # decision trees
    if model == 'DecisionTreeClassifier' or model == 'DecisionTreeRegressor':
        if m_features_dt == -1:
            m_features_dt = str('auto')
        if m_features_dt == 0:
            grass.fatal("m_features_dt must be greater than zero, or -1 which uses the sqrt(nfeatures)...exiting")
        if min_samples_split_dt < 1:
            grass.fatal("min_samples_split_dt must be >=1.....exiting")
        if min_samples_leaf_dt < 1:
            grass.fatal("min_samples_leaf_dt must be >=1.....exiting")

    # random forests
    if model == 'RandomForestClassifier' or model == 'RandomForestRegressor':
        if m_features_rf == -1:
            m_features_rf = str('auto')
        if m_features_rf == 0:
            grass.fatal("mfeatures must be greater than zero, or -1 which uses the sqrt(nfeatures)...exiting")
        if minsplit_rf < 1:
            grass.fatal("minsplit must be greater than zero.....exiting")
        if ntrees_rf < 1:
            grass.fatal("ntrees must be greater than zero.....exiting")

    # gradient tree boosting
    if model == 'GradientBoostingClassifier' or model == 'GradientBoostingRegressor':
        if n_estimators_gtb < 1:
            grass.fatal("n_estimators_gtb must be greater than zero...exiting")
        if max_depth_gtb < 1:
            grass.fatal("max_depth_gtb must be greater than zero...exiting")
        if min_samples_split_gtb < 1:
            grass.fatal("min_samples_split_gtb must be greater than zero...exiting")
        if min_samples_leaf_gtb < 1:
            grass.fatal("min_samples_leaf_gtb must be greater than zero...exiting")
        if max_features_gtb == -1:
            max_features_gtb = str('auto')
        if max_features_gtb == 0:
            grass.fatal("max_features_gtb must be greater than zero, or -1 which uses the sqrt(nfeatures)...exiting")

    # general options
    if rowincr <= 0:
        grass.fatal("rowincr must be greater than zero....exiting")
    if model_save != '' and model_load != '':
        grass.fatal("Cannot save and load a model at the same time.....exiting")
    if model_load == '' and roi == '':
        grass.fatal("Require labelled pixels regions of interest.....exiting")
    if weighting == True:
        weighting = 'balanced'
    else:
        weighting = None


    """
    Obtain information about GRASS rasters to be classified
    -------------------------------------------------------
    """
    
    # fetch individual raster names from group
    groupmaps = im.group(group=igroup, flags="g",
                         quiet = True, stdout_=PIPE).outputs.stdout
                         
    maplist = groupmaps.split(os.linesep)
    maplist = maplist[0:len(maplist)-1]
    n_features = len(maplist)

    # use grass.pygrass.gis.region to get information about the current region
    current = Region()

    # lazy import of sklearn
    try:
        from sklearn.externals import joblib
        import warnings
        warnings.filterwarnings("ignore")
    except:
        grass.fatal("Scikit-learn python module is not installed...exiting")


    """
    Sample training data using training ROI
    ---------------------------------------
    """
    
    # load the model or training data
    if model_load != '':
        clf = joblib.load(model_load)
    else:
        if load_training != '':
            X, y = load_training_data(load_training)
        else:
            # query predictor rasters with training features
            if lowmem != True:
                X, y = sample_predictors(roi, maplist)
            else:
                X, y = sample_predictors_byrow(roi, maplist)
            
            # shuffle the training data
            X, y = shuffle_data(X, y, rstate=randst)
            
            # use GRASS option to save the training data
            if save_training != '': save_training_data(X, y, save_training)

        # determine the number of class labels using np.unique
        nclasses = len(np.unique(y))
        class_list = np.unique(y)
    
    # Error checking for m_features settings
    if m_features_dt > n_features: m_features_dt = n_features
    if m_features_rf > n_features: m_features_rf = n_features
    if max_features_gtb > n_features: max_features_gtb = n_features


    """
    Train the classifier
    --------------------
    """

    # define classifier unless model is to be loaded from file
    if model_load == '':
        
        # classifiers
        from sklearn.linear_model import LogisticRegression
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.naive_bayes import GaussianNB
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
        
        from sklearn.neighbors import KNeighborsRegressor
        from sklearn.tree import DecisionTreeRegressor
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.ensemble import GradientBoostingRegressor
        
        classifiers = {
            'LogisticRegression': LogisticRegression(C=c_lr, fit_intercept=fi, n_jobs=ncores, class_weight=weighting),
            'DecisionTreeClassifier': DecisionTreeClassifier(splitter=splitter_dt,
                                                             max_features=m_features_dt,
                                                             min_samples_split=min_samples_split_dt,
                                                             min_samples_leaf=min_samples_leaf_dt,
                                                             min_weight_fraction_leaf=min_weight_fraction_leaf_dt,
                                                             random_state=randst,
                                                             class_weight=weighting),
            'DecisionTreeRegressor': DecisionTreeRegressor(splitter=splitter_dt,
                                                           max_features=m_features_dt,
                                                           min_samples_split=min_samples_split_dt,
                                                           min_samples_leaf=min_samples_leaf_dt,
                                                           min_weight_fraction_leaf=min_weight_fraction_leaf_dt,
                                                           random_state=randst),
            'RandomForestClassifier': RandomForestClassifier(n_estimators=ntrees_rf,
                                                             oob_score=True,
                                                             max_features=m_features_rf,
                                                             min_samples_split=minsplit_rf,
                                                             random_state=randst,
                                                             n_jobs=ncores,
                                                             class_weight=weighting),
            'RandomForestRegressor': RandomForestRegressor(n_jobs=ncores,
                                                           n_estimators=ntrees_rf,
                                                           oob_score=False,
                                                           max_features=m_features_rf,
                                                           min_samples_split=minsplit_rf,
                                                           random_state=randst),
            'GradientBoostingClassifier': GradientBoostingClassifier(learning_rate=learning_rate_gtb,
                                                                     n_estimators=n_estimators_gtb,
                                                                     max_depth=max_depth_gtb,
                                                                     min_samples_split=min_samples_split_gtb,
                                                                     min_samples_leaf=min_samples_leaf_gtb,
                                                                     min_weight_fraction_leaf=min_weight_fraction_leaf_gtb,
                                                                     subsample=subsample_gtb,
                                                                     max_features=max_features_gtb,
                                                                     random_state=randst),
            'GradientBoostingRegressor': GradientBoostingRegressor(learning_rate=learning_rate_gtb,
                                                                   n_estimators=n_estimators_gtb,
                                                                   max_depth=max_depth_gtb,
                                                                   min_samples_split=min_samples_split_gtb,
                                                                   min_samples_leaf=min_samples_leaf_gtb,
                                                                   min_weight_fraction_leaf=min_weight_fraction_leaf_gtb,
                                                                   subsample=subsample_gtb,
                                                                   max_features=max_features_gtb,
                                                                   random_state=randst),
            'GaussianNB': GaussianNB(),
            'LinearDiscriminantAnalysis': LinearDiscriminantAnalysis(),
            'QuadraticDiscriminantAnalysis': QuadraticDiscriminantAnalysis(),
        }
        
        # define classifier
        clf = classifiers[model]
        
        # train classifier
        clf.fit(X, y)
        grass.message(_("Model built with: " + model))
        
        
        """
        Cross Validation
        ----------------
        """

        # output internal performance measures for random forests
        if model == 'RandomForestClassifier':
            grass.message(_("\r\n"))
            grass.message(_('RF OOB prediction  accuracy: \t %0.3f' %
                            (clf.oob_score_ * 100)))
        if model == 'RandomForestRegressor':
            grass.message(_("\r\n"))
            grass.message(_('Coefficient of determination R^2: \t %0.3f' %
                         (clf.score(X=training_data, y=training_labels))))
       
        # If cv > 1 then use cross-validation to generate performance measures
        if cv > 1:
            from sklearn.cross_validation import cross_val_predict, cross_val_score
            from sklearn.metrics import classification_report

            grass.message(_('\r\n'))
            grass.message(_("Cross validation global performance measures......:"))

            if mode == 'classification':
                # get metrics from kfold cross validation
                cmstats, byclass_stats = cross_val_classification(clf, X, y, cv, randst)
                
                grass.message(_("Accuracy                  :\t%0.2f\t+/-SD\t%0.2f" \
                    %(cmstats['accuracy'].mean(), cmstats['accuracy'].std())))
                grass.message(_("Kappa                     :\t%0.2f\t+/-SD\t%0.2f" \
                    % (cmstats['kappa'].mean(), cmstats['kappa'].std())))
                grass.message(_("Precision weighted average:\t%0.2f\t+/-SD\t%0.2f" \
                    % (cmstats['precision'].mean(), cmstats['precision'].std())))
                grass.message(_("Recall weighted average   :\t%0.2f\t+/-SD\t%0.2f" \
                    % (cmstats['recall'].mean(), cmstats['recall'].std())))
                grass.message(_("f1 weighted average       :\t%0.2f\t+/-SD\t%0.2f" \
                    % (cmstats['f1'].mean(), cmstats['f1'].std())))
                
                # test for if binary and classes equal 0,1
                if len(np.unique(y)) == 2 and all ([0,1] == np.unique(y)):
                    grass.message(_("ROC AUC                   :\t%0.2f\t+/-SD\t%0.2f"\
                        % (cmstats['auc'].mean(), cmstats['auc'].std())))
                
                # calculate scores by class
                grass.message(_("\r\n"))
                grass.message(_("Performance measures by class......:"))
                grass.message(_("Cla\tRecall\t2SD \tPrecision\t2SD\tf1  \tSD"))

                byclass_scores = ['recall', 'precision', 'f1']
                
                for i in range(nclasses):
                    row = str(int(class_list[i])) + '\t'
                    for method in byclass_scores:
                        row += ('%.2f' % byclass_stats[method][i, :].mean() ) +\
                        '\t' + ('%.2f' % byclass_stats[method][i, :].std() ) + '\t'
                    grass.message(_(row))
                
            else:
                r2 = cross_val_score(clf, X, y, cv=cv, scoring='r2', n_jobs=ncores)
                grass.message(_("R2:\t%0.2f\t+/-\t%0.2f" % (r2.mean(), r2.std() * 2)))
                
        # diagnostics
        if importances == True:
            if (model == 'RandomForestClassifier' or 
                model == 'GradientBoostingClassifier' or
                model == 'RandomForestRegressor' or
                model == 'GradientBoostingRegressor' or
                model == 'DecisionTreeClassifier' or
                model == 'DecisionTreeRegressor'):
                    
                    clfimp = clf.feature_importances_
                    grass.message(_("\r\n"))
                    grass.message(_("Feature importances"))
                    grass.message(_("id" + "\t" + "Raster" + "\t" + "Importance"))
                    
                    for i in range(len(clfimp)):
                         grass.message(_(str(i) + "\t" + maplist[i]
                                         + "\t" + str(round(clfimp[i], 4))))
        
        # save the model
        if model_save != '':
            joblib.dump(clf, model_save + ".pkl")
        
        if modelonly == True:
            grass.fatal("Model built and now exiting")


    """
    Prediction on the rest of the GRASS rasters in the imagery group
    ----------------------------------------------------------------
    """
    
    prediction(clf, maplist, class_probabilities, rowincr, output, mode)
    

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
