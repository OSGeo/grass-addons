#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:	    v.class.ml
#
# AUTHOR(S):   Pietro Zambelli (University of Trento)
#
# COPYRIGHT:	(C) 2013 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#%  description: Vector
#%  keywords: machine learning
#%  keywords: classification
#%  overwrite: yes
#%End
#%option G_OPT_V_MAP
#%  key: vector
#%  description: Name of input vector map
#%  required: yes
#%end
#%option G_OPT_V_MAP
#%  key: vtraining
#%  description: Name of training vector map
#%  required: no
#%end
#%option
#%  key: vlayer
#%  type: string
#%  multiple: no
#%  description: layer name or number to use for the machine learning
#%  required: no
#%end
#%option
#%  key: tlayer
#%  type: string
#%  multiple: no
#%  description: layer number/name for the training layer
#%  required: no
#%end
#%option
#%  key: rlayer
#%  type: string
#%  multiple: no
#%  description: layer number/name for the ML results
#%  required: no
#%end
#%option
#%  key: npy_data
#%  type: string
#%  multiple: no
#%  description: Data with statistics in npy format.
#%  answer: data.npy
#%  required: no
#%end
#%option
#%  key: npy_cats
#%  type: string
#%  multiple: no
#%  description: Numpy array with vector cats.
#%  answer: cats.npy
#%  required: no
#%end
#%option
#%  key: npy_cols
#%  type: string
#%  multiple: no
#%  description: Numpy array with columns names.
#%  answer: cols.npy
#%  required: no
#%end
#%option
#%  key: npy_index
#%  type: string
#%  multiple: no
#%  description: Boolean numpy array with training indexes.
#%  answer: indx.npy
#%  required: no
#%end
#%option
#%  key: npy_tdata
#%  type: string
#%  multiple: no
#%  description: training npy file with training set, default: training_data.npy
#%  answer: training_data.npy
#%  required: no
#%end
#%option
#%  key: npy_tclasses
#%  type: string
#%  multiple: no
#%  description: training npy file with the classes, default: training_classes.npy
#%  answer: training_classes.npy
#%  required: no
#%end
#%option
#%  key: npy_btdata
#%  type: string
#%  multiple: no
#%  description: training npy file with training set, default: training_data.npy
#%  answer: Xbt.npy
#%  required: no
#%end
#%option
#%  key: npy_btclasses
#%  type: string
#%  multiple: no
#%  description: training npy file with the classes, default: training_classes.npy
#%  answer: Ybt.npy
#%  required: no
#%end
#%option
#%  key: imp_csv
#%  type: string
#%  multiple: no
#%  description: Feature importances with forests of trees: CSV
#%  answer: features_importances.csv
#%  required: no
#%end
#%option
#%  key: imp_fig
#%  type: string
#%  multiple: no
#%  description: Feature importances with forests of trees: figure
#%  answer: features_importances.png
#%  required: no
#%end
#%option
#%  key: scalar
#%  type: string
#%  multiple: yes
#%  description: scaler method, center the data before scaling, if no, not scale at all
#%  required: no
#%  answer: with_mean,with_std
#%end
#%option
#%  key: n_training
#%  type: integer
#%  multiple: no
#%  description: Number of random training to training the machine learning
#%  required: no
#%end
#%option
#%  key: pyclassifiers
#%  type: string
#%  multiple: no
#%  description: a python file with classifiers
#%  required: no
#%end
#%option
#%  key: pyvar
#%  type: string
#%  multiple: no
#%  description: name of the python variable that must be a list of dictionary
#%  required: no
#%end
#%option
#%  key: pyindx
#%  type: string
#%  multiple: no
#%  description: specify the index of the classifiers that you want to use
#%  required: no
#%end
#%option
#%  key: pyindx_optimize
#%  type: string
#%  multiple: no
#%  description: Index of the classifiers to optimize the training set
#%  required: no
#%end
#%option
#%  key: nan
#%  type: string
#%  multiple: yes
#%  description: Column pattern:Value or Numpy funtion to use to substitute NaN values
#%  required: no
#%  answer: *_skewness:nanmean,*_kurtosis:nanmean
#%end
#%option
#%  key: inf
#%  type: string
#%  multiple: yes
#%  description: Key:Value or Numpy funtion to use to substitute NaN values
#%  required: no
#%  answer: *_skewness:nanmean,*_kurtosis:nanmean
#%end
#%option
#%  key: neginf
#%  type: string
#%  multiple: yes
#%  description: Key:Value or Numpy funtion to use to substitute NaN values
#%  required: no
#%  answer:
#%end
#%option
#%  key: posinf
#%  type: double
#%  multiple: yes
#%  description: Key:Value or Numpy funtion to use to substitute NaN values
#%  required: no
#%  answer:
#%end
#%option
#%  key: csv_test_cls
#%  type: string
#%  multiple: no
#%  description: csv file name with results of different machine learning scores
#%  required: no
#%  answer: test_classifiers.csv
#%end
#%option
#%  key: report_class
#%  type: string
#%  multiple: no
#%  description: csv file name with results of different machine learning scores
#%  required: no
#%  answer: classification_report.txt
#%end
#%option
#%  key: svc_c_range
#%  type: double
#%  multiple: yes
#%  description: C value list
#%  required: no
#%  answer: 1e-2,1e-1,1e0,1e1,1e2,1e3,1e4,1e5,1e6,1e7,1e8
#%end
#%option
#%  key: svc_gamma_range
#%  type: double
#%  multiple: yes
#%  description: gamma value list
#%  required: no
#%  answer: 1e-6,1e-5,1e-4,1e-3,1e-2,1e-1,1e0,1e1,1e2,1e3,1e4
#%end
#%option
#%  key: svc_kernel_range
#%  type: string
#%  multiple: yes
#%  description: kernel value list
#%  required: no
#%  answer: linear,poly,rbf,sigmoid
#%end
#%option
#%  key: svc_n_jobs
#%  type: integer
#%  multiple: no
#%  description: number of jobs
#%  required: no
#%  answer: 1
#%end
#%option
#%  key: svc_c
#%  type: double
#%  multiple: no
#%  description: C value
#%  required: no
#%end
#%option
#%  key: svc_gamma
#%  type: double
#%  multiple: no
#%  description: gamma value
#%  required: no
#%end
#%option
#%  key: svc_kernel
#%  type: string
#%  multiple: no
#%  description: Available kernel are: ‘linear’, ‘poly’, ‘rbf’, ‘sigmoid’, ‘precomputed’
#%  required: no
#%  answer: rbf
#%end
#%option
#%  key: svc_img
#%  type: string
#%  multiple: no
#%  description: filename with the image od SVC parameter
#%  required: no
#%  answer: domain_%s.svg
#%end
#%option
#%  key: rst_names
#%  type: string
#%  multiple: no
#%  description: filename with the image od SVC parameter
#%  required: no
#%  answer: %s
#%end
#-----------------------------------------------------
#%flag
#%  key: e
#%  description: Extract the training set from the vtraining map
#%end
#%flag
#%  key: n
#%  description: Export to numpy files
#%end
#%flag
#%  key: f
#%  description: Feature importances with forests of trees
#%end
#%flag
#%  key: b
#%  description: Balance the training using the class with the minor number of areas
#%end
#%flag
#%  key: o
#%  description: optimize the training samples
#%end
#%flag
#%  key: c
#%  description: Classify the whole dataset
#%end
#%flag
#%  key: r
#%  description: Export the classify resutls to raster maps
#%end
#%flag
#%  key: t
#%  description: Test different classification methods
#%end
#%flag
#%  key: v
#%  description: Bias variance
#%end
#%flag
#%  key: d
#%  description: Explore the SVC domain
#%end
#-----------------------------------------------------
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import imp
import sys
import os
from pprint import pprint
from fnmatch import fnmatch

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from grass.pygrass.functions import get_lib_path
from grass.pygrass.messages import get_msgr
from grass.pygrass.vector import Vector
from grass.pygrass.modules import Module
from grass.script.core import parser, overwrite

path = get_lib_path("v.class.ml", "")
if path is None:
    raise ImportError("Not able to find the path %s directory." % path)

sys.path.append(path)


from training_extraction import extract_training
from ml_classifiers import CLASSIFIERS
from ml_functions import (balance, explorer_clsfiers, run_classifier,
                          optimize_training, explore_SVC, plot_grid)
from sqlite2npy import save2npy
from npy2table import export_results
from features import importances, tocsv


RULES = {'*_skewness': np.nanmean,
         '*_coeff_var': np.nanmean,
         '*_stddev': np.nanmean,
         '*_variance': np.nanmean,
         '*_mean': np.nanmean,
         '*_range': np.nanmean,
         '*_max': np.nanmax,
         '*_min': np.nanmin, }


def get_indexes(string, sep=',', rangesep='-'):
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
    with Vector(vtraining, mode='r') as vct:
        cur = vct.table.execute('SELECT cat, color FROM %s;' % vct.name)
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
    pairs = [s.strip().split(':') for s in string.strip().split(',')]
    for key, val in pairs:
        res[key] = convert(val)
    return res


def find_special_cols(array, cols, report=True,
                      special=('nan', 'inf', 'neginf', 'posinf')):
    sp = {key: [] for key in special}
    cntr = {key: [] for key in special}
    for i in range(len(cols)):
        for key in special:
            barray = getattr(np, 'is%s' % key)(array[:, i])
            if barray.any():
                sp[key].append(i)
                cntr[key].append(barray.sum())
    if report:
        indent = '    '
        tot = len(array)
        for key in special:
            fmt = '- %15s (%3d/%d, %4.3f%%)'
            strs = [fmt % (col, cnt, tot, cnt/float(tot)*100)
                    for col, cnt in zip(cols[np.array(sp[key])], cntr[key])]
            print('%s:\n%s' % (key, indent), ('\n%s' % indent).join(strs),
                  sep='')
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
                    indx = getattr(np, 'is%s' % key)(X[:, i])
                    val = (rules[key][rule] if np.isscalar(rules[key][rule])
                           else rules[key][rule](X[:, i][~indx]))
                    X[:, i][indx] = val
                    vals[key][cols[i]] = val
    return X, vals


def extract_classes(vect, layer):
    vect, mset = vect.split('@') if '@'in vect else (vect, '')
    with Vector(vect, mapset=mset, layer=layer, mode='r') as vct:
        vct.table.filters.select('cat', 'class')
        return {key: val for key, val in vct.table.execute()}


def main(opt, flg):
    msgr = get_msgr()
    indexes = None
    vect = opt['vector']
    vtraining = opt['vtraining'] if opt['vtraining'] else None
    scaler = None
    vlayer = opt['vlayer'] if opt['vlayer'] else vect + '_stats'
    tlayer = opt['tlayer'] if opt['tlayer'] else vect + '_training'
    rlayer = opt['rlayer'] if opt['rlayer'] else vect + '_results'

    labels = extract_classes(vtraining, vlayer)
    pprint(labels)

    if opt['scalar']:
        scapar = opt['scalar'].split(',')
        scaler = StandardScaler(with_mean='with_mean' in scapar,
                                with_std='with_std' in scapar)
    # if training extract training
    if vtraining and flg['e']:
        msgr.message("Extract training from: <%s>." % vtraining)
        extract_training(vect, vtraining, tlayer)
        flg['n'] = True

    if flg['n']:
        msgr.message("Save arrays to npy files.")
        save2npy(vect, vlayer, tlayer,
                 fcats=opt['npy_cats'], fcols=opt['npy_cols'],
                 fdata=opt['npy_data'], findx=opt['npy_index'],
                 fclss=opt['npy_tclasses'], ftdata=opt['npy_tdata'])

    # define the classifiers to use/test
    if opt['pyclassifiers'] and opt['pyvar']:
        # import classifiers to use
        mycls = imp.load_source("mycls", opt['pyclassifiers'])
        classifiers = getattr(mycls, opt['pyvar'])
    else:
        classifiers = CLASSIFIERS

    # Append the SVC classifier
    if opt['svc_c'] and opt['svc_gamma']:
            svc = {'name': 'SVC', 'classifier': SVC,
                   'kwargs': {'C': float(opt['svc_c']),
                              'gamma': float(opt['svc_gamma']),
                              'kernel': opt['svc_kernel']}}
            classifiers.append(svc)

    # extract classifiers from pyindx
    if opt['pyindx']:
        indexes = [i for i in get_indexes(opt['pyindx'])]
        classifiers = [classifiers[i] for i in indexes]

    num = int(opt['n_training']) if opt['n_training'] else None

    # load fron npy files
    Xt = np.load(opt['npy_tdata'])
    Yt = np.load(opt['npy_tclasses'])
    cols = np.load(opt['npy_cols'])

    # Define rules to substitute NaN, Inf, posInf, negInf values
    rules = {}
    for key in ('nan', 'inf', 'neginf', 'posinf'):
        if opt[key]:
            rules[key] = get_rules(opt[key])
    pprint(rules)

    # Substitute (skip cat column)
    Xt, rules_vals = substitute(Xt, rules, cols[1:])

    # Feature importances with forests of trees
    if flg['f']:
        importances(Xt, Yt, cols[1:],
                    csv=opt['imp_csv'], img=opt['imp_fig'],
                    # default parameters to save the matplotlib figure
                    **dict(dpi=300, transparent=False, bbox_inches='tight'))

    # optimize the training set
    if flg['o']:
        ind_optimize = (int(opt['pyindx_optimize']) if opt['pyindx_optimize']
                        else 0)
        cls = classifiers[ind_optimize]
        msgr.message("Find the optimum training set.")
        best, Xbt, Ybt = optimize_training(cls, Xt, Yt,
                                           labels, #{v: k for k, v in labels.items()},
                                           scaler,
                                           num=num, maxiterations=1000)
        msg = "    - save the optimum training data set to: %s."
        msgr.message(msg % opt['npy_btdata'])
        np.save(opt['npy_btdata'], Xbt)
        msg = "    - save the optimum training classes set to: %s."
        msgr.message(msg % opt['npy_btclasses'])
        np.save(opt['npy_btclasses'], Ybt)

    # balance the data
    if flg['b']:
        msg = "Balancing the training data set, each class have <%d> samples."
        msgr.message(msg % num)
        Xbt, Ybt = balance(Xt, Yt, num)
    else:
        if not flg['o']:
            Xbt = (np.load(opt['npy_btdata'])
                   if os.path.isfile(opt['npy_btdata']) else Xt)
            Ybt = (np.load(opt['npy_btclasses'])
                   if os.path.isfile(opt['npy_btclasses']) else Yt)

    # scale the data
    if scaler:
        msgr.message("Scaling the training data set.")
        scaler.fit(Xbt, Ybt)
        Xt = scaler.transform(Xt)
        Xbt = scaler.transform(Xbt)

    if flg['d']:
        C_range = [float(c) for c in opt['svc_c_range'].split(',')]
        gamma_range = [float(g) for g in opt['svc_gamma_range'].split(',')]
        kernel_range = [str(s) for s in opt['svc_kernel_range'].split(',')]
        msgr.message("Exploring the SVC domain.")
        grid = explore_SVC(Xbt, Ybt, n_folds=3, n_jobs=int(opt['svc_n_jobs']),
                           C=C_range, gamma=gamma_range, kernel=kernel_range)
        import pickle
        pkl = open('grid.pkl', 'w')
        pickle.dump(grid, pkl)
        pkl.close()
        plot_grid(grid, save=opt['svc_img'])

    # test the accuracy of different classifiers
    if flg['t']:
        # test different classifiers
        msgr.message("Exploring different classifiers.")
        msgr.message("cls_id   cls_name          mean     max     min     std")
        #import ipdb; ipdb.set_trace()
        res = explorer_clsfiers(classifiers, Xt, Yt,
                                indexes=indexes, n_folds=5, bv=flg['v'])
        # TODO: sort(order=...) is working only in the terminal, why?
        #res.sort(order='mean')
        with open(opt['csv_test_cls'], 'w') as csv:
            csv.write(tocsv(res))

    if flg['c']:
        # classify
        cols = []
        data = np.load(opt['npy_data'])
        pprint(rules_vals)
        # Substitute (skip cat column)
        data = substitute(data, rules_vals, cols[1:])

        msgr.message("Scaling the whole data set.")
        data = scaler.transform(data) if scaler else data
        cats = np.load(opt['npy_cats'])

        for cls in classifiers:
            run_classifier(cls, Xbt, Ybt, Xt, Yt, labels, data,
                           save=opt['report_class'])
            cols.append((cls['name'], 'INTEGER'))

#        import pickle
#        res = open('res.pkl', 'r')
#        classifiers = pickle.load(res)
        msgr.message("Export the results to layer: <%s>" % str(rlayer))
        export_results(vect, classifiers, cats, rlayer, vtraining, cols,
                       overwrite(), pkl='res.pkl')
#        res.close()

    if flg['r']:
        rules = ('\n'.join(['%d %s' % (k, v)
                            for k, v in get_colors(vtraining).items()])
                 if vtraining else None)

        msgr.message("Export the layer with results to raster")
        with Vector(vect, mode='r') as vct:
            tab = vct.dblinks.by_name(rlayer).table()
            rasters = [c for c in tab.columns]
            rasters.remove(tab.key)

        import ipdb; ipdb.set_trace()
        v2rst = Module('v.to.rast')
        rclrs = Module('r.colors')
        for rst in rasters:
            v2rst(input=vect, layer=rlayer, type='area',
                  use='attr', attrcolumn=rst, output=opt['rst_names'] % rst,
                  rows=4096 * 4, overwrite=overwrite())
            if rules:
                rclrs(map=rst, rules='-', stdin_=rules)


if __name__ == "__main__":
    main(*parser())
