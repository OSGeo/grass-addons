# -*- coding: utf-8 -*-

import os
import scipy
import numpy as np
from numpy.random import RandomState
from copy import deepcopy
import tempfile
import grass.script as grass
from grass.pygrass.raster import RasterRow
from grass.pygrass.gis.region import Region
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.modules.shortcuts import imagery as im
from subprocess import PIPE


class random_oversampling():

    def __init__(self, random_state):
        """
        Balances X, y observations using simple oversampling

        Args
        ----
        random_state: Seed to pass onto random number generator
        """

        self.random_state = random_state

    def fit_sample(self, X, y):
        """
        Performs equal balancing of response and explanatory variances

        Args
        ----
        X: numpy array of training data
        y: 1D numpy array of response data

        Returns
        -------
        X_resampled: Numpy array of resampled training data
        y_resampled: Numpy array of resampled response data
        """

        np.random.seed(seed=self.random_state)

        # count the number of observations per class
        y_classes = np.unique(y)
        class_counts = np.histogram(y, bins=len(y_classes))[0]
        maj_counts = class_counts.max()

        y_resampled = y
        X_resampled = X

        for cla, counts in zip(y_classes, class_counts):
            # get the number of samples needed to balance minority class
            num_samples = maj_counts - counts

            # get the indices of the ith class
            indx = np.nonzero(y == cla)

            # create some new indices
            oversamp_indx = np.random.choice(indx[0], size=num_samples)

            # concatenate to the original X and y
            y_resampled = np.concatenate((y[oversamp_indx], y_resampled))
            X_resampled = np.concatenate((X[oversamp_indx], X_resampled))

        return (X_resampled, y_resampled)


class train():

    def __init__(self, estimator, categorical_var=None,
                 preprocessing=None, sampling=None):
        """
        Train class to perform preprocessing, fitting, parameter search and
        cross-validation in a single step

        Args
        ----
        estimator: Scikit-learn compatible estimator object
        categorical_var: 1D list containing indices of categorical predictors
        preprocessing: Sklearn preprocessing scaler
        sampling: Balancing object e.g. from imbalance-learn
        """

        # fitting data
        self.estimator = estimator

        # for onehot-encoding
        self.enc = None
        self.categorical_var = categorical_var
        self.category_values = None

        # for preprocessing of data
        self.sampling = sampling
        self.preprocessing = preprocessing

        # for cross-validation scores
        self.scores = None
        self.fimp = None
        self.mean_tpr = None
        self.mean_fpr = None

    def __onehotencode(self, X):

        """
        Method to convert a list of categorical arrays in X into a suite of
        binary predictors which are added to the end of the array

        Args
        ----
        X: 2D numpy array containing training data
        """

        from sklearn.preprocessing import OneHotEncoder

        # store original range of values
        self.category_values = [0] * len(self.categorical_var)
        for i, cat in enumerate(self.categorical_var):
            self.category_values[i] = np.unique(X[:, cat])

        # fit and transform categorical grids to a suite of binary features
        self.enc = OneHotEncoder(categorical_features=self.categorical_var,
                                 sparse=False)
        self.enc.fit(X)
        X = self.enc.transform(X)

        return(X)

    def fit(self, X, y, groups=None):

        """
        Main fit method for the train object

        Args
        ----
        X, y: training data and labels as numpy arrays
        groups: groups to be used for cross-validation
        """

        from sklearn.model_selection import RandomizedSearchCV, GridSearchCV

        # Balance classes prior to fitting
        if self.sampling is not None:
            if groups is None:
                X, y = self.sampling.fit_sample(X, y)
            else:
                X = np.hstack((X, groups.reshape(-1, 1)))
                X, y = self.sampling.fit_sample(X, y)
                groups = X[:, -1]
                X = X[:, :-1]

        if self.preprocessing is not None:
            X = self.__preprocessor(X)

        if self.categorical_var is not None:
            X = self.__onehotencode(X)

        # fit the model on the training data and predict the test data
        # need the groups parameter because the estimator can be a
        # RandomizedSearchCV or GridSearchCV estimator where cv=GroupKFold
        if isinstance(self.estimator, RandomizedSearchCV) \
                or isinstance(self.estimator, GridSearchCV):
            param_search = True
        else:
            param_search = False

        if groups is not None and param_search is True:
            self.estimator.fit(X, y, groups=groups)
        else:
            self.estimator.fit(X, y)

    def __preprocessor(self, X):
        """
        Transforms the non-categorical X

        Args
        ----
        X; 2D numpy array to transform
        """

        # create mask so that indices that represent categorical
        # predictors are not selected
        if self.categorical_var is not None:
            idx = np.arange(X.shape[1])
            mask = np.ones(len(idx), dtype=bool)
            mask[self.categorical_var] = False
        else:
            mask = np.arange(X.shape[1])

        X_continuous = X[:, mask]
        self.preprocessing.fit(X=X_continuous)
        X[:, mask] = self.preprocessing.transform(X_continuous)

        return(X)

    def varImp_permutation(self, estimator, X_test, y_true,
                           n_permutations, scorers,
                           random_state):

        """
        Method to perform permutation-based feature importance during
        cross-validation (cross-validation is applied externally to this
        method)

        Procedure is:
        1. Pass fitted estimator and test partition X y
        2. Assess AUC on the test partition (bestauc)
        3. Permute each variable and assess the difference between bestauc and
           the messed-up variable
        4. Repeat (3) for many random permutations
        5. Average the repeats

        Args
        ----
        estimator: estimator that has been fitted to a training partition
        X_test, y_true: data and labels from a test partition
        n_permutations: number of random permutations to apply
        random_state: seed to pass to the numpy random.seed

        Returns
        -------
        scores: AUC scores for each predictor following permutation
        """

        from sklearn import metrics
        if scorers == 'binary' or scorers == 'multiclass':
            scorer = metrics.accuracy_score
        if scorers == 'regression':
            scorer = metrics.r2_score

        # calculate score on original variables without permutation
        # determine best metric type for binary/multiclass/regression scenarios
        y_pred = estimator.predict(X_test)
        best_score = scorer(y_true, y_pred)

        np.random.seed(seed=random_state)
        rstate = RandomState(random_state)
        scores = np.zeros((n_permutations, X_test.shape[1]))

        # outer loop to repeat the pemutation rep times
        for rep in range(n_permutations):

            # inner loop to permute each predictor variable and assess
            # difference in auc
            for i in range(X_test.shape[1]):
                Xscram = np.copy(X_test)
                Xscram[:, i] = rstate.choice(X_test[:, i], X_test.shape[0])

                # fit the model on the training data and predict the test data
                y_pred = estimator.predict(Xscram)
                scores[rep, i] = best_score-scorer(y_true, y_pred)
                if scores[rep, i] < 0:
                    scores[rep, i] = 0

        # average the repetitions
        scores = scores.mean(axis=0)

        return(scores)

    def specificity_score(self, y_true, y_pred):

        """
        Simple method to calculate specificity score

        Args
        ----
        y_true: 1D numpy array of truth values
        y_pred: 1D numpy array of predicted classes

        Returns
        -------
        specificity: specificity score
        """

        from sklearn.metrics import confusion_matrix

        cm = confusion_matrix(y_true, y_pred)

        tn = float(cm[0][0])
        # fn = float(cm[1][0])
        # tp = float(cm[1][1])
        fp = float(cm[0][1])

        specificity = tn/(tn+fp)

        return (specificity)

    def cross_val(self, splitter, X, y, groups=None, scorers='binary',
                  feature_importances=False, n_permutations=25,
                  random_state=None):

        from sklearn.model_selection import RandomizedSearchCV, GridSearchCV
        from sklearn import metrics

        """
        Stratified Kfold and GroupFold cross-validation
        Generates suites of scoring_metrics for binary classification,

        multiclass classification and regression scenarios

        Args
        ----
        splitter: Scikit learn model_selection object, e.g. StratifiedKFold
        X, y: 2D numpy array of training data and 1D array of labels
        groups: 1D numpy array of groups to be used for cross-validation
        scorers: String specifying suite of performance metrics to use
        feature_importances: Boolean to perform permutation-based importances
        n_permutations: Number of permutations during feature importance
        random_state: Seed to pass to the random number generator
        """

        # preprocessing -------------------------------------------------------
        if self.preprocessing is not None:
            X = self.__preprocessor(X)

        if self.categorical_var is not None:
            X = self.__onehotencode(X)

        # create copy of fitting estimator for cross-val fitting
        fit_train = deepcopy(self.estimator)

        # create dictionary of lists to store metrics -------------------------
        n_classes = len(np.unique(y))

        if scorers == 'accuracy':
            self.scores = {
                'accuracy': []
            }

        if scorers == 'binary':
            self.scores = {
                'accuracy': [],
                'precision': [],
                'recall': [],
                'specificity': [],
                'f1': [],
                'kappa': [],
                'auc': []
            }

        if scorers == 'multiclass':
            self.scores = {
                'accuracy': [],
                'kappa': [],
                'precision': np.zeros((0, n_classes)),  # scores per sample
                'recall': np.zeros((0, n_classes)),
                'f1': np.zeros((0, n_classes))
                }

        if scorers == 'regression':
            self.scores = {
                'r2': []
            }

        self.mean_tpr = 0
        self.mean_fpr = np.linspace(0, 1, 100)

        # create np array to store feature importance scores
        # for each predictor per fold
        if feature_importances is True:
            self.fimp = np.zeros((splitter.get_n_splits(), X.shape[1]))
            self.fimp[:] = np.nan

        # generate Kfold indices ----------------------------------------------

        if groups is None:
            k_fold = splitter.split(X, y)
        else:
            k_fold = splitter.split(
                X, y, groups=groups)

        # train on k-1 folds and test of k folds ------------------------------

        for train_indices, test_indices in k_fold:

            # get indices for train and test partitions
            X_train, X_test = X[train_indices], X[test_indices]
            y_train, y_test = y[train_indices], y[test_indices]
            if groups is not None:
                groups_train = groups[train_indices]

            # balance the training fold
            if self.sampling is not None:
                if groups is None:
                    X_train, y_train = self.sampling.fit_sample(
                            X_train, y_train)
                else:
                    X_train = np.hstack((X_train, groups_train.reshape(-1, 1)))
                    X_train, y_train = self.sampling.fit_sample(
                            X_train, y_train)
                    groups_train = X_train[:, -1]
                    X_train = X_train[:, :-1]

            else:
                # also get indices of groups for the training partition
                if groups is not None:
                    groups_train = groups[train_indices]

            # fit the model on the training data and predict the test data
            # need the groups parameter because the estimator can be a
            # RandomizedSearchCV or GridSearchCV estimator where cv=GroupKFold
            if isinstance(fit_train, RandomizedSearchCV) is True \
                    or isinstance(fit_train, GridSearchCV):
                param_search = True
            else:
                param_search = False

            # train fit_train on training fold
            if groups is not None and param_search is True:
                fit_train.fit(X_train, y_train, groups=groups_train)
            else:
                fit_train.fit(X_train, y_train)

            # prediction of test fold
            y_pred = fit_train.predict(X_test)
            labels = np.unique(y_pred)

            # calculate metrics
            if scorers == 'accuracy':
                self.scores['accuracy'] = np.append(
                    self.scores['accuracy'],
                    metrics.accuracy_score(y_test, y_pred))

            elif scorers == 'binary':
                self.scores['accuracy'] = np.append(
                    self.scores['accuracy'],
                    metrics.accuracy_score(y_test, y_pred))

                y_pred_proba = fit_train.predict_proba(X_test)[:, 1]
                self.scores['auc'] = np.append(
                    self.scores['auc'],
                    metrics.roc_auc_score(y_test, y_pred_proba))

                self.scores['precision'] = np.append(
                    self.scores['precision'], metrics.precision_score(
                        y_test, y_pred, labels, average='binary'))

                self.scores['recall'] = np.append(
                    self.scores['recall'], metrics.recall_score(
                        y_test, y_pred, labels, average='binary'))

                self.scores['specificity'] = np.append(
                    self.scores['specificity'], self.specificity_score(
                        y_test, y_pred))

                self.scores['f1'] = np.append(
                    self.scores['f1'], metrics.f1_score(
                        y_test, y_pred, labels, average='binary'))

                self.scores['kappa'] = np.append(
                    self.scores['kappa'],
                    metrics.cohen_kappa_score(y_test, y_pred))

                fpr, tpr, thresholds = metrics.roc_curve(y_test, y_pred_proba)
                self.mean_tpr += scipy.interp(self.mean_fpr, fpr, tpr)
                self.mean_tpr[0] = 0.0

            elif scorers == 'multiclass':

                self.scores['accuracy'] = np.append(
                    self.scores['accuracy'],
                    metrics.accuracy_score(y_test, y_pred))

                self.scores['kappa'] = np.append(
                    self.scores['kappa'],
                    metrics.cohen_kappa_score(y_test, y_pred))

                self.scores['precision'] = np.vstack((
                    self.scores['precision'],
                    np.array(metrics.precision_score(
                        y_test, y_pred, average=None))))

                self.scores['recall'] = np.vstack((
                    self.scores['recall'],
                    np.array(metrics.recall_score(
                        y_test, y_pred, average=None))))

                self.scores['f1'] = np.vstack((
                    self.scores['f1'],
                    np.array(metrics.f1_score(
                        y_test, y_pred, average=None))))

            elif scorers == 'regression':
                self.scores['r2'] = np.append(
                    self.scores['r2'], metrics.r2_score(y_test, y_pred))

            # feature importances using permutation
            if feature_importances is True:
                if bool((np.isnan(self.fimp)).all()) is True:
                    self.fimp = self.varImp_permutation(
                        fit_train, X_test, y_test, n_permutations, scorers,
                        random_state)
                else:
                    self.fimp = np.row_stack(
                        (self.fimp, self.varImp_permutation(
                            fit_train, X_test, y_test,
                            n_permutations, scorers, random_state)))

        # summarize data ------------------------------------------------------

        # convert onehot-encoded feature importances back to original vars
        if self.fimp is not None and self.enc is not None:

            # get start,end positions of each suite of onehot-encoded vars
            feature_ranges = deepcopy(self.enc.feature_indices_)
            for i in range(0, len(self.enc.feature_indices_)-1):
                feature_ranges[i+1] = feature_ranges[i] + \
                              len(self.category_values[i])

            # take sum of each onehot-encoded feature
            ohe_feature = [0] * len(self.categorical_var)
            ohe_sum = [0] * len(self.categorical_var)

            for i in range(len(self.categorical_var)):
                ohe_feature[i] = \
                           self.fimp[:, feature_ranges[i]:feature_ranges[i+1]]
                ohe_sum[i] = ohe_feature[i].sum(axis=1)

            # remove onehot-encoded features from the importances array
            features_for_removal = np.array(range(feature_ranges[-1]))
            self.fimp = np.delete(self.fimp, features_for_removal, axis=1)

            # insert summed importances into original positions
            for index in self.categorical_var:
                self.fimp = np.insert(self.fimp, np.array(index),
                                      ohe_sum[0], axis=1)

        if scorers == 'binary':
            self.mean_tpr /= splitter.get_n_splits(X, y)
            self.mean_tpr[-1] = 1.0

    def get_roc_curve(self):
        return (self.mean_tpr, self.mean_fpr)

    def get_cross_val_scores(self):
        return (self.scores)

    def predict(self, predictors, output, labels=None,
                class_probabilities=False, rowincr=25):

        """
        Prediction on list of GRASS rasters using a fitted scikit learn model

        Parameters
        ----------
        predictors: List of GRASS rasters

        class_probabilties: Predict class probabilities

        rowincr: Integer of raster rows to process at one time
        output: Name of GRASS raster to output classification results
        """

        # determine output data type and nodata
        if labels is not None:
            ftype = 'CELL'
            nodata = -2147483648
        else:
            ftype = 'FCELL'
            nodata = np.nan

        # create a list of rasterrow objects for predictors
        n_features = len(predictors)
        rasstack = [0] * n_features

        for i in range(n_features):
            rasstack[i] = RasterRow(predictors[i])
            if rasstack[i].exist() is True:
                rasstack[i].open('r')
            else:
                grass.fatal("GRASS raster " + predictors[i] +
                            " does not exist.... exiting")

        current = Region()

        # create a imagery mask
        # the input rasters might have different dimensions and null pixels.
        # r.series used to automatically create a mask by propagating the nulls
        grass.run_command("r.series", output='tmp_clfmask',
                          input=predictors, method='count', flags='n',
                          overwrite=True)

        mask_raster = RasterRow('tmp_clfmask')
        mask_raster.open('r')

        # create and open RasterRow objects for classification
        classification = RasterRow(output)
        classification.open('w', ftype, overwrite=True)

        # create and open RasterRow objects for  probabilities if enabled
        if class_probabilities is True:

            # determine number of classes
            nclasses = len(labels)

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
        try:
            for rowblock in range(0, current.rows, rowincr):
                grass.percent(rowblock, current.rows, rowincr)
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
                nanmask = np.isnan(mask_np_row)  # True in mask means invalid data

                # reshape each row-band matrix into a n*m array
                nsamples = rowincr * current.cols
                flat_pixels = img_np_row.reshape((nsamples, n_features))

                # remove NaN values and GRASS CELL nodata vals
                flat_pixels[flat_pixels == -2147483648] = np.nan
                flat_pixels = np.nan_to_num(flat_pixels)

                # rescale
                if self.preprocessing is not None:
                    # create mask so that indices that represent categorical
                    # predictors are not selected
                    if self.categorical_var is not None:
                        idx = np.arange(n_features)
                        mask = np.ones(len(idx), dtype=bool)
                        mask[self.categorical_var] = False
                    else:
                        mask = np.arange(n_features)
                    flat_pixels_continuous = flat_pixels[:, mask]
                    flat_pixels[:, mask] = self.preprocessing.transform(
                            flat_pixels_continuous)

                # onehot-encoding
                if self.enc is not None:
                    try:
                        flat_pixels = self.enc.transform(flat_pixels)
                    except:
                        # if this fails it is because the onehot-encoder was fitted
                        # on the training samples, but the prediction data contains
                        # new values, i.e. the training data has not sampled all of
                        # categories
                        grass.fatal('There are values in the categorical rasters '
                                    'that are not present in the training data '
                                    'set, i.e. the training data has not sampled '
                                    'all of the categories')

                # perform prediction
                result = self.estimator.predict(flat_pixels)
                result = result.reshape((rowincr, current.cols))

                # replace NaN values so that the prediction does not have a border
                result = np.ma.masked_array(
                    result, mask=nanmask, fill_value=-99999)

                # return a copy of result, with masked values filled with a value
                result = result.filled([nodata])

                # for each row we can perform computation, and write the result
                for row in range(rowincr):
                    newrow = Buffer((result.shape[1],), mtype=ftype)
                    newrow[:] = result[row, :]
                    classification.put_row(newrow)

                # same for probabilities
                if class_probabilities is True:
                    result_proba = self.estimator.predict_proba(flat_pixels)

                    for iclass in range(result_proba.shape[1]):

                        result_proba_class = result_proba[:, iclass]
                        result_proba_class = result_proba_class.reshape(
                                                (rowincr, current.cols))

                        result_proba_class = np.ma.masked_array(
                            result_proba_class, mask=nanmask, fill_value=np.nan)

                        result_proba_class = result_proba_class.filled([np.nan])

                        for row in range(rowincr):
                            newrow = Buffer((
                                        result_proba_class.shape[1],),
                                        mtype='FCELL')

                            newrow[:] = result_proba_class[row, :]
                            prob[iclass].put_row(newrow)
        finally:
            # close all predictors
            for i in range(n_features):
                rasstack[i].close()

            # close classification and mask maps
            classification.close()
            mask_raster.close()

            grass.run_command("g.remove", name='tmp_clfmask',
                              flags="f", type="raster", quiet=True)

            # close all class probability maps
            try:
                for iclass in range(nclasses):
                    prob[iclass].close()
            except:
                pass


def model_classifiers(estimator='LogisticRegression', random_state=None,
                      C=1, max_depth=None, max_features='auto',
                      min_samples_split=2, min_samples_leaf=1,
                      n_estimators=100, subsample=1.0,
                      learning_rate=0.1, max_degree=1):

    """
    Provides the classifiers and parameters using by the module

    Args
    ----
    estimator: Name of estimator
    random_state: Seed to use in randomized components
    C: Inverse of regularization strength
    max_depth: Maximum depth for tree-based methods
    min_samples_split: Minimum number of samples to split a node
    min_samples_leaf: Minimum number of samples to form a leaf
    n_estimators: Number of trees
    subsample: Controls randomization in gradient boosting
    learning_rate: Used in gradient boosting
    max_degree: For earth

    Returns
    -------
    clf: Scikit-learn classifier object
    mode: Flag to indicate whether classifier performs classification or
          regression
    """

    from sklearn.linear_model import LogisticRegression
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
    from sklearn.naive_bayes import GaussianNB
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.svm import SVC

    # optional packages that add additional classifiers here
    if estimator == 'EarthClassifier' or estimator == 'EarthRegressor':
        try:
            from sklearn.pipeline import Pipeline
            from pyearth import Earth

            earth_classifier = Pipeline([('Earth',
                                          Earth(max_degree=max_degree)),
                                        ('Logistic', LogisticRegression())])

            classifiers = {'EarthClassifier': earth_classifier,
                           'EarthRegressor': Earth(max_degree=max_degree)}
        except:
            grass.fatal('Py-earth package not installed')

    elif estimator == 'XGBClassifier' or estimator == 'XGBRegressor':
        try:
            from xgboost import XGBClassifier, XGBRegressor

            if max_depth is None:
                max_depth = int(3)

            classifiers = {
                'XGBClassifier':
                    XGBClassifier(learning_rate=learning_rate,
                                  n_estimators=n_estimators,
                                  max_depth=max_depth,
                                  subsample=subsample),
                'XGBRegressor':
                    XGBRegressor(learning_rate=learning_rate,
                                 n_estimators=n_estimators,
                                 max_depth=max_depth,
                                 subsample=subsample)}
        except:
            grass.fatal('XGBoost package not installed')
    else:
        # core sklearn classifiers go here
        classifiers = {
            'SVC': SVC(C=C, probability=True, random_state=random_state),
            'LogisticRegression':
                LogisticRegression(C=C, random_state=random_state, n_jobs=-1,
                                   fit_intercept=True),
            'DecisionTreeClassifier':
                DecisionTreeClassifier(max_depth=max_depth,
                                       max_features=max_features,
                                       min_samples_split=min_samples_split,
                                       min_samples_leaf=min_samples_leaf,
                                       random_state=random_state),
            'DecisionTreeRegressor':
                DecisionTreeRegressor(max_features=max_features,
                                      min_samples_split=min_samples_split,
                                      min_samples_leaf=min_samples_leaf,
                                      random_state=random_state),
            'RandomForestClassifier':
                RandomForestClassifier(n_estimators=n_estimators,
                                       max_features=max_features,
                                       min_samples_split=min_samples_split,
                                       min_samples_leaf=min_samples_leaf,
                                       random_state=random_state,
                                       n_jobs=-1,
                                       oob_score=False),
            'RandomForestRegressor':
                RandomForestRegressor(n_estimators=n_estimators,
                                      max_features=max_features,
                                      min_samples_split=min_samples_split,
                                      min_samples_leaf=min_samples_leaf,
                                      random_state=random_state,
                                      n_jobs=-1,
                                      oob_score=False),
            'GradientBoostingClassifier':
                GradientBoostingClassifier(learning_rate=learning_rate,
                                           n_estimators=n_estimators,
                                           max_depth=max_depth,
                                           min_samples_split=min_samples_split,
                                           min_samples_leaf=min_samples_leaf,
                                           subsample=subsample,
                                           max_features=max_features,
                                           random_state=random_state),
            'GradientBoostingRegressor':
                GradientBoostingRegressor(learning_rate=learning_rate,
                                          n_estimators=n_estimators,
                                          max_depth=max_depth,
                                          min_samples_split=min_samples_split,
                                          min_samples_leaf=min_samples_leaf,
                                          subsample=subsample,
                                          max_features=max_features,
                                          random_state=random_state),
            'GaussianNB': GaussianNB(),
            'LinearDiscriminantAnalysis': LinearDiscriminantAnalysis(),
            'QuadraticDiscriminantAnalysis': QuadraticDiscriminantAnalysis(),
        }

    # define classifier
    clf = classifiers[estimator]

    # classification or regression
    if estimator == 'LogisticRegression' \
        or estimator == 'DecisionTreeClassifier' \
        or estimator == 'RandomForestClassifier' \
        or estimator == 'GradientBoostingClassifier' \
        or estimator == 'GaussianNB' \
        or estimator == 'LinearDiscriminantAnalysis' \
        or estimator == 'QuadraticDiscriminantAnalysis' \
        or estimator == 'EarthClassifier' \
        or estimator == 'XGBClassifier' \
            or estimator == 'SVC':
            mode = 'classification'
    else:
        mode = 'regression'

    return (clf, mode)


def save_training_data(X, y, groups, file):

    """
    Saves any extracted training data to a csv file

    Args
    ----
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels
    file: Path to a csv file to save data to
    """

    # if there are no group labels, create a nan filled array
    if groups is None:
        groups = np.empty((y.shape[0]))
        groups[:] = np.nan

    training_data = np.column_stack([X, y, groups])
    np.savetxt(file, training_data, delimiter=',')


def load_training_data(file):

    """
    Loads training data and labels from a csv file

    Args
    ----
    file: Path to a csv file to save data to

    Returns
    -------
    X: Numpy array containing predictor values
    y: Numpy array containing labels
    groups: Numpy array of group labels, or None
    """

    training_data = np.loadtxt(file, delimiter=',')
    n_cols = training_data.shape[1]
    last_Xcol = n_cols-2

    # check to see if last column contains group labels or nans
    groups = training_data[:, -1]

    # if all nans then set groups to None
    if bool(np.isnan(groups).all()) is True:
        groups = None

    # fetch X and y
    X = training_data[:, 0:last_Xcol]
    y = training_data[:, -2]

    return(X, y, groups)


def extract(response, predictors, impute=False, shuffle_data=True,
            lowmem=False, random_state=None):

    """
    Samples a list of GRASS rasters using a labelled raster
    Per raster sampling

    Args
    ----
    response: String; GRASS raster with labelled pixels
    predictors: List of GRASS rasters containing explanatory variables

    Returns
    -------

    training_data: Numpy array of extracted raster values
    training_labels: Numpy array of labels
    y_indexes: Row and Columns of label positions
    """

    from sklearn.utils import shuffle
    from sklearn.preprocessing import Imputer

    current = Region()

    # open response raster as rasterrow and read as np array
    if RasterRow(response).exist() is True:
        roi_gr = RasterRow(response)
        roi_gr.open('r')

        if lowmem is False:
            response_np = np.array(roi_gr)
        else:
            response_np = np.memmap(tempfile.NamedTemporaryFile(),
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
        training_data = np.memmap(tempfile.NamedTemporaryFile(),
                                  dtype='float32', mode='w+',
                                  shape=(n_labels, n_features))

    # Loop through each raster and sample pixel values at training indexes
    if lowmem is True:
        feature_np = np.memmap(tempfile.NamedTemporaryFile(),
                               dtype='float32', mode='w+',
                               shape=(current.rows, current.cols))

    for f in range(n_features):
        predictor_gr = RasterRow(predictors[f])
        predictor_gr.open('r')

        if lowmem is False:
            feature_np = np.array(predictor_gr)
        else:
            feature_np[:] = np.array(predictor_gr)[:]

        training_data[0:n_labels, f] = feature_np[is_train]

        # close each predictor map
        predictor_gr.close()

    # convert any CELL maps no datavals to NaN in the training data
    for i in range(n_features):
        training_data[training_data[:, i] == -2147483648] = np.nan

    # convert indexes of training pixels from tuple to n*2 np array
    is_train = np.array(is_train).T

    # impute missing values
    if impute is True:
        missing = Imputer(strategy='median')
        training_data = missing.fit_transform(training_data)

    # Remove nan rows from training data
    X = training_data[~np.isnan(training_data).any(axis=1)]
    y = training_labels[~np.isnan(training_data).any(axis=1)]
    y_indexes = is_train[~np.isnan(training_data).any(axis=1)]

    # shuffle the training data
    if shuffle_data is True:
        X, y, y_indexes = shuffle(X, y, y_indexes, random_state=random_state)

    # close the response map
    roi_gr.close()

    return(X, y, y_indexes)


def maps_from_group(group):

    """
    Parse individual rasters into a list from an imagery group

    Args
    ----
    group: String; GRASS imagery group
    Returns
    -------
    maplist: Python list containing individual GRASS raster maps
    """
    groupmaps = im.group(group=group, flags="g",
                         quiet=True, stdout_=PIPE).outputs.stdout

    maplist = groupmaps.split(os.linesep)
    maplist = maplist[0:len(maplist)-1]
    map_names = []

    for rastername in maplist:
        map_names.append(rastername.split('@')[0])

    return(maplist, map_names)
