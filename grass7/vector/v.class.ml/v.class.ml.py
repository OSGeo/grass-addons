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
#%  type: double
#%  multiple: no
#%  description: Value to use to substitute NaN
#%  required: no
#%end
#%option
#%  key: inf
#%  type: double
#%  multiple: no
#%  description: Value to use to substitute NaN
#%  required: no
#%end
#%option
#%  key: csv
#%  type: string
#%  multiple: no
#%  description: csv file name with tha accuracy of different machine learning
#%  required: no
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
#%  key: d
#%  description: Explore the SVC domain
#%end
#-----------------------------------------------------
"""
v.category input=seg005_64@pietro layer=1,2,3,4,5,6,7,8,9 type=point,line,centroid,area,face output=seg005_64_new option=transfer

v.category input=seg005_64_new option=report

i.pca -n input=Combabula_Nearmap.red@PERMANENT,Combabula_Nearmap.green@PERMANENT,Combabula_Nearmap.blue@PERMANENT output_prefix=pca
PC1      2.78 ( 0.5757, 0.5957, 0.5601) [92.83%]
PC2      0.20 ( 0.6002, 0.1572,-0.7842) [ 6.81%]
PC3      0.01 ( 0.5552,-0.7877, 0.2670) [ 0.36%]

time r.texture -a input=pca.1@pietro prefix=pca5_ size=5 --o
time r.texture -a input=pca.1@pietro prefix=pca3_ size=3 --o
echo finish
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import imp
import sys
import os

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from grass.pygrass.functions import get_lib_path
from grass.pygrass.messages import Messenger
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

def main(opt, flg):
    msgr = Messenger()
    indexes = None
    vect = opt['vector']
    vtraining = opt['vtraining'] if opt['vtraining'] else None
    scaler = None
    vlayer = opt['vlayer'] if opt['vlayer'] else vect + '_stats'
    tlayer = opt['tlayer'] if opt['tlayer'] else vect + '_training'
    rlayer = opt['rlayer'] if opt['rlayer'] else vect + '_results'

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
        save2npy(vect, vlayer, tlayer)

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

    csv = open(opt['csv'], 'w') if opt['csv'] else sys.stdout
    num = int(opt['n_training']) if opt['n_training'] else None

    # load fron npy files
    Xt = np.load(opt['npy_tdata'])
    Yt = np.load(opt['npy_tclasses'])
    clsses = sorted(set(Yt))

    # Substitute NaN
    if opt['nan']:
        msgr.message("Substitute NaN values with: <%g>" % float(opt['nan']))
        Xt[np.isnan(Xt)] = float(opt['nan'])
    if opt['inf']:
        msgr.message("Substitute Inf values with: <%g>" % float(opt['inf']))
        Xt[np.isinf(Xt)] = float(opt['inf'])

    # optimize the training set
    if flg['o']:
        ind_optimize = (int(opt['pyindx_optimize']) if opt['pyindx_optimize']
                        else 0)
        cls = classifiers[ind_optimize]
        msgr.message("Find the optimum training set.")
        best, Xbt, Ybt = optimize_training(cls, Xt, Yt, scaler,
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
        plot_grid(grid, save=opt['svc_img'])

    # test the accuracy of different classifiers
    if flg['t']:
        # test different classifiers
        msgr.message("Exploring different classifiers.")
        explorer_clsfiers(classifiers, Xbt, Ybt, Xt, Yt, clsses, indexes, csv)

    if flg['c']:
        # classify
        cols = []
        data = np.load(opt['npy_data'])
        if opt['nan']:
            msg = "Substitute NaN values with: <%g>" % float(opt['nan'])
            msgr.message(msg)
            data[np.isnan(data)] = float(opt['nan'])
        if opt['inf']:
            msg = "Substitute Inf values with: <%g>" % float(opt['inf'])
            msgr.message(msg)
            data[np.isinf(data)] = float(opt['inf'])

        msgr.message("Scaling the whole data set.")
        data = scaler.transform(data) if scaler else data
        cats = np.load(opt['npy_cats'])

        for cls in classifiers:
            run_classifier(cls, Xbt, Ybt, Xt, Yt, clsses, data, save=csv)
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
