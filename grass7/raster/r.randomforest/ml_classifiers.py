#!/usr/bin/env python

from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.svm import SVC


def model_classifiers(estimator, random_state, class_weight,
                      C, max_depth, max_features,
                      min_samples_split, min_samples_leaf,
                      n_estimators, subsample, learning_rate):

    classifiers = {
        'SVC': SVC(C=C, probability=True, random_state=random_state),
        'LogisticRegression': LogisticRegression(C=C, class_weight=class_weight,
                                                 random_state=random_state),
        'DecisionTreeClassifier': DecisionTreeClassifier(max_depth=max_depth,
                                                         max_features=max_features,
                                                         min_samples_split=min_samples_split,
                                                         min_samples_leaf=min_samples_leaf,
                                                         random_state=random_state,
                                                         class_weight=class_weight),
        'DecisionTreeRegressor': DecisionTreeRegressor(max_features=max_features,
                                                       min_samples_split=min_samples_split,
                                                       min_samples_leaf=min_samples_leaf,
                                                       random_state=random_state),
        'RandomForestClassifier': RandomForestClassifier(n_estimators=n_estimators,
                                                         class_weight=class_weight,
                                                         max_features=max_features,
                                                         min_samples_split=min_samples_split,
                                                         random_state=random_state,
                                                         n_jobs=-1,
                                                         oob_score=True),
        'RandomForestRegressor': RandomForestRegressor(n_estimators=n_estimators,
                                                       max_features=max_features,
                                                       min_samples_split=min_samples_split,
                                                       random_state=random_state,
                                                       n_jobs=-1,
                                                       oob_score=True),
        'GradientBoostingClassifier': GradientBoostingClassifier(learning_rate=learning_rate,
                                                                 n_estimators=n_estimators,
                                                                 max_depth=max_depth,
                                                                 min_samples_split=min_samples_split,
                                                                 min_samples_leaf=min_samples_leaf,
                                                                 subsample=subsample,
                                                                 max_features=max_features,
                                                                 random_state=random_state),
        'GradientBoostingRegressor': GradientBoostingRegressor(learning_rate=learning_rate,
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

    SVCOpts = {'C': [1, 10, 100], 'shrinking': [True, False]}
    LogisticRegressionOpts = {'C': [1, 10, 100, 1000]}
    DecisionTreeOpts = {'max_depth': [2, 4, 6, 8, 10, 20],
                        'max_features': ['sqrt', 'log2', None],
                        'min_samples_split': [2, 0.01, 0.05, 0.1, 0.25]}
    RandomForestOpts = {'max_features': ['sqrt', 'log2', None]}
    GradientBoostingOpts = {'learning_rate': [0.01, 0.02, 0.05, 0.1],
                            'max_depth': [3, 4, 6, 10],
                            'max_features': ['sqrt', 'log2', None],
                            'n_estimators': [50, 100, 150, 250, 500]}

    param_grids = {
        'SVC': SVCOpts,
        'LogisticRegression': LogisticRegressionOpts,
        'DecisionTreeClassifier': DecisionTreeOpts,
        'DecisionTreeRegressor': DecisionTreeOpts,
        'RandomForestClassifier': RandomForestOpts,
        'RandomForestRegressor': RandomForestOpts,
        'GradientBoostingClassifier': GradientBoostingOpts,
        'GradientBoostingRegressor': GradientBoostingOpts,
        'GaussianNB': {},
        'LinearDiscriminantAnalysis': {},
        'QuadraticDiscriminantAnalysis': {},
    }
    
    # define classifier
    clf = classifiers[estimator]
    params = param_grids[estimator]
    
    # classification or regression
    if estimator == 'LogisticRegression' \
        or estimator == 'DecisionTreeClassifier' \
        or estimator == 'RandomForestClassifier' \
        or estimator == 'GradientBoostingClassifier' \
        or estimator == 'GaussianNB' \
        or estimator == 'LinearDiscriminantAnalysis' \
        or estimator == 'QuadraticDiscriminantAnalysis' \
            or estimator == 'SVC':
            mode = 'classification'
    else:
        mode = 'regression'

    return (clf, params, mode)
