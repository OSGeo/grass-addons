# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 15:08:38 2013

@author: pietro
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from gettext import lgettext as _

from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import (NearestNeighbors,
                               KNeighborsClassifier,
                               RadiusNeighborsClassifier,
                               NearestCentroid)
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB


from grass.pygrass.messages import Messenger

MSGR = Messenger()

try:
    import mlpy
except ImportError:
    MSGR.warning(_("MLPY not found in the current python path"
                   "check that is installed or set the python path."
                   "Only `sklearn` will be used."))
    mlpy = None


COLS = [('cat', 'INTEGER PRIMARY KEY'),
        ('class', 'INTEGER'),
        ('color', 'VARCHAR(11)'), ]


# Unsupervisioned
#nbrs = NearestNeighbors(n_neighbors=8,
#                        algorithm='ball_tree').fit(data)
#distances, indices = nbrs.kneighbors(data)


CLASSIFIERS = [
    #
    # Stochastic Gradient Descent (SGD)
    #
    {'name': 'sgd_hinge_l2', 'classifier': SGDClassifier,
     'kwargs': {'loss': "hinge", 'penalty': "l2"}},
    {'name': 'sgd_huber_l2', 'classifier': SGDClassifier,
     'kwargs': {'loss': "modified_huber", 'penalty': "l2"}},
    {'name': 'sgd_log_l2', 'classifier': SGDClassifier,
     'kwargs': {'loss': "log", 'penalty': "l2"}},
    {'name': 'sgd_hinge_l1', 'classifier': SGDClassifier,
     'kwargs': {'loss': "hinge", 'penalty': "l1"}},
    {'name': 'sgd_huber_l1', 'classifier': SGDClassifier,
     'kwargs': {'loss': "modified_huber", 'penalty': "l1"}},
    {'name': 'sgd_log_l1', 'classifier': SGDClassifier,
     'kwargs': {'loss': "log", 'penalty': "l1"}},
    {'name': 'sgd_hinge_elastic', 'classifier': SGDClassifier,
     'kwargs': {'loss': "hinge", 'penalty': "elasticnet"}},
    {'name': 'sgd_huber_elastic', 'classifier': SGDClassifier,
     'kwargs': {'loss': "modified_huber", 'penalty': "elasticnet"}},
    {'name': 'sgd_log_elastic', 'classifier': SGDClassifier,
     'kwargs': {'loss': "log", 'penalty': "elasticnet"}},
    #
    # K-NN
    #
    # uniform
    {'name': 'knn2_uniform', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 2, 'weights': 'uniform'}},
    {'name': 'knn4_uniform', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 4, 'weights': 'uniform'}},
    {'name': 'knn8_uniform', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 8, 'weights': 'uniform'}},
    {'name': 'knn16_uniform', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 16, 'weights': 'uniform'}},
    # distance
    {'name': 'knn2_distance', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 2, 'weights': 'distance'}},
    {'name': 'knn4_distance', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 4, 'weights': 'distance'}},
    {'name': 'knn8_distance', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 8, 'weights': 'distance'}},
    {'name': 'knn16_distance', 'classifier': KNeighborsClassifier,
     'kwargs': {'n_neighbors': 16, 'weights': 'distance'}},
    # radius
    {'name': 'knn_radius_0p5_uniform',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 0.5, 'weights': 'uniform'}},
    {'name': 'knn_radius_1_uniform',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 1., 'weights': 'uniform'}},
    {'name': 'knn_radius_1p5_uniform',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 1.5, 'weights': 'uniform'}},
    {'name': 'knn_radius_2_uniform',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 2., 'weights': 'uniform'}},
    {'name': 'knn_radius_2p5_uniform',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 2.5, 'weights': 'uniform'}},
    {'name': 'knn_radius_5_uniform',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 5., 'weights': 'uniform'}},

    {'name': 'knn_radius_0p5_distance',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 0.5, 'weights': 'distance'}},
    {'name': 'knn_radius_1_distance',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 1., 'weights': 'distance'}},
    {'name': 'knn_radius_1p5_distance',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 1.5, 'weights': 'distance'}},
    {'name': 'knn_radius_2_distance',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 2., 'weights': 'distance'}},
    {'name': 'knn_radius_2p5_distance',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 2.5, 'weights': 'distance'}},
    {'name': 'knn_radius_5_distance',
     'classifier': RadiusNeighborsClassifier,
     'kwargs': {'radius': 5., 'weights': 'distance'}},
    # centroid
    # ‘euclidean’, ‘l2’, ‘l1’, ‘manhattan’, ‘cityblock’
    #  [‘braycurtis’, ‘canberra’, ‘chebyshev’, ‘correlation’, ‘cosine’, ‘dice’, ‘hamming’, ‘jaccard’, ‘kulsinski’, ‘mahalanobis’, ‘matching’, ‘minkowski’, ‘rogerstanimoto’, ‘russellrao’, ‘seuclidean’, ‘sokalmichener’, ‘sokalsneath’, ‘sqeuclidean’, ‘yule’]
    {'name': 'knn_centroid_euclidean_none', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'euclidean', 'shrink_threshold ': None}},
    {'name': 'knn_centroid_euclidean_0p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'euclidean', 'shrink_threshold ': 0.5}},
    {'name': 'knn_centroid_euclidean_1', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'euclidean', 'shrink_threshold ': 1.0}},
    {'name': 'knn_centroid_euclidean_1p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'euclidean', 'shrink_threshold ': 1.5}},
    {'name': 'knn_centroid_euclidean_2', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'euclidean', 'shrink_threshold ': 2.0}},

    {'name': 'knn_centroid_l2_none', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l2', 'shrink_threshold ': None}},
    {'name': 'knn_centroid_l2_0p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l2', 'shrink_threshold ': 0.5}},
    {'name': 'knn_centroid_l2_1', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l2', 'shrink_threshold ': 1.0}},
    {'name': 'knn_centroid_l2_1p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l2', 'shrink_threshold ': 1.5}},
    {'name': 'knn_centroid_l2_2', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l2', 'shrink_threshold ': 2.0}},

    {'name': 'knn_centroid_l1_none', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l1', 'shrink_threshold ': None}},
    {'name': 'knn_centroid_l1_0p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l1', 'shrink_threshold ': 0.5}},
    {'name': 'knn_centroid_l1_1', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l1', 'shrink_threshold ': 1.0}},
    {'name': 'knn_centroid_l1_1p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l1', 'shrink_threshold ': 1.5}},
    {'name': 'knn_centroid_l1_2', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'l1', 'shrink_threshold ': 2.0}},

    {'name': 'knn_centroid_manhattan_none', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'manhattan', 'shrink_threshold ': None}},
    {'name': 'knn_centroid_manhattan_0p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'manhattan', 'shrink_threshold ': 0.5}},
    {'name': 'knn_centroid_manhattan_1', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'manhattan', 'shrink_threshold ': 1.0}},
    {'name': 'knn_centroid_manhattan_1p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'manhattan', 'shrink_threshold ': 1.5}},
    {'name': 'knn_centroid_manhattan_2', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'manhattan', 'shrink_threshold ': 2.0}},

    {'name': 'knn_centroid_cityblock_none', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'cityblock', 'shrink_threshold ': None}},
    {'name': 'knn_centroid_cityblock_0p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'cityblock', 'shrink_threshold ': 0.5}},
    {'name': 'knn_centroid_cityblock_1', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'cityblock', 'shrink_threshold ': 1.0}},
    {'name': 'knn_centroid_cityblock_1p5', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'cityblock', 'shrink_threshold ': 1.5}},
    {'name': 'knn_centroid_cityblock_2', 'classifier': NearestCentroid,
     'kwargs': {'metric': 'cityblock', 'shrink_threshold ': 2.0}},
    #
    # Tree
    #
    {'name': 'd_tree_gini', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'gini', 'splitter': 'best', 'max_depth': None,
                'min_samples_split': 2, 'min_samples_leaf': 1,
                'max_features': None, 'random_state': None,
                'min_density': None}},
    {'name': 'd_tree_gini_sqrt', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 'sqrt'}},
    {'name': 'd_tree_gini_log2', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 'log2'}},
    {'name': 'd_tree_gini_0p25', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 0.25}},
    {'name': 'd_tree_gini_0p50', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 0.5}},
    {'name': 'd_tree_gini_0p75', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 0.75}},

    {'name': 'd_tree_entropy', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'entropy', 'splitter': 'best', 'max_depth': None,
                'min_samples_split': 2, 'min_samples_leaf': 1,
                'max_features': None, 'random_state': None,
                'min_density': None}},
    {'name': 'd_tree_entropy_sqrt', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 'sqrt'}},
    {'name': 'd_tree_entropy_log2', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 'log2'}},
    {'name': 'd_tree_entropy_0p25', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 0.25}},
    {'name': 'd_tree_entropy_0p50', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 0.5}},
    {'name': 'd_tree_entropy_0p75', 'classifier': DecisionTreeClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 0.75}},

    {'name': 'rand_tree_gini', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'gini', 'splitter': 'best', 'max_depth': None,
                'min_samples_split': 2, 'min_samples_leaf': 1,
                'max_features': None, 'random_state': None,
                'min_density': None}},
    {'name': 'rand_tree_gini_sqrt', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 'sqrt'}},
    {'name': 'rand_tree_gini_log2', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 'log2'}},
    {'name': 'rand_tree_gini_0p25', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 0.25}},
    {'name': 'rand_tree_gini_0p50', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 0.5}},
    {'name': 'rand_tree_gini_0p75', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'gini', 'max_depth': 0.75}},

    {'name': 'rand_tree_entropy', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'entropy', 'splitter': 'best', 'max_depth': None,
                'min_samples_split': 2, 'min_samples_leaf': 1,
                'max_features': None, 'random_state': None,
                'min_density': None}},
    {'name': 'rand_tree_entropy_sqrt', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 'sqrt'}},
    {'name': 'rand_tree_entropy_log2', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 'log2'}},
    {'name': 'rand_tree_entropy_0p25', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 0.25}},
    {'name': 'rand_tree_entropy_0p50', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 0.5}},
    {'name': 'rand_tree_entropy_0p75', 'classifier': RandomForestClassifier,
     'kwargs': {'criterion': 'entropy', 'max_depth': 0.75}},

    #
    # Gausian
    #
    {'name': 'gaussianNB', 'classifier': GaussianNB},
]


class MLPYWrapper(object):
    def __init__(self, cls):
        self.cls = cls
        self.mlcls = None
        self.wrap = dict(fit='learn', predict='pred')

    def __getattr__(self, name):
        if self.mlcls and name in self.wrap.keys():
            return getattr(self.mlcls, self.wrap[name])
        return super(MLPYWrapper, self).__getattr__(self, name)

    def __call__(self, *args, **kwargs):
        self.mlcls = self.cls(*args, **kwargs)


if mlpy is not None:
    MLPY_CLS = [
        #
        # Linear Discriminant Analysis Classifier (LDAC)
        #
        {'name': 'mlpy_LDAC_1', 'classifier': MLPYWrapper(mlpy.LDAC)},
        #
        # Elastic Net Classifier
        #
        {'name': 'mlpy_ElasticNetC_0.1_0.1',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.1, 'eps': 0.1, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.1_0.01',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.1, 'eps': 0.01, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.1_0.001',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.1, 'eps': 0.001, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.01_0.1',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.01, 'eps': 0.1, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.01_0.01',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.01, 'eps': 0.01, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.01_0.001',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.01, 'eps': 0.001, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.001_0.1',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.001, 'eps': 0.1, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.001_0.01',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.001, 'eps': 0.01, 'supp': True, 'tol': 0.01}},
        {'name': 'mlpy_ElasticNetC_0.001_0.001',
         'classifier': MLPYWrapper(mlpy.ElasticNetC),
         'kwargs': {'lmb': 0.001, 'eps': 0.001, 'supp': True, 'tol': 0.01}},
        #
        # Diagonal Linear Discriminant Analysis (DLDA)
        #
        {'name': 'mlpy_DLDA_0.01', 'classifier': MLPYWrapper(mlpy.DLDA),
         'kwargs': {'delta': 0.01}},
        {'name': 'mlpy_DLDA_0.05', 'classifier': MLPYWrapper(mlpy.DLDA),
         'kwargs': {'delta': 0.05}},
        {'name': 'mlpy_DLDA_0.1', 'classifier': MLPYWrapper(mlpy.DLDA),
         'kwargs': {'delta': 0.1}},
        {'name': 'mlpy_DLDA_0.5', 'classifier': MLPYWrapper(mlpy.DLDA),
         'kwargs': {'delta': 0.5}},
        #
        # mlpy.Golub
        #
        {'name': 'mlpy_Golub', 'classifier': MLPYWrapper(mlpy.Golub)},
        #
        # LibLinear
        #
        {'name': 'mlpy_liblin_l2r_lr',
         'classifier': MLPYWrapper(mlpy.LibLinear),
         'kwargs': {'solver_type': 'l2r_lr', 'C': 1, 'eps': 0.01}},
        {'name': 'mlpy_liblin_l2r_l2loss_svc',
         'classifier': MLPYWrapper(mlpy.LibLinear),
         'kwargs': {'solver_type': 'l2r_l2loss_svc', 'C': 1, 'eps': 0.01}},
        {'name': 'mlpy_liblin_l2r_l1loss_svc_dual',
         'classifier': MLPYWrapper(mlpy.LibLinear),
         'kwargs': {'solver_type': 'l2r_l1loss_svc_dual',
                    'C': 1, 'eps': 0.01}},
        {'name': 'mlpy_liblin_mcsvm_cs',
         'classifier': MLPYWrapper(mlpy.LibLinear),
         'kwargs': {'solver_type': 'mcsvm_cs', 'C': 1, 'eps': 0.01}},
        {'name': 'mlpy_liblin_l1r_l2loss_svc',
         'classifier': MLPYWrapper(mlpy.LibLinear),
         'kwargs': {'solver_type': 'l1r_l2loss_svc', 'C': 1, 'eps': 0.01}},
        {'name': 'mlpy_liblin_l1r_lr',
         'classifier': MLPYWrapper(mlpy.LibLinear),
         'kwargs': {'solver_type': 'l1r_lr', 'C': 1, 'eps': 0.01}},
        {'name': 'mlpy_liblin_l2r_lr_dual',
         'classifier': MLPYWrapper(mlpy.LibLinear),
         'kwargs': {'solver_type': 'l2r_lr_dual', 'C': 1, 'eps': 0.01}},
        #
        # K-NN
        #
        {'name': 'mlpy_KNN_1', 'classifier': MLPYWrapper(mlpy.KNN),
         'kwargs': {'k': 1}},
        {'name': 'mlpy_KNN_2', 'classifier': MLPYWrapper(mlpy.KNN),
         'kwargs': {'k': 2}},
        {'name': 'mlpy_KNN_3', 'classifier': MLPYWrapper(mlpy.KNN),
         'kwargs': {'k': 3}},
        {'name': 'mlpy_KNN_4', 'classifier': MLPYWrapper(mlpy.KNN),
         'kwargs': {'k': 4}},
        {'name': 'mlpy_KNN_8', 'classifier': MLPYWrapper(mlpy.KNN),
         'kwargs': {'k': 8}},
        {'name': 'mlpy_KNN_8', 'classifier': MLPYWrapper(mlpy.KNN),
         'kwargs': {'k': 16}},
        #
        # Tree
        #
        {'name': 'mlpy_tree_0_0', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 0, 'minsize': 0}},
        {'name': 'mlpy_tree_0_5', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 0, 'minsize': 5}},
        {'name': 'mlpy_tree_0_10', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 0, 'minsize': 10}},
        {'name': 'mlpy_tree_0_20', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 0, 'minsize': 20}},
        {'name': 'mlpy_tree_0_40', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 0, 'minsize': 40}},
        {'name': 'mlpy_tree_1_', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 1, 'minsize': 0}},
        {'name': 'mlpy_tree_1_5', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 1, 'minsize': 5}},
        {'name': 'mlpy_tree_1_10', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 1, 'minsize': 10}},
        {'name': 'mlpy_tree_1_20', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 1, 'minsize': 20}},
        {'name': 'mlpy_tree_1_40', 'classifier': MLPYWrapper(mlpy.ClassTree),
         'kwargs': {'stumps': 1, 'minsize': 40}},
        #
        # mlpy.MaximumLikelihoodC
        #
        #{'name': 'mlpy_maximumlike',
        # 'classifier': MLPYWrapper(mlpy.MaximumLikelihoodC)},
    ]
    # add MLPY
    CLASSIFIERS.extend(MLPY_CLS)
