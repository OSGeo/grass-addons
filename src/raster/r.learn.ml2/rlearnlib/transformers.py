import importlib

import numpy as np
import grass.script as gs


class ImportSklearnModule:
    """Lazy import of 'sklearn' module"""

    try:
        sklearn_base = importlib.import_module("sklearn.base")
    except:
        gs.fatal("Package python3-scikit-learn 0.20 or newer is not installed")


class CategoryEncoder(
    ImportSklearnModule.sklearn_base.BaseEstimator,
    ImportSklearnModule.sklearn_base.TransformerMixin,
):
    """Transformer to encode GRASS GIS category labels into integer labels"""

    def __init__(self):
        self._encoding = None
        self._inverse = None

    def fit(self, X, y=None):
        self._encoding = {value: label for (label, value, mtype) in X}
        self._inverse = {label: value for (label, value, mtype) in X}
        return self

    def transform(self, X, y=None):
        """Takes integer values and returns the category label"""
        return np.asarray([self._encoding[x] for x in X]).astype(np.object)

    def inverse_transform(self, X, y=None):
        """Takes a category label and returns the category index"""
        return np.asarray([self._inverse[x] for x in X]).astype(np.object)
