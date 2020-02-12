# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 12:54:42 2013

@author: pietro
"""
from grass.pygrass.modules.grid.patch import get_start_end_index
from grass.pygrass.raster import RasterRow
from grass.pygrass.messages import get_msgr

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

def rpatch_row(rast, rasts, bboxes, max_rasts):
    """Patch a row of bound boxes."""
    sei = get_start_end_index(bboxes)
    # instantiate two buffer
    buff = rasts[0][0]
    rbuff = rasts[0][0]
    r_start, r_end, c_start, c_end = sei[0]
    for row in xrange(r_start, r_end):
        for col, ras in enumerate(rasts):
            r_start, r_end, c_start, c_end = sei[col]
            buff = ras.get_row(row, buff)
            rbuff[c_start:c_end] = buff[c_start:c_end] + max_rasts[col]
        rast.put_row(rbuff)


def rpatch_map(raster, mapset, mset_str, bbox_list, overwrite=False,
               start_row=0, start_col=0, prefix=''):
    """Patch raster using a bounding box list to trim the raster."""
    # Instantiate the RasterRow input objects
    rast = RasterRow(prefix + raster, mapset)
    with RasterRow(name=raster, mapset=mset_str % (0, 0), mode='r') as rtype:
        rast.open('w', mtype=rtype.mtype, overwrite=overwrite)
    msgr = get_msgr()
    rasts = []
    mrast = 0
    nrows = len(bbox_list)
    for row, rbbox in enumerate(bbox_list):
        rrasts = []
        max_rasts = []
        for col in range(len(rbbox)):
            msgr.percent(row, nrows, 1)
            rrasts.append(RasterRow(name=raster,
                                    mapset=mset_str % (start_row + row,
                                                       start_col + col)))
            rrasts[-1].open('r')
            mrast += rrasts[-1].info.max + 1
            max_rasts.append(mrast)
        rasts.append(rrasts)
        rpatch_row(rast, rrasts, rbbox, max_rasts)
        for rst in rrasts:
            rst.close()
            del(rst)

    rast.close()

# run on a cluster
#import os
#import re
#from grass.pygrass.modules.grid.split import split_region_tiles
#from grass.pygrass.modules.grid.node import row_order
#
#
#def node_patch(cmd, nwidth, nheight, out_regexp, overwrite=True):
#    from grass.lib.gis import G_tempfile
#    tmp, dummy = os.path.split(os.path.split(G_tempfile())[0])
#    tmpdir = os.path.join(cmd)
#    bboxes = split_region_tiles(width=nwidth, height=nheight)
#    for out in os.listdir(tmpdir):
#        outdir = os.path.join(tmpdir, out)
#        rasts = os.listdir(outdir)
#        rsts = row_order(rasts, bboxes)
#        rst = RasterRow(re.findall(out_regexp, rasts[0])[0])
#        rst.open('w', mtype=rsts[0][0].mtype, overwrite=overwrite)
#        for rrst, rbbox in zip(rsts, bboxes):
#            rpatch_row(rst, rrst, rbbox)
#
#        for rrst in rsts:
#            for r in rrst:
#                r.close()
#
#        rst.close()
