# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 15:08:38 2013

@author: pietro
"""
from __future__ import (absolute_import, division, print_function)
import time
import random as rnd
from gettext import lgettext as _
import sys
import pickle as pk

import numpy as np
import matplotlib.pyplot as plt


from sklearn import metrics as metrics
from sklearn.metrics import precision_recall_curve as prc, roc_curve, auc
from sklearn.cross_validation import StratifiedKFold
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC
from sklearn.cross_validation import cross_val_score

#from grass.pygrass.messages import get_msgr


COLS = [('cat', 'INTEGER PRIMARY KEY'),
        ('class', 'INTEGER'),
        ('color', 'VARCHAR(11)'), ]


SCORES_DTYPE = [('index', 'i'),
                ('name', '<U32'),
                ('mean', 'f'),
                ('max', 'f'),
                ('min', 'f'),
                ('std', 'f')]


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


def accuracy(sol, cls=None, data=None, labels=None, pred=None):
    cls = cls if cls else dict()
    clsses = sorted(labels.keys())
    if 'cls' in cls:
        cls['pred_start'] = time.time()
        pred = cls['cls'].predict(data)
        cls['pred_stop'] = time.time()

    cls['t_acc'] = metrics.accuracy_score(sol, pred, normalize=True)
    lab = [labels[key] for key in clsses]
    cls['report'] = metrics.classification_report(sol, pred, lab)
    cls['confusion'] = metrics.confusion_matrix(sol, pred, lab)
    c_acc = []
    for c in clsses:
        indx = (sol == c).nonzero()
        c_acc.append(metrics.accuracy_score(sol[indx], pred[indx],
                                            normalize=True))
    cls['c_acc'] = np.array(c_acc)
    cls['c_acc_mean'] = cls['c_acc'].mean()
    return cls


def test_classifier(cls, Xt, Yt, Xd, Yd, labels, save=sys.stdout,
                    verbose=True):
    cls['cls'] = cls['classifier'](**cls.get('kwargs', {}))
    cls['fit_start'] = time.time()
    cls['cls'].fit(Xt, Yt)
    cls['fit_stop'] = time.time()
    try:
        cls['params'] = cls['cls'].get_params()
    except AttributeError:
        cls['params'] = None
    accuracy(Yd, cls, Xd, labels)
    if verbose:
        print_test(cls, save=save)


def run_classifier(cls, Xt, Yt, Xd, Yd, labels, data,
                   report=sys.stdout):
    test_classifier(cls, Xt, Yt, Xd, Yd, labels, verbose=False)
    cls['pred_start'] = time.time()
    cls['predict'] = cls['cls'].predict(data)
    cls['pred_stop'] = time.time()
    print_test(cls, save=report)
    report.write('\n' + cls['report'])
    report.write('\n' + cls['confusion'])
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


def optimize_training(cls, tdata, tclss, labels,
                      scaler=None, num=None, maxiterations=1000):
    best = cls.copy()
    best['c_acc_mean'] = 0
    means = []
    #msgr = get_msgr()
    for i in range(maxiterations):  # TODO: use multicore
        #msgr.percent(i, maxiterations, 1)
        Xt, Yt = balance(tdata, tclss, num)
        if scaler:
            scaler.fit(Xt, Yt)
            sXt = scaler.transform(Xt)
            stdata = scaler.transform(tdata)
        else:
            sXt, stdata = Xt, tdata
        test_classifier(cls, sXt, Yt, stdata, tclss, labels, verbose=False)
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


def plot_bias_variance(data_sizes, train_errors, test_errors, name,
                       title="Bias-Variance for '%s'",
                       train_err_std=None, test_err_std=None,
                       train_stl='-', test_stl='-',
                       train_width=1, test_width=1,
                       train_clr='b', test_clr='r', alpha=0.2,
                       fmt='png', **kwargs):
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.set_ylim([0.0, 1.0])
    ax.set_xlabel('Data set size')
    ax.set_ylabel('Error')
    ax.set_title(title % name)
    if train_err_std is not None:
        ax.fill_between(data_sizes,
                        train_errors - train_err_std,
                        train_errors + train_err_std,
                        facecolor=train_clr, alpha=alpha)
    if test_err_std is not None:
        ax.fill_between(data_sizes,
                        test_errors - test_err_std,
                        test_errors + test_err_std,
                        facecolor=test_clr, alpha=alpha)
    ax.plot(data_sizes, test_errors, label="test error", color=test_clr,
            linestyle=test_stl, linewidth=test_width)
    ax.plot(data_sizes, train_errors, label="train error", color=train_clr,
            linestyle=train_stl, linewidth=train_width)
    ax.legend(loc="upper right")
    ax.grid(True, linestyle='-', color='0.75')
    fig.savefig("bv_%s.%s" % (name.replace(" ", "_"), fmt), **kwargs)


def bias_variance_analysis(cls, tdata, tclss, n_folds=5, step=5):
    clss = sorted(set(tclss))
    num = min([len(tclss[tclss == c]) for c in clss])

    clf = cls['classifier'](**cls['kwargs'])
    keys = ('fprs', 'tprs', 'roc_scores', 'pr_scores', 'precisions',
            'recalls', 'thresholds')

    bv = {}
    lk = {l: {k: [] for k in keys} for l in clss}
    for n in range(5, num, step):
        X, y = balance(tdata, tclss, n)
        cv = StratifiedKFold(y, n_folds=n_folds)
        # instantiate empty lists
        train_errors, test_errors, scores = [], [], []
        for train, test in cv:
            X_train, y_train = X[train], y[train]
            X_test, y_test = X[test], y[test]

            # fit train data
            clf.fit(X_train, y_train)

            # get score
            train_score = clf.score(X_train, y_train)
            test_score = clf.score(X_test, y_test)
            scores.append(test_score)

            # get errors
            train_errors.append(1 - train_score)
            test_errors.append(1 - test_score)

            # get probability
            proba = clf.predict_proba(X_test)

            # compute score for each class VS rest
            for idx, label in enumerate(clss):
                fpr, tpr, roc_thr = roc_curve(y_test, proba[:, idx], label)
                precision, recall, pr_thr = prc(y_test, proba[:, idx], label)
                lk[label]['fprs'].append(fpr)
                lk[label]['tprs'].append(tpr)
                lk[label]['roc_scores'].append(auc(fpr, tpr))

                lk[label]['precisions'].append(precision)
                lk[label]['recalls'].append(recall)
                lk[label]['thresholds'].append(pr_thr)
                lk[label]['pr_scores'].append(auc(recall, precision))
        bv[n] = {'test': np.array(test_errors),
                 'train': np.array(train_errors),
                 'score': np.array(scores)}
    cls['bias variance'] = bv
    cls['label scores'] = lk


def explorer_clsfiers(clsses, Xd, Yd, indexes=None, n_folds=5, bv=False):
    gen = zip(indexes, clsses) if indexes else enumerate(clsses)
    cv = StratifiedKFold(Yd, n_folds=n_folds)
    fmt = '%5d %-30s %6.4f %6.4f %6.4f %6.4f'
    res = []
    kw = dict(bbox_inches="tight", dpi=300)
    for index, cls in gen:
        try:
            cls['scores'] = cross_val_score(cls['classifier'](**cls['kwargs']),
                                            Xd, Yd, cv=cv, n_jobs=1, verbose=0)
            # TODO: if n_jobs == -1 raise:
            # AttributeError: '_MainProcess' object has no attribute '_daemonic'
            mean, mx, mn, st = (cls['scores'].mean(), cls['scores'].max(),
                                cls['scores'].min(), cls['scores'].std())
            vals = (index, cls['name'], mean, mx, mn, st)
            print(fmt % vals)
            res.append(vals)
            if bv:
                bias_variance_analysis(cls, Xd, Yd, n_folds=5, step=5)
                bv = cls['bias variance']
                data_sizes = np.array(sorted(bv.keys()))
                test = np.array([bv[i]['test'] for i in data_sizes])
                train = np.array([bv[i]['train'] for i in data_sizes])
                plot_bias_variance(data_sizes,
                                   train.mean(axis=1), test.mean(axis=1),
                                   cls['name'], "Bias-Variance for '%s'",
                                   train_err_std=train.std(axis=1),
                                   test_err_std=test.std(axis=1),
                                   train_stl='-', test_stl='-',
                                   train_width=1, test_width=1,
                                   train_clr='b', test_clr='r', alpha=0.2,
                                   fmt='png', **kw)
                with open("%s.pkl" % cls['name'].replace(' ', '_'), 'wb') as pkl:
                    pk.dump(cls, pkl)
        except:
            #import ipdb; ipdb.set_trace()
            #print('problem with: %s' % cls['name'])
            pass
    return np.array(res, dtype=SCORES_DTYPE)


def explorer_clsfiers_old(clsses, Xt, Yt, Xd, Yd, clss,
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


CMAP = plt.cm.Blues


def plot_grid(grid, save=''):
    C = grid.param_grid['C']
    gamma = grid.param_grid['gamma']
    kernels = grid.param_grid['kernel']
    for kernel in kernels:
        scores = [x[1] for x in grid.grid_scores_ if x[0]['kernel'] == kernel]
        scores = np.array(scores).reshape(len(C), len(gamma))
        # draw heatmap of accuracy as a function of gamma and C
        #pl.figure(figsize=(8, 6))
        #pl.subplots_adjust(left=0.05, right=0.95, bottom=0.15, top=0.95)
        fig, ax = plt.subplots()
        img = ax.imshow(scores, interpolation='nearest', cmap=CMAP)
        ax.set_xlabel(r'$\gamma$')
        ax.set_ylabel('C')
        ax.set_xticks(np.arange(len(gamma)))
        ax.set_xticklabels(gamma, rotation=45)
        ax.set_yticks(np.arange(len(C)))
        ax.set_yticklabels(C)
#        if kernel == 'poly':
#            import ipdb; ipdb.set_trace()
        ic, igamma = np.unravel_index(np.argmax(scores), scores.shape)
        ax.plot(igamma, ic, 'r.')
        best = scores[ic, igamma]
        titl = r"%s $best:\, %0.4f, \,C:\, %g, \,\gamma: \,%g$" % (kernel.title(),
                                                                   best, C[ic],
                                                                   gamma[igamma])
        ax.set_title(titl)
        fig.colorbar(img)
        if save:
            fig.savefig(save % kernel, dpi=600, trasparent=True, bbox_inches='tight')
        fig.show()


def explore_SVC(Xt, Yt, n_folds=3, n_jobs=1, **kwargs):
    cv = StratifiedKFold(y=Yt, n_folds=n_folds)
    grid = GridSearchCV(SVC(), param_grid=kwargs, cv=cv, n_jobs=n_jobs,
                        verbose=2)
    grid.fit(Xt, Yt)
    print("The best classifier is: ", grid.best_estimator_)
    return grid
