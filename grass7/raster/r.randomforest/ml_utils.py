import os
import numpy as np
import grass.script as grass
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.buffer import Buffer
from sklearn.model_selection import StratifiedKFold
from sklearn import metrics
from sklearn.model_selection import GroupKFold
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn import preprocessing
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
from sklearn.utils import shuffle

from sklearn.externals import joblib
from grass.pygrass.modules.shortcuts import raster as r
from sklearn.cluster import KMeans


def save_training_data(X, y, groups, file):

    """
    Saves any extracted training data to a csv file

    Parameters
    ----------
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels
    file: Path to a csv file to save data to

    """

    # if there are no group labels, create a nan filled array
    if groups is None:
        groups = np.empty((y.shape[0]))
        groups[:] = np.nan

    training_data = np.zeros((y.shape[0], X.shape[1]+2))
    training_data[:, 0:X.shape[1]] = X
    training_data[:, X.shape[1]] = y
    training_data[:, X.shape[1]+1] = groups

    np.savetxt(file, training_data, delimiter=',')


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
    groups: Numpy array of group labels, or None

    """

    training_data = np.loadtxt(file, delimiter=',')

    # check to see if last column contains group labels or nans
    lastcol = training_data[:, training_data.shape[1]-1]

    if np.isnan(lastcol).all() is True:
        n_features = training_data.shape[1]-1
        groups = lastcol
    else:
        n_features = training_data.shape[1]
        groups = None

    # retreave X and y
    X = training_data[:, 0:n_features-1]
    y = training_data[:, n_features-1]

    return(X, y, groups)


def sample_predictors(response, predictors, shuffle_data, lowmem, random_state):

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
    y_indexes: Row and Columns of label positions

    """
    current = Region()
    tmpdir = grass.tempdir()

    # open response raster as rasterrow and read as np array
    if RasterRow(response).exist() is True:
        roi_gr = RasterRow(response)
        roi_gr.open('r')

        if lowmem is False:        
            response_np = np.array(roi_gr)
        else:
            response_np = np.memmap(os.path.join(tmpdir, 'response'),
                                    dtype='float32', mode='w+',
                                    shape=(current.rows, current.cols))
            response_np[:] = np.array(roi_gr)[:]
    else:
        grass.fatal("GRASS response raster does not exist.... exiting")

    # determine number of predictor rasters
    n_features = len(predictors)

    # check to see if all predictors exist
    for i in range(n_features):
        if RasterRow(predictors[i]).exist() is not True:
            grass.fatal("GRASS raster " + predictors[i] +
                        " does not exist.... exiting")

    # check if any of those pixels are labelled (not equal to nodata)
    # can use even if roi is FCELL because nodata will be nan
    is_train = np.nonzero(response_np > -2147483648)
    training_labels = response_np[is_train]
    n_labels = np.array(is_train).shape[1]

    # Create a zero numpy array of len training labels
    if lowmem is False:
        training_data = np.zeros((n_labels, n_features))
    else:
        training_data = np.memmap(os.path.join(tmpdir, 'training'),
                                  dtype='float32', mode='w+',
                                  shape=(n_labels, n_features))

    # Loop through each raster and sample pixel values at training indexes
    if lowmem is True:
        feature_np = np.memmap(os.path.join(tmpdir, 'feature',
					   dtype='float32', mode='w+',
                               shape=(current.rows, current.cols)))  

    for f in range(n_features):
        predictor_gr = RasterRow(predictors[f])
        predictor_gr.open('r')
        
        if lowmem is False:
            feature_np = np.array(predictor_gr)
        else:
            feature_np[:] = np.array(predictor_gr)[:]

        training_data[0:n_labels, f] = feature_np[is_train]
        predictor_gr.close()

    # convert any CELL maps no datavals to NaN in the training data
    for i in range(n_features):
        training_data[training_data[:, i] == -2147483648] = np.nan

    # convert indexes of training pixels from tuple to n*2 np array
    is_train = np.array(is_train).T

    # Remove nan rows from training data
    X = training_data[~np.isnan(training_data).any(axis=1)]
    y = training_labels[~np.isnan(training_data).any(axis=1)]
    y_indexes = is_train[~np.isnan(training_data).any(axis=1)]

    roi_gr.close()

    # shuffle the training data
    if shuffle_data is True:
        X, y, y_indexes = shuffle(X, y, y_indexes, random_state=random_state)

    return(X, y, y_indexes)


def prediction(clf, labels, predictors, scaler, class_probabilities,
               rowincr, output, mode):

    """
    Prediction on list of GRASS rasters using a fitted scikit learn model

    Parameters
    ----------
    clf: Scikit learn estimator object
    labels: Numpy array of the labels used for the classification
    predictors: List of GRASS rasters
    scaler: Scaler for predictors, or None
    output: Name of GRASS raster to output classification results
    rowincr: Integer of raster rows to process at one time
    class_probabilties: Predict class probabilities
    mode: String, classification or regression mode

    """

    # create a list of rasterrow objects for predictors
    n_features = len(predictors)
    nclasses = len(labels)
    rasstack = [0] * n_features

    for i in range(n_features):
        rasstack[i] = RasterRow(predictors[i])
        if rasstack[i].exist() is True:
            rasstack[i].open('r')
        else:
            grass.fatal("GRASS raster " + predictors[i] +
                        " does not exist.... exiting")

    # use grass.pygrass.gis.region to get information about the current region
    current = Region()

    # create a imagery mask
    # the input rasters might have different dimensions and non-value pixels.
    # r.series used to automatically create a mask by propagating the nulls
    grass.run_command("r.series", output='tmp_clfmask',
                      input=predictors, method='count', flags='n',
                      overwrite=True)

    mask_raster = RasterRow('tmp_clfmask')
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
    if class_probabilities is True:
        prob_out_raster = [0] * nclasses
        prob = [0] * nclasses
        for iclass in range(nclasses):
            prob_out_raster[iclass] = output + \
                '_classPr' + str(int(labels[iclass]))
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
        nanmask = np.isnan(mask_np_row)  # True in the mask means invalid data

        # reshape each row-band matrix into a n*m array
        nsamples = rowincr * current.cols
        flat_pixels = img_np_row.reshape((nsamples, n_features))

        # remove NaN values
        flat_pixels = np.nan_to_num(flat_pixels)

        # rescale
        if scaler is not None:
            flat_pixels = scaler.transform(flat_pixels)

        # perform prediction
        result = clf.predict(flat_pixels)
        result = result.reshape((rowincr, current.cols))

        # replace NaN values so that the prediction does not have a border
        result = np.ma.masked_array(result, mask=nanmask, fill_value=-99999)

        # return a copy of result, with masked values filled with a value
        result = result.filled([nodata])

        # for each row we can perform computation, and write the result into
        for row in range(rowincr):
            newrow = Buffer((result.shape[1],), mtype=ftype)
            newrow[:] = result[row, :]
            classification.put_row(newrow)

        # same for probabilities
        if class_probabilities is True and mode is 'classification':
            result_proba = clf.predict_proba(flat_pixels)

            for iclass in range(result_proba.shape[1]):

                result_proba_class = result_proba[:, iclass]
                result_proba_class = result_proba_class.reshape(
                                        (rowincr, current.cols))

                result_proba_class = np.ma.masked_array(
                    result_proba_class, mask=nanmask, fill_value=np.nan)

                result_proba_class = result_proba_class.filled([np.nan])

                for row in range(rowincr):

                    newrow = Buffer((
                                result_proba_class.shape[1],), mtype='FCELL')

                    newrow[:] = result_proba_class[row, :]
                    prob[iclass].put_row(newrow)

    classification.close()
    mask_raster.close()

    if class_probabilities is True and mode is 'classification':
        for iclass in range(nclasses):
            prob[iclass].close()


def cross_val_classification(clf, X, y, group_ids, cv, rstate):

    """
    Stratified Kfold cross-validation
    Generates several scoring_metrics

    Parameters
    ----------
    clf: Scikit learn estimator object
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    group_ids: Numpy array containing group labels for samples
    cv: Integer of cross-validation folds
    rstate: Seed to pass to the random number generator

    Returns
    -------
    scores: Dictionary of global accuracy measures per fold
    y_test_agg: Aggregated test responses
    y_pred_agg: Aggregated predicted responses

    """

    # dicts of lists to store metrics
    scores = {
        'accuracy': [],
        'auc': [],
        'r2': []
    }

    # generate Kfold indices
    if group_ids is None:
        k_fold = StratifiedKFold(
            n_splits=cv, shuffle=False, random_state=rstate).split(X, y)
    else:

        n_groups = len(np.unique(group_ids))

        if cv > n_groups:
            grass.message(
                "Number of cv folds cannot be larger than the number of groups in the zonal raster, using n_groups")
            cv = n_groups
        k_fold = GroupKFold(n_splits=cv).split(X, y, groups=group_ids)

    y_test_agg = []
    y_pred_agg = []

    # loop through each fold
    for train_indices, test_indices in k_fold:

        X_train, X_test = X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]

        # fit the model on the training data and predict the test data
        fit = clf.fit(X_train, y_train)
        y_pred = fit.predict(X_test)

        y_test_agg = np.append(y_test_agg, y_test)
        y_pred_agg = np.append(y_pred_agg, y_pred)

        # calculate metrics
        scores['accuracy'] = np.append(
            scores['accuracy'], metrics.accuracy_score(y_test, y_pred))

        scores['r2'] = np.append(
            scores['r2'], metrics.r2_score(y_test, y_pred))

        # test for if binary and classes equal 0,1
        if len(np.unique(y)) == 2 and all([0, 1] == np.unique(y)):
            try:
                y_pred_proba = fit.predict_proba(X_test)[:, 1]

                scores['auc'] = np.append(
                    scores['auc'], metrics.roc_auc_score(y_test, y_pred_proba))
            except:
                pass

    return(scores, y_test_agg, y_pred_agg)


def tune_split(X, y, Id, estimator, params, test_size, random_state):

    if Id is None:
        X, X_devel, y, y_devel = train_test_split(X, y, test_size=test_size,
                            random_state=random_state)
        Id_devel = None
    else:
        X, X_devel, y, y_devel, Id, Id_devel = train_test_split(X, y, Id, test_size=test_size,
                            random_state=random_state, stratify=Id)

    clf = GridSearchCV(estimator=estimator, cv=3, param_grid=params,
                              scoring="accuracy", n_jobs=-1)
    
    clf.fit(X_devel, y_devel)

    return (X, X_devel, y, y_devel, Id, Id_devel, clf)


def feature_importances(clf, X, y):

    min_max_scaler = preprocessing.MinMaxScaler()

    try:
        clfimp = min_max_scaler.fit_transform(
                    clf.feature_importances_.reshape(-1, 1))
    except:
        try:
            clfimp = min_max_scaler.fit_transform(
                        abs(clf.coef_.T).reshape(-1, 1))
        except:
            sk = SelectKBest(f_classif, k='all')
            sk_fit = sk.fit(X, y)
            clfimp = min_max_scaler.fit_transform(
                        sk_fit.scores_.reshape(-1, 1))

    return (clfimp)


def sample_training_data(roi, maplist, cv, cvtype, model_load, model_save,
                         load_training, save_training, lowmem, random_state):
    
    # load the model or training data
    if model_load != '':
        clf = joblib.load(model_load)
        X, y, Id = load_training_data(
                            model_load.replace('.pkl', '.csv'))
    else:
        clf = None
        if load_training != '':
            X, y, Id = load_training_data(load_training)
        else:
            # create clumped roi for spatial cross validation
            if cv > 1 and cvtype == 'clumped':
                r.clump(input=roi, output='tmp_roi_clumped', overwrite=True, quiet=True)
                maplist2 = maplist
                maplist2.append('tmp_roi_clumped')
                X, y, sample_coords = sample_predictors(response=roi,
                                                        predictors=maplist2,
                                                        shuffle_data=False,
                                                        lowmem=lowmem)
                 # take Id from last column
                Id = X[:, X.shape[1]-1]

                # remove Id column from predictors
                X = X[:, 0:X.shape[1]]
            else:
                # query predictor rasters with training features
                Id = None
                X, y, sample_coords = sample_predictors(
                    response=roi, predictors=maplist, shuffle_data=True,
                    lowmem=lowmem, random_state=random_state)

            if save_training != '':
                save_training_data(X, y, Id, save_training)
                
            if model_save != '':
                save_training_data(X, y, Id, model_save + ".csv")

    # perform kmeans clustering on point coordinates
    if cv > 1 and cvtype == 'kmeans':
        clusters = KMeans(
            n_clusters=cv, random_state=random_state, n_jobs=-1)
        clusters.fit(sample_coords)
        Id = clusters.labels_

    return (X, y, Id, clf)
