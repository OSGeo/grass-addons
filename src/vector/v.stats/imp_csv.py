# -*- coding: utf-8 -*-
from __future__ import print_function, division
import numpy as np

import grass.lib.gis as glg

NPY2COLTYPE = {"<i8": "INTEGER", "<f8": "DOUBLE"}

# shp column names
ALLSHPN = [
    "area_id",
    "cat",
    "nisles",
    "x_extent",
    "y_extent",
    "iperimeter",
    "iarea",
    "icompact",
    "ifd",
    "perimeter",
    "area",
    "boundarea",
    "aratio",
    "compact",
    "fd",
]

# shp column types
ALLSHPT = [
    "<i8",
    "<i8",
    "<i8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
]

# rst column names
ALLRSTN = [
    "zone",
    "label",
    "all_cells",
    "non_null_cells",
    "null_cells",
    "sum",
    "sum_abs",
    "min",
    "max",
    "range",
    "mean",
    "mean_of_abs",
    "variance",
    "stddev",
    "coeff_var",
    "skewness",
    "kurtosis",
    "variance2",
    "stddev2",
    "coeff_var2",
    "skewness2",
    "kurtosis2",
    "first_quart",
    "median",
    "third_quart",
    "perc_90",
    "mode",
    "occurrences",
]

# rst column type
ALLRSTT = [
    "<i8",
    "<i8",
    "<i8",
    "<i8",
    "<i8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
    "<f8",
]

SKIPCSV = ["label", "non_null_cells", "null_cells", "mean_of_abs", "sum", "sum_abs"]

SKIPSHP = [
    "area_id",
]

# ----------------------------------------


def getrow(shpdata, rstdata, cols):
    drow = np.zeros((len(cols),))
    lenght = len(shpdata)
    for i, rows in enumerate(zip(shpdata, *rstdata)):
        glg.G_percent(i, lenght, 2)
        start = 0
        for row in rows:
            end = start + row.shape[0]
            # print('---')
            # for c, r in zip(cols[start:end], row):
            #    print(c[0], r)
            drow[start:end] = row
            start = end
        # import ipdb; ipdb.set_trace()
        yield drow


def getcols(names, types, skipnames=None, prefix="", gettype=lambda x: x):
    cols = []
    skipnames = skipnames if skipnames else []
    for cname, ctype in zip(names, types):
        if cname not in skipnames:
            cols.append((prefix + cname, gettype(ctype)))
    return cols


def gettablecols(prefixes, allshpn, allshpt, skipshp, allrstn, allrstt, skiprst):
    def gettype(x):
        return NPY2COLTYPE[x]

    # define the new columns
    cols = getcols(allshpn, allshpt, skipshp, gettype=gettype)
    for prfx in prefixes:
        cols += getcols(allrstn, allrstt, skiprst, prefix=prfx, gettype=gettype)
    return cols


def update_cols(
    tab,
    shpcsv,
    rstcsv,
    prefixes=None,
    skipshp=None,
    skiprst=None,
    shpcat=0,
    rstcat=0,
    allshpn=ALLSHPN,
    allrstn=ALLRSTN,
    allshpt=ALLSHPT,
    allrstt=ALLRSTT,
    overwrite=False,
    separator=";",
):
    prefixes = prefixes if prefixes else [csv[:-4] for csv in rstcsv]
    skipshp = skipshp if skipshp else []
    skiprst = skiprst if skiprst else []
    useshpcols = [allshpn.index(c) for c in allshpn if c not in skipshp]
    userstcols = [allrstn.index(c) for c in allrstn if c not in skiprst]

    print("Start loading data from:")
    print("    - %s." % shpcsv, end="")
    shpdata = np.genfromtxt(
        shpcsv,
        delimiter=separator,
        usecols=useshpcols,
        dtype=getcols(allshpn, allshpt, skipshp),
    )
    shpdata.sort(order="cat")
    # remove negative categories
    shpdata = shpdata[shpdata["cat"] > 0]
    print(" Done.")

    rstdata = []
    for rst in rstcsv:
        print("    - %s." % rst, end="")
        rstd = np.genfromtxt(
            rst,
            delimiter=separator,
            names=True,
            usecols=userstcols,
            missing_values=("nan", "-nan"),
            dtype=getcols(allrstn, allrstt, skiprst),
        )
        rstd.sort(order="zone")
        rstdata.append(rstd[rstd["zone"] > 0])
        print(" Done.")

    npz = "csvfile.npz"
    print("Save arrays to: %s" % npz)
    kwargs = {shpcsv: shpdata}
    for csv, rst in zip(rstcsv, rstdata):
        kwargs[csv] = rst
    np.savez_compressed(npz, **kwargs)

    print("Cheking categories and zones correspondance:")
    for i, rst in enumerate(rstdata):
        print("    - <%s>." % rstcsv[i], end="")
        #        if rstcsv[i] == 'median5_contr.csv':
        # import ipdb; ipdb.set_trace()
        if not (shpdata["cat"] == rst["zone"]).all():
            msg = "The categories and the zones are not equal, in <%s>"
            raise ValueError(msg % rstcsv[i])
        print(" Ok.")

    print("Conversion from record array to array")
    newdtype = np.dtype([(n, "<f8") for n in shpdata.dtype.names])
    shpdata = shpdata.astype(newdtype).view("<f8").reshape((len(shpdata), -1))
    print(".", end="")
    for i, rst in enumerate(rstdata):
        # convert to <f8 and remove the first column with the zones
        newdtype = np.dtype([(n, "<f8") for n in rst.dtype.names][1:])
        rstdata[i] = rst.astype(newdtype).view("<f8").reshape((len(rst), -1))
        print(".", end="")
    print("Done.")
    # create the new table
    if tab.exist():
        tab.drop(force=True)
    cols = gettablecols(
        prefixes,
        allshpn,
        allshpt,
        skipshp,
        # remove zone from raster
        allrstn[1:],
        allrstt[1:],
        skiprst,
    )
    tab.create(cols)
    cur = tab.conn.cursor()
    print("Merge shape table with raster csv.")
    tab.insert(getrow(shpdata, rstdata, cols), cursor=cur, many=True)
    tab.conn.commit()
    print("%d rows inserted." % tab.n_rows())
    return tab
