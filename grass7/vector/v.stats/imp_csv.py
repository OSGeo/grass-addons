# -*- coding: utf-8 -*-
from __future__ import print_function, division
import numpy as np

import grass.lib.gis as glg

NPY2COLTYPE = {'<i8': 'INTEGER',
               '<f8': 'DOUBLE'}

# shp column names
ALLSHPN = ['area_id',    'cat',   'nisles',     'x_extent', 'y_extent',
           'iperimeter', 'iarea', 'icompact',   'ifd',      'perimeter',
           'area',       'boundarea', 'aratio', 'compact',  'fd']

# shp column types
ALLSHPT = ['<i8', '<i8', '<i8', '<f8', '<f8',
           '<f8', '<f8', '<f8', '<f8', '<f8',
           '<f8', '<f8', '<f8', '<f8', '<f8']

# rst column names
ALLRSTN = ['zone', 'label', 'all_cells', 'non_null_cells', 'null_cells',
           'sum', 'sum_abs', 'min', 'max', 'range',
           'mean', 'mean_of_abs', 'variance', 'stddev', 'coeff_var',
           'skewness', 'kurtosis', 'variance2', 'stddev2', 'coeff_var2',
           'skewness2', 'kurtosis2', 'first_quart', 'median', 'third_quart',
           'perc_90', 'mode', 'occurrences']

# rst column type
ALLRSTT = ['<i8', '<i8', '<i8', '<i8', '<i8',
           '<f8', '<f8', '<f8', '<f8', '<f8',
           '<f8', '<f8', '<f8', '<f8', '<f8',
           '<f8', '<f8', '<f8', '<f8', '<f8',
           '<f8', '<f8', '<f8', '<f8', '<f8',
           '<f8', '<f8', '<f8']

SKIPCSV = ['label', 'non_null_cells', 'null_cells',
           'mean_of_abs', 'sum', 'sum_abs']

SKIPSHP = ['area_id', ]

#SKIPSHP = ['areas', 'red__n', 'red__min', 'red__max', 'red__range', 'red__sum',
#           'red__mean', 'red__stddev', 'red__variance', 'red__cf_var',
#           'red__first_quartile', 'red__median', 'red__third_quartile',
#           'red__percentile_90', 'green__n', 'green__min', 'green__max',
#           'green__range', 'green__mean', 'green__stddev', 'green__variance',
#           'green__cf_var', 'green__sum', 'green__first_quartile',
#           'green__median', 'green__third_quartile', 'green__percentile_90',
#           'blue__n', 'blue__min', 'blue__max', 'blue__range', 'blue__mean',
#           'blue__stddev', 'blue__variance', 'blue__cf_var', 'blue__sum',
#           'blue__first_quartile', 'blue__median', 'blue__third_quartile',
#           'blue__percentile_90']

#----------------------------------------


def getrow(shpdata, rstdata, dim):
    drow = np.zeros((dim, ))
    lenght = len(shpdata)
    for i, rows in enumerate(zip(shpdata, *[rst[:, 1:] for rst in rstdata])):
        glg.G_percent(i, lenght, 2)
        start = 0
        for row in rows:
            end = start + row.shape[0]
            drow[start:end] = row
            start = end
        yield drow


def getcols(names, types, skipnames=None, prefix='',
            gettype=lambda x: x):
    cols = []
    skipnames = skipnames if skipnames else []
    for cname, ctype in zip(names, types):
        if cname not in skipnames:
            cols.append((prefix + cname, gettype(ctype)))
    return cols


def gettablecols(prefixes, allshpn, allshpt, skipshp,
                 allrstn, allrstt, skiprst):
    gettype = lambda x: NPY2COLTYPE[x]
    # define the new columns
    cols = getcols(allshpn, allshpt, skipshp, gettype=gettype)
    for prfx in prefixes:
        cols += getcols(allrstn, allrstt, skiprst,
                        prefix=prfx, gettype=gettype)
    return cols


def update_cols(tab, shpcsv, rstcsv, prefixes=None,
                skipshp=None, skiprst=None,
                shpcat=0, rstcat=0,
                allshpn=ALLSHPN, allrstn=ALLRSTN,
                allshpt=ALLSHPT, allrstt=ALLRSTT, overwrite=False):
    prefixes = prefixes if prefixes else [csv[:-4] for csv in rstcsv]
    skipshp = skipshp if skipshp else []
    skiprst = skiprst if skiprst else []
    useshpcols = [allshpn.index(c) for c in allshpn if c not in skipshp]
    userstcols = [allrstn.index(c) for c in allrstn if c not in skiprst]

    print("Start loading data from:")
    print("    - %s." % shpcsv, end='')
    shpdata = np.genfromtxt(shpcsv, delimiter=';', names=True,
                            usecols=useshpcols,
                            dtype=getcols(allshpn, allshpt, skipshp))
    shpdata.sort(order='cat')
    print(' Done.')

    rstdata = []
    for rst in rstcsv:
        print("    - %s." % rst, end='')
        rstdata.append(np.genfromtxt(rst, delimiter='|', names=True,
                                     usecols=userstcols,
                                     missing_values=('nan', '-nan'),
                                     dtype=getcols(allrstn, allrstt,
                                                   userstcols)))
        rstdata[-1].sort(order='zone')
        print(' Done.')

    print("Cheking categories and zones correspondance:")
    for i, rst in enumerate(rstdata):
        print("    - <%s>." % rstcsv[i], end='')
#        if rstcsv[i] == 'median5_contr.csv':
#            import ipdb; ipdb.set_trace()
        if not (shpdata['cat'] == rst['zone']).all():
            msg = "The categories and the zones are not equal, in <%s>"
            raise ValueError(msg % rstcsv[i])
        print(' Ok.')

    print("Conversion from record array to array")
    shpdata = np.array(shpdata.tolist())
    print('.', end='')
    for i, rst in enumerate(rstdata):
        rstdata[i] = np.array(rst.tolist())
        print('.', end='')
    print('Done.')
    # create the new table
    if tab.exist():
        tab.drop(force=True)
    cols = gettablecols(prefixes, allshpn, allshpt, skipshp,
                        allrstn, allrstt, skiprst)
    tab.create(cols)
    cur = tab.conn.cursor()
    print("Merge shape table with raster csv.")
    tab.insert(getrow(shpdata, rstdata, len(cols)), cursor=cur, many=True)
    tab.conn.commit()
    print("%d rows inserted." % tab.n_rows())
    return tab


#link = None
#with VectorTopo(VSEG, mode='r') as vect:
#    #link = update_cols(vect.table, CSV, PREFIX, allcsvcols=ALL,
#    #                   skipcsv=SKIPCSV, skipshp=SKIPSHP)
#    link = update_cols(vect.table, ECSV, PREFIX, allcsvcols=ALL,
#                       skipcsv=SKIPCSV, skipshp=ESKIPSHP)
#    link.layer = vect.layer + 1
#
##----------------------------
#with Vector(VSEG, mode='rw') as vect:
#    link = Link(layer=NEW_LAYER, name=NEW_NAME_LAYER, table=NEW_TABLE_NAME)
#    vect.dblinks.add(link)


