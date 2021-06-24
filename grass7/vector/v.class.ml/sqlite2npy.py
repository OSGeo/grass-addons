# -*- coding: utf-8 -*-
"""
Created on Sat Nov  2 23:40:22 2013

@author: pietro
"""
from __future__ import print_function, division

import numpy as np
from grass.pygrass.vector import VectorTopo

FCATS = "cats.npy"
FCOLS = "cols.npy"
FDATA = "data.npy"
FINDX = "indx.npy"
FCLSS = "training_classes.npy"
FTDATA = "training_data.npy"


def cpdata(shape, iterator, dtype=float, msg=""):
    """Avoid to create a python list and then convert the python list to a
    numpy array. This function instantiate statically a numpy array and then
    fill the numpy array with the data coming from the generator to reduce
    the memory consumption."""
    nrows = shape[0]
    # msgr = ???
    # msgr.message(msg)
    print(msg)
    dt = np.empty(shape, dtype=dtype)
    for i, data in enumerate(iterator):
        # msgr.percent(i, nrows, 2)
        dt[i] = data
    return dt


def save2npy(
    vect,
    l_data,
    l_trn,
    fcats=FCATS,
    fcols=FCOLS,
    fdata=FDATA,
    findx=FINDX,
    fclss=FCLSS,
    ftdata=FTDATA,
):
    """Return 6 arrays:
    - categories,
    - columns name,
    - data,
    - a boolean array with the training,
    - the training classes,
    - the training data.
    """
    with VectorTopo(vect, mode="r") as vct:
        # instantiate the tables
        data = (
            vct.dblinks.by_layer(int(l_data)).table()
            if l_data.isdigit()
            else vct.dblinks.by_name(l_data).table()
        )
        trng = (
            vct.dblinks.by_layer(int(l_trn)).table()
            if l_trn.isdigit()
            else vct.dblinks.by_name(l_trn).table()
        )

        # check the dimensions
        n_trng, n_data = trng.n_rows(), data.n_rows()
        if n_trng != n_data:
            msg = (
                "Different dimension between the training set (%d)"
                " and the data set (%d)" % (n_trng, n_data)
            )
            print(msg)
            raise

        # extract the training
        slct_trn = "SELECT class FROM {tname};".format(tname=trng.name)
        trn_all = cpdata(
            (n_data,),
            (np.nan if a[0] is None else a[0] for a in trng.execute(slct_trn)),
            msg=slct_trn,
        )
        # trn_all = np.array([np.nan if a[0] is None else a[0]
        #                     for a in trng.execute(slct_trn)])
        trn_indxs = ~np.isnan(trn_all)

        # extract the data
        data_cols = data.columns.names()
        cols = np.array(data_cols)
        data_cols.remove(data.key)
        scols = ", ".join(data_cols)
        slct_data = "SELECT {cols} FROM {tname};".format(cols=scols, tname=data.name)
        shape = (n_data, len(data_cols))
        # use the function to be more memory efficient
        dta = cpdata(shape, data.execute(slct_data), msg=slct_data)

        # extract the cats
        slct_cats = "SELECT {cat} FROM {tname};".format(cat=trng.key, tname=trng.name)
        cats = cpdata(
            (n_data,), (c[0] for c in data.execute(slct_cats)), dtype=int, msg=slct_cats
        )
        # cats = np.array([c[0] for c in data.execute(slct_cats)])

        # training samples
        trn_dta = dta[trn_indxs]
        trn_ind = trn_all[trn_indxs]

        # save
        np.save(fcats, cats)
        np.save(fcols, cols)
        np.save(fdata, dta)
        np.save(findx, trn_indxs)
        np.save(fclss, trn_ind)
        np.save(ftdata, trn_dta)
        return cats, cols, dta, trn_indxs, trn_ind, trn_dta


def load_from_npy(fcats=FCATS, fdata=FDATA, findx=FINDX, fclss=FCLSS, ftdata=FTDATA):
    cats = np.load(fcats)
    data = np.load(fdata)
    indx = np.load(findx)
    Yt = np.load(fclss)
    Xt = np.load(ftdata)
    return cats, data, indx, Yt, Xt
