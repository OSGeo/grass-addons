# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 15:08:38 2013

@author: pietro
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import time
import random as rnd
from gettext import lgettext as _
import sys

import numpy as np
import pylab as pl


from sklearn.metrics import accuracy_score
from sklearn.cross_validation import StratifiedKFold
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC

from grass.pygrass.messages import Messenger

MSGR = Messenger()


COLS = [('cat', 'INTEGER PRIMARY KEY'),
        ('class', 'INTEGER'),
        ('color', 'VARCHAR(11)'), ]


def print_cols(clss, sep=';', save=sys.stdout):
    clsses = sorted(set(clss))
    cols = ['ml_index', 'ml_name', 'fit_time', 'prediction_time',
            'tot_accuracy']
    cols += [str(cls) for cls in clsses]
    cols += ['mean', ]
    print(sep.join(cols), file=save)


def print_test(cls, timefmt='%.4fs', accfmt='%.5f', sep=';', save=sys.stdout):
    res = [str(cls['index']) if 'index' in cls else 'None',
           cls['name'],
           timefmt % (cls['fit_stop'] - cls['fit_start']),
           timefmt % (cls['pred_stop'] - cls['pred_start']),
           accfmt % cls['t_acc'],
           sep.join([accfmt % acc for acc in cls['c_acc']]),
           accfmt % cls['c_acc_mean']]
    print(sep.join(res), file=save)


def accuracy(sol, cls=None, data=None, clss=None, pred=None):
    cls = cls if cls else dict()
    clsses = clss if clss else sorted(set(sol))
    if 'cls' in cls:
        cls['pred_start'] = time.time()
        pred = cls['cls'].predict(data)
        cls['pred_stop'] = time.time()

    cls['t_acc'] = accuracy_score(sol, pred, normalize=True)
    c_acc = []
    for c in clsses:
        indx = sol == c
        c_acc.append(accuracy_score(sol[indx], pred[indx],
                                    normalize=True))
    cls['c_acc'] = np.array(c_acc)
    cls['c_acc_mean'] = cls['c_acc'].mean()
    return cls


def test_classifier(cls, Xt, Yt, Xd, Yd, clss, save=sys.stdout,
                    verbose=True):
    cls['cls'] = cls['classifier'](**cls.get('kwargs', {}))
    cls['fit_start'] = time.time()
    cls['cls'].fit(Xt, Yt)
    cls['fit_stop'] = time.time()
    try:
        cls['params'] = cls['cls'].get_params()
    except AttributeError:
        cls['params'] = None
    accuracy(Yd, cls, Xd, clss)
    if verbose:
        print_test(cls, save=save)


def run_classifier(cls, Xt, Yt, Xd, Yd, clss, data,
                   save=sys.stdout):
    test_classifier(cls, Xt, Yt, Xd, Yd, clss, verbose=False)
    cls['pred_start'] = time.time()
    cls['predict'] = cls['cls'].predict(data)
    cls['pred_stop'] = time.time()
    print_test(cls, save=save)
    np.save(cls['name'] + '.npy', cls['predict'])


def reduce_cls(Yt, subs):
    Yr = np.copy(Yt)
    for k in subs:
        indx = Yr == k
        Yr[indx] = subs[k]
    return Yr


def balance_cls(data, num):
    indx = np.random.randint(0, len(data), size=num)
    return data[indx]


def balance(tdata, tclss, num=None):
    clss = sorted(set(tclss))
    num = num if num else min([len(tclss[tclss == c]) for c in clss])
    dt = []
    for c in clss:
        dt.extend([(c, d) for d in balance_cls(tdata[tclss == c], num)])
    rnd.shuffle(dt)
    bclss = np.array([r[0] for r in dt], dtype=int)
    bdata = np.array([r[1] for r in dt])
    return bdata, bclss


def optimize_training(cls, tdata, tclss,
                      scaler=None, num=None, maxiterations=1000):
    best = cls.copy()
    best['c_acc_mean'] = 0
    means = []
    for i in range(maxiterations):  # TODO: use multicore
        MSGR.percent(i, maxiterations, 1)
        Xt, Yt = balance(tdata, tclss, num)
        if scaler:
            scaler.fit(Xt, Yt)
            sXt = scaler.transform(Xt)
            stdata = scaler.transform(tdata)
        else:
            sXt, stdata = Xt, tdata
        test_classifier(cls, sXt, Yt, stdata, tclss, None, verbose=False)
        if cls['c_acc_mean'] > best['c_acc_mean']:
            print("%f > %f" % (cls['c_acc_mean'], best['c_acc_mean']))
            best = cls.copy()
            bXt, bYt = Xt, Yt
        means.append(cls['c_acc_mean'])
    means = np.array(means)
    print("best accuracy: %f, number of iterations: %d" % (best['c_acc_mean'],
                                                           maxiterations))
    print("mean of means: %f" % means.mean())
    print("min of means: %f" % means.min())
    print("max of means: %f" % means.max())
    print("std of means: %f" % means.std())
    return best, bXt, bYt


def explorer_clsfiers(clsses, Xt, Yt, Xd, Yd, clss,
                      indexes=None, csv=sys.stdout):
    errors = []
    gen = zip(indexes, clsses) if indexes else enumerate(clsses)
    print_cols(Yt, sep=';', save=csv)
    for ind, cls in gen:
        print(cls['name'], ind)
        cls['index'] = ind
        try:
            test_classifier(cls, Xt, Yt, Xd, Yd, clss, csv)
        except:
            errors.append(cls)
    for err in errors:
        print('Error in: %s' % err['name'])


def plot_grid(grid, save=''):
    C = grid.param_grid['C']
    gamma = grid.param_grid['gamma']

    for kernel in grid.param_grid['kernel']:
        scores = [x[1] for x in grid.grid_scores_ if x[0]['kernel'] == kernel]
        scores = np.array(scores).reshape(len(C), len(gamma))
        # draw heatmap of accuracy as a function of gamma and C
        pl.figure(figsize=(8, 6))
        pl.subplots_adjust(left=0.05, right=0.95, bottom=0.15, top=0.95)
        pl.imshow(scores, interpolation='nearest', cmap=pl.cm.spectral)
        pl.xlabel(r'$\gamma$')
        pl.ylabel('C')
        pl.colorbar()
        pl.xticks(np.arange(len(gamma)), gamma, rotation=45)
        pl.yticks(np.arange(len(C)), C)
        ic, igamma = np.unravel_index(np.argmax(scores), scores.shape)
        pl.plot(igamma, ic, 'r.')
        best = scores[igamma, ic]
        titl = r"$best:\, %0.4f, \,C:\, %g, \,\gamma: \,%g$" % (best,
                                                             C[ic],
                                                             gamma[igamma])
        pl.title(titl)
        if save:
            pl.savefig(save, dpi=600, trasparent=True, bbox_inches='tight')
        pl.show()


def explore_SVC(Xt, Yt, n_folds=3, n_jobs=1, **kwargs):
    cv = StratifiedKFold(y=Yt, n_folds=n_folds)
    grid = GridSearchCV(SVC(), param_grid=kwargs, cv=cv, n_jobs=n_jobs)
    grid.fit(Xt, Yt)
    print("The best classifier is: ", grid.best_estimator_)
    return grid
