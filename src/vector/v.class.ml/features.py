#!/usr/bin/env python
# -- coding: utf-8 --
from __future__ import absolute_import, division, print_function

import numpy as np
import matplotlib  # required by windows

matplotlib.use("wxAGG")  # required by windows
import matplotlib.pyplot as plt

from sklearn.ensemble import ExtraTreesClassifier


N_ESTIMATORS = 500
RANDOM_STATE = 0


IMP_DTYPE = [("col", "<U24"), ("imp", "f"), ("std", "f")]


def tocsv(array, sep=";", fmt="%s"):
    return "\n".join([sep.join([fmt % el for el in row]) for row in array])


def importances(
    X,
    y,
    cols,
    csv="",
    img="",
    clf=ExtraTreesClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE),
    **savefig,
):
    clf.fit(X, y)
    imp = clf.feature_importances_
    std = np.std([est.feature_importances_ for est in clf.estimators_], axis=0)
    res = np.array([(c, i, s) for c, i, s in zip(cols, imp, std)], dtype=IMP_DTYPE)
    res.sort(order="imp")
    res = res[::-1]
    if csv:
        with open(csv, "w") as csv:
            csv.write(tocsv(res))
    if img:
        fig, ax = plt.subplots(figsize=(5, 40))
        pos = range(len(cols))
        ax.barh(pos, res["imp"] * 100, align="center", alpha=0.4)
        ax.set_yticks(pos)
        ax.set_yticklabels(res["col"])
        ax.set_xlabel("Importance [%]")
        ax.set_title("Feature importances")
        ax.grid()
        fig.savefig(img, **savefig)
    return res
