# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 12:54:42 2013

@author: pietro
"""
from __future__ import print_function, division
import os
from grass.pygrass.modules import Module, ParallelModuleQueue


def get_shp_csv(vector, csv=None, overwrite=False, separator=';'):
    vasts = Module('v.area.stats')
    csv = vector + '.csv' if csv is None else csv
    if os.path.exists(csv) and overwrite:
        os.remove(csv)
    vasts(map=vector, output=csv, overwrite=overwrite, separator=separator)
    return csv


def get_zones(vector, zones, layer=1, overwrite=False):
    v2rast = Module('v.to.rast', input=vector, layer=str(layer), type='area',
                    output=zones, overwrite=overwrite, rows=65536, use='cat')
    rclr = Module("r.colors", map=zones, color="random")


def get_rst_csv(rasters, zones, csvfiles, percentile=90., overwrite=False,
                nprocs=1, separator=';'):
    queue = ParallelModuleQueue(nprocs=nprocs)
    for rast, csv in zip(rasters, csvfiles):
        print(rast, csv)
        queue.put(Module('r.univar2', map=rast, zones=zones,
                         percentile=percentile, output=csv, separator=separator,
                         overwrite=overwrite, flags='et', run_=False))
    # wait the end of all process
    queue.wait()
    return csvfiles
