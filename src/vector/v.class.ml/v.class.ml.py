#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:            v.class.ml
#
# AUTHOR(S):   Pietro Zambelli (University of Trento)
#
# COPYRIGHT:        (C) 2013 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %Module
# % description: Classification of a vector maps based on the values in attribute tables
# % keyword: vector
# % keyword: classification
# % keyword: machine learning
# % overwrite: yes
# %End
# %option G_OPT_V_MAP
# % key: vector
# % description: Name of input vector map
# % required: yes
# %end
# %option G_OPT_V_MAP
# % key: vtraining
# % description: Name of training vector map
# % required: no
# %end
# %option
# % key: vlayer
# % type: string
# % multiple: no
# % description: layer name or number to use for data
# % required: no
# %end
# %option
# % key: tlayer
# % type: string
# % multiple: no
# % description: layer number/name for the training layer
# % required: no
# %end
# %option
# % key: rlayer
# % type: string
# % multiple: no
# % description: layer number/name for the ML results
# % required: no
# %end
# %option
# % key: npy_data
# % type: string
# % multiple: no
# % description: Data with statistics in npy format.
# % answer: data.npy
# % required: no
# %end
# %option
# % key: npy_cats
# % type: string
# % multiple: no
# % description: Numpy array with vector cats.
# % answer: cats.npy
# % required: no
# %end
# %option
# % key: npy_cols
# % type: string
# % multiple: no
# % description: Numpy array with columns names.
# % answer: cols.npy
# % required: no
# %end
# %option
# % key: npy_index
# % type: string
# % multiple: no
# % description: Boolean numpy array with training indexes.
# % answer: indx.npy
# % required: no
# %end
# %option
# % key: npy_tdata
# % type: string
# % multiple: no
# % description: training npy file with training set, default: training_data.npy
# % answer: training_data.npy
# % required: no
# %end
# %option
# % key: npy_tclasses
# % type: string
# % multiple: no
# % description: training npy file with the classes, default: training_classes.npy
# % answer: training_classes.npy
# % required: no
# %end
# %option
# % key: npy_btdata
# % type: string
# % multiple: no
# % description: training npy file with training set, default: training_data.npy
# % answer: Xbt.npy
# % required: no
# %end
# %option
# % key: npy_btclasses
# % type: string
# % multiple: no
# % description: training npy file with the classes, default: training_classes.npy
# % answer: Ybt.npy
# % required: no
# %end
# %option
# % key: imp_csv
# % type: string
# % multiple: no
# % description: CSV file name with the feature importances rank using extra tree algorithms
# % answer: features_importances.csv
# % required: no
# %end
# %option
# % key: imp_fig
# % type: string
# % multiple: no
# % description: Figure file name with feature importances rank using extra tree algorithms
# % answer: features_importances.png
# % required: no
# %end
# %option
# % key: scalar
# % type: string
# % multiple: yes
# % description: scaler method, center the data before scaling, if no, not scale at all
# % required: no
# % answer: with_mean,with_std
# %end
# %option
# % key: decomposition
# % type: string
# % multiple: no
# % description: choose a decomposition method (PCA, KernelPCA, ProbabilisticPCA, RandomizedPCA, FastICA, TruncatedSVD) and set the parameters using the | to separate the decomposition method from the parameters like: PCA|n_components=98
# % required: no
# % answer:
# %end
# %option
# % key: n_training
# % type: integer
# % multiple: no
# % description: Number of random training per class to training the machine learning algorithms
# % required: no
# %end
# %option
# % key: pyclassifiers
# % type: string
# % multiple: no
# % description: a python file with classifiers
# % required: no
# %end
# %option
# % key: pyvar
# % type: string
# % multiple: no
# % description: name of the python variable that must be a list of dictionary
# % required: no
# %end
# %option
# % key: pyindx
# % type: string
# % multiple: no
# % description: specify the index or range of index of the classifiers that you want to use
# % required: no
# %end
# %option
# % key: pyindx_optimize
# % type: string
# % multiple: no
# % description: Index of the classifiers to optimize the training set
# % required: no
# %end
# %option
# % key: nan
# % type: string
# % multiple: yes
# % description: Column pattern:Value or Numpy funtion to use to substitute NaN values
# % required: no
# % answer: *_skewness:nanmean,*_kurtosis:nanmean
# %end
# %option
# % key: inf
# % type: string
# % multiple: yes
# % description: Key:Value or Numpy funtion to use to substitute Inf values
# % required: no
# % answer: *_skewness:nanmean,*_kurtosis:nanmean
# %end
# %option
# % key: neginf
# % type: string
# % multiple: yes
# % description: Key:Value or Numpy funtion to use to substitute neginf values
# % required: no
# % answer:
# %end
# %option
# % key: posinf
# % type: string
# % multiple: yes
# % description: Key:Value or Numpy funtion to use to substitute posinf values
# % required: no
# % answer:
# %end
# %option
# % key: csv_test_cls
# % type: string
# % multiple: no
# % description: csv file name with results of different machine learning scores
# % required: no
# % answer: test_classifiers.csv
# %end
# %option
# % key: report_class
# % type: string
# % multiple: no
# % description: text file name with the report of different machine learning algorithms
# % required: no
# % answer: classification_report.txt
# %end
# %option
# % key: svc_c_range
# % type: double
# % multiple: yes
# % description: C value range list to explore SVC domain
# % required: no
# % answer: 1e-2,1e-1,1e0,1e1,1e2,1e3,1e4,1e5,1e6,1e7,1e8
# %end
# %option
# % key: svc_gamma_range
# % type: double
# % multiple: yes
# % description: gamma value range list to explore SVC domain
# % required: no
# % answer: 1e-6,1e-5,1e-4,1e-3,1e-2,1e-1,1e0,1e1,1e2,1e3,1e4
# %end
# %option
# % key: svc_kernel_range
# % type: string
# % multiple: yes
# % description: kernel value range list to explore SVC domain
# % required: no
# % answer: linear,poly,rbf,sigmoid
# %end
# %option
# % key: svc_poly_range
# % type: string
# % multiple: yes
# % description: polynomial order list to explore SVC domain
# % required: no
# % answer:
# %end
# %option
# % key: svc_n_jobs
# % type: integer
# % multiple: no
# % description: number of jobs to use during the domain exploration
# % required: no
# % answer: 1
# %end
# %option
# % key: svc_c
# % type: double
# % multiple: no
# % description: definitive C value
# % required: no
# %end
# %option
# % key: svc_gamma
# % type: double
# % multiple: no
# % description: definitive gamma value
# % required: no
# %end
# %option
# % key: svc_kernel
# % type: string
# % multiple: no
# % description: definitive kernel value. Available kernel are: 'linear', 'poly', 'rbf', 'sigmoid', 'precomputed'
# % required: no
# % answer: rbf
# %end
# %option
# % key: svc_img
# % type: string
# % multiple: no
# % description: filename pattern with the image of SVC parameter
# % required: no
# % answer: domain_%s.svg
# %end
# %option
# % key: rst_names
# % type: string
# % multiple: no
# % description: filename pattern for raster
# % required: no
# % answer: %s
# %end
# -----------------------------------------------------
# %flag
# % key: e
# % description: Extract the training set from the vtraining map
# %end
# %flag
# % key: n
# % description: Export to numpy files
# %end
# %flag
# % key: f
# % description: Feature importances using extra trees algorithm
# %end
# %flag
# % key: b
# % description: Balance the training using the class with the minor number of data
# %end
# %flag
# % key: o
# % description: Optimize the training samples
# %end
# %flag
# % key: c
# % description: Classify the whole dataset
# %end
# %flag
# % key: r
# % description: Export the classify results to raster maps
# %end
# %flag
# % key: t
# % description: Test different classification methods
# %end
# %flag
# % key: v
# % description: add to test to compute the Bias variance
# %end
# %flag
# % key: x
# % description: add to test to compute extra parameters like: confusion matrix, ROC, PR
# %end
# %flag
# % key: d
# % description: Explore the SVC domain
# %end
# %flag
# % key: a
# % description: append the classification results
# %end
# -----------------------------------------------------
from __future__ import absolute_import, division, print_function, unicode_literals
from importlib.machinery import SourceFileLoader
import sys
import os
from pprint import pprint
from fnmatch import fnmatch

import numpy as np

from grass.pygrass.utils import set_path
from grass.pygrass.messages import get_msgr
from grass.pygrass.vector import Vector
from grass.pygrass.modules import Module
from grass.script.core import parser, overwrite

set_path("v.class.ml")

from training_extraction import extract_training
from sqlite2npy import save2npy
from npy2table import export_results


DECMP = {}


def load_decompositions():
    """Import decompositions and update dictionary which stores them"""
    from sklearn.decomposition import (
        PCA,
        KernelPCA,
        ProbabilisticPCA,
        RandomizedPCA,
        FastICA,
        TruncatedSVD,
    )
    from sklearn.lda import LDA

    DECMP.update(
        {
            "PCA": PCA,
            "KernelPCA": KernelPCA,
            "ProbabilisticPCA": ProbabilisticPCA,
            "RandomizedPCA": RandomizedPCA,
            "FastICA": FastICA,
            "TruncatedSVD": TruncatedSVD,
            "LDA": LDA,
        }
    )


def get_indexes(string, sep=",", rangesep="-"):
    """
    >>> indx = '1-5,34-36,40'
    >>> [i for i in get_indexes(indx)]
    [1, 2, 3, 4, 5, 34, 35, 36, 40]
    """
    for ind in string.split(sep):
        if rangesep in ind:
            start, stop = ind.split(rangesep)
            for i in range(int(start), int(stop) + 1):
                yield i
        else:
            yield int(ind)


def get_colors(vtraining):
    vect, mset = vtraining.split("@") if "@" in vtraining else (vtraining, "")
    with Vector(vect, mapset=mset, mode="r") as vct:
        cur = vct.table.execute("SELECT cat, color FROM %s;" % vct.name)
        return dict([c for c in cur.fetchall()])


def convert(string):
    try:
        return float(string)
    except:
        try:
            return getattr(np, string)
        except AttributeError:
            msg = "Not a valid option, is not a number or a numpy function."
            raise TypeError(msg)


def get_rules(string):
    res = {}
    pairs = [s.strip().split(":") for s in string.strip().split(",")]
    for key, val in pairs:
        res[key] = convert(val)
    return res


def find_special_cols(
    array, cols, report=True, special=("nan", "inf", "neginf", "posinf")
):
    sp = {key: [] for key in special}
    cntr = {key: [] for key in special}
    for i in range(len(cols)):
        for key in special:
            barray = getattr(np, "is%s" % key)(array[:, i])
            if barray.any():
                sp[key].append(i)
                cntr[key].append(barray.sum())
    if report:
        indent = "    "
        tot = len(array)
        for k in special:
            fmt = "- %15s (%3d/%d, %4.3f%%)"
            if sp[k]:
                strs = [
                    fmt % (col, cnt, tot, cnt / float(tot) * 100)
                    for col, cnt in zip(cols[np.array(sp[k])], cntr[k])
                ]
                print("%s:\n%s" % (k, indent), ("\n%s" % indent).join(strs), sep="")
    return sp


def substitute(X, rules, cols):
    vals = {}
    special_cols = find_special_cols(X, cols)
    pprint(special_cols)
    for key in rules.keys():
        vals[key] = {}
        for i in special_cols[key]:
            for rule in rules[key]:
                if fnmatch(cols[i], rule):
                    indx = getattr(np, "is%s" % key)(X[:, i])
                    val = (
                        rules[key][rule]
                        if np.isscalar(rules[key][rule])
                        else rules[key][rule](X[:, i][~indx])
                    )
                    X[:, i][indx] = val
                    vals[key][cols[i]] = val
    return X, vals


def extract_classes(vect, layer):
    vect, mset = vect.split("@") if "@" in vect else (vect, "")
    with Vector(vect, mapset=mset, layer=layer, mode="r") as vct:
        vct.table.filters.select("cat", "class")
        return {key: val for key, val in vct.table.execute()}


def main(opt, flg):
    # import functions which depend on sklearn only after parser run
    from ml_functions import (
        balance,
        explorer_clsfiers,
        run_classifier,
        optimize_training,
        explore_SVC,
        plot_grid,
    )
    from features import importances, tocsv

    msgr = get_msgr()
    indexes = None
    vect = opt["vector"]
    vtraining = opt["vtraining"] if opt["vtraining"] else None
    scaler, decmp = None, None
    vlayer = opt["vlayer"] if opt["vlayer"] else vect + "_stats"
    tlayer = opt["tlayer"] if opt["tlayer"] else vect + "_training"
    rlayer = opt["rlayer"] if opt["rlayer"] else vect + "_results"

    labels = extract_classes(vtraining, 1)
    pprint(labels)

    if opt["scalar"]:
        scapar = opt["scalar"].split(",")
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler(
            with_mean="with_mean" in scapar, with_std="with_std" in scapar
        )

    if opt["decomposition"]:
        dec, params = (
            opt["decomposition"].split("|")
            if "|" in opt["decomposition"]
            else (opt["decomposition"], "")
        )
        kwargs = (
            {k: v for k, v in (p.split("=") for p in params.split(","))}
            if params
            else {}
        )
        load_decompositions()
        decmp = DECMP[dec](**kwargs)

    # if training extract training
    if vtraining and flg["e"]:
        msgr.message("Extract training from: <%s> to <%s>." % (vtraining, vect))
        extract_training(vect, vtraining, tlayer)
        flg["n"] = True

    if flg["n"]:
        msgr.message("Save arrays to npy files.")
        save2npy(
            vect,
            vlayer,
            tlayer,
            fcats=opt["npy_cats"],
            fcols=opt["npy_cols"],
            fdata=opt["npy_data"],
            findx=opt["npy_index"],
            fclss=opt["npy_tclasses"],
            ftdata=opt["npy_tdata"],
        )

    # define the classifiers to use/test
    if opt["pyclassifiers"] and opt["pyvar"]:
        # import classifiers to use
        mycls = SourceFileLoader("mycls", opt["pyclassifiers"]).load_module()
        classifiers = getattr(mycls, opt["pyvar"])
    else:
        from ml_classifiers import CLASSIFIERS

        classifiers = CLASSIFIERS

    # Append the SVC classifier
    if opt["svc_c"] and opt["svc_gamma"]:
        from sklearn.svm import SVC

        svc = {
            "name": "SVC",
            "classifier": SVC,
            "kwargs": {
                "C": float(opt["svc_c"]),
                "gamma": float(opt["svc_gamma"]),
                "kernel": opt["svc_kernel"],
            },
        }
        classifiers.append(svc)

    # extract classifiers from pyindx
    if opt["pyindx"]:
        indexes = [i for i in get_indexes(opt["pyindx"])]
        classifiers = [classifiers[i] for i in indexes]

    num = int(opt["n_training"]) if opt["n_training"] else None

    # load fron npy files
    Xt = np.load(opt["npy_tdata"])
    Yt = np.load(opt["npy_tclasses"])
    cols = np.load(opt["npy_cols"])

    # Define rules to substitute NaN, Inf, posInf, negInf values
    rules = {}
    for key in ("nan", "inf", "neginf", "posinf"):
        if opt[key]:
            rules[key] = get_rules(opt[key])
    pprint(rules)

    # Substitute (skip cat column)
    Xt, rules_vals = substitute(Xt, rules, cols[1:])
    Xtoriginal = Xt

    # scale the data
    if scaler:
        msgr.message("Scaling the training data set.")
        scaler.fit(Xt, Yt)
        Xt = scaler.transform(Xt)

    # decompose data
    if decmp:
        msgr.message("Decomposing the training data set.")
        decmp.fit(Xt)
        Xt = decmp.transform(Xt)

    # Feature importances with forests of trees
    if flg["f"]:
        np.save("training_transformed.npy", Xt)
        importances(
            Xt,
            Yt,
            cols[1:],
            csv=opt["imp_csv"],
            img=opt["imp_fig"],
            # default parameters to save the matplotlib figure
            **dict(dpi=300, transparent=False, bbox_inches="tight")
        )

    # optimize the training set
    if flg["o"]:
        ind_optimize = int(opt["pyindx_optimize"]) if opt["pyindx_optimize"] else 0
        cls = classifiers[ind_optimize]
        msgr.message("Find the optimum training set.")
        best, Xbt, Ybt = optimize_training(
            cls,
            Xt,
            Yt,
            labels,  # {v: k for k, v in labels.items()},
            scaler,
            decmp,
            num=num,
            maxiterations=1000,
        )
        msg = "    - save the optimum training data set to: %s."
        msgr.message(msg % opt["npy_btdata"])
        np.save(opt["npy_btdata"], Xbt)
        msg = "    - save the optimum training classes set to: %s."
        msgr.message(msg % opt["npy_btclasses"])
        np.save(opt["npy_btclasses"], Ybt)

    # balance the data
    if flg["b"]:
        msg = "Balancing the training data set, each class have <%d> samples."
        msgr.message(msg % num)
        Xbt, Ybt = balance(Xt, Yt, num)
    else:
        if not flg["o"]:
            Xbt = (
                np.load(opt["npy_btdata"]) if os.path.isfile(opt["npy_btdata"]) else Xt
            )
            Ybt = (
                np.load(opt["npy_btclasses"])
                if os.path.isfile(opt["npy_btclasses"])
                else Yt
            )

    # scale the data
    if scaler:
        msgr.message("Scaling the training data set.")
        scaler.fit(Xbt, Ybt)
        Xt = scaler.transform(Xt)
        Xbt = scaler.transform(Xbt)

    if flg["d"]:
        C_range = [float(c) for c in opt["svc_c_range"].split(",") if c]
        gamma_range = [float(g) for g in opt["svc_gamma_range"].split(",") if g]
        kernel_range = [str(s) for s in opt["svc_kernel_range"].split(",") if s]
        poly_range = [int(i) for i in opt["svc_poly_range"].split(",") if i]
        allkwargs = dict(
            C=C_range, gamma=gamma_range, kernel=kernel_range, degree=poly_range
        )
        kwargs = {}
        for k in allkwargs:
            if allkwargs[k]:
                kwargs[k] = allkwargs[k]
        msgr.message("Exploring the SVC domain.")
        grid = explore_SVC(Xbt, Ybt, n_folds=5, n_jobs=int(opt["svc_n_jobs"]), **kwargs)
        import pickle

        krnlstr = "_".join(s for s in opt["svc_kernel_range"].split(",") if s)
        pkl = open("grid%s.pkl" % krnlstr, "w")
        pickle.dump(grid, pkl)
        pkl.close()
        #        pkl = open('grid.pkl', 'r')
        #        grid = pickle.load(pkl)
        #        pkl.close()
        plot_grid(grid, save=opt["svc_img"])

    # test the accuracy of different classifiers
    if flg["t"]:
        # test different classifiers
        msgr.message("Exploring different classifiers.")
        msgr.message("cls_id   cls_name          mean     max     min     std")

        res = explorer_clsfiers(
            classifiers,
            Xt,
            Yt,
            labels=labels,
            indexes=indexes,
            n_folds=5,
            bv=flg["v"],
            extra=flg["x"],
        )
        # TODO: sort(order=...) is working only in the terminal, why?
        # res.sort(order='mean')
        with open(opt["csv_test_cls"], "w") as csv:
            csv.write(tocsv(res))

    if flg["c"]:
        # classify
        data = np.load(opt["npy_data"])
        indx = np.load(opt["npy_index"])

        # Substitute using column values
        data, dummy = substitute(data, rules, cols[1:])
        Xt = data[indx]

        if scaler:
            msgr.message("Scaling the training data set.")
            scaler.fit(Xt, Yt)
            Xt = scaler.transform(Xt)
            msgr.message("Scaling the whole data set.")
            data = scaler.transform(data)
        if decmp:
            msgr.message("Decomposing the training data set.")
            decmp.fit(Xt)
            Xt = decmp.transform(Xt)
            msgr.message("Decompose the whole data set.")
            data = decmp.transform(data)
        cats = np.load(opt["npy_cats"])

        np.save("data_filled_scaled.npy", data)
        tcols = []
        for cls in classifiers:
            report = (
                open(opt["report_class"], "w") if opt["report_class"] else sys.stdout
            )
            run_classifier(cls, Xt, Yt, Xt, Yt, labels, data, report=report)
            tcols.append((cls["name"], "INTEGER"))

        import pickle

        with open("classification_results.pkl", "w") as res:
            pickle.dump(classifiers, res)
        # classifiers = pickle.load(res)
        msgr.message("Export the results to layer: <%s>" % str(rlayer))
        export_results(
            vect,
            classifiers,
            cats,
            rlayer,
            vtraining,
            tcols,
            overwrite(),
            pkl="res.pkl",
            append=flg["a"],
        )
    #        res.close()

    if flg["r"]:
        rules = (
            "\n".join(["%d %s" % (k, v) for k, v in get_colors(vtraining).items()])
            if vtraining
            else None
        )

        msgr.message("Export the layer with results to raster")
        with Vector(vect, mode="r") as vct:
            tab = vct.dblinks.by_name(rlayer).table()
            rasters = [c for c in tab.columns]
            rasters.remove(tab.key)

        v2rst = Module("v.to.rast")
        rclrs = Module("r.colors")
        for rst in rasters:
            v2rst(
                input=vect,
                layer=rlayer,
                type="area",
                use="attr",
                attrcolumn=rst.encode(),
                output=(opt["rst_names"] % rst).encode(),
                memory=1000,
                overwrite=overwrite(),
            )
            if rules:
                rclrs(map=rst.encode(), rules="-", stdin_=rules)


if __name__ == "__main__":
    main(*parser())
