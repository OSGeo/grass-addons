# -*- coding: utf-8 -*-
import numpy as np
import os
#import pdb

# import grass libraries
from grass.script import mapcalc
from grass.script import core as gcore
from grass.pygrass.raster import RasterRow
from grass.pygrass.raster.buffer import Buffer
from grass.pygrass.gis.region import Region

try:
    from scipy.sparse import csr_matrix
except ImportError:
    gcore.warning('You should install scipy to use this module: '
                  'pip install scipy')


def cleanup(raster=None, vector=None, pattern=None, debug=False):
    """Delete temporary maps"""
    if not debug:
        if raster:
            gcore.run_command("g.remove", flags="f", type='raster',
                              name=raster)
        if vector:
            gcore.run_command("g.remove", flags="f", type='vector',
                              name=vector)
        if pattern:
            gcore.run_command("g.remove", flags="f", type='raster,vector',
                              pattern=pattern)


def check_overlay_rv(raster, vector):
    """
    check the overlay between a raster and a vector
    :param raster: grass raster name
    :type raster: string
    :param vector: grass vector name
    :type vector: string
    """
    gcore.run_command('v.to.rast',
                      input=vector,
                      output='vec_rast',
                      use='cat')
    #pdb.set_trace()
    formula = 'overlay = if( %s>0  && vec_rast , vec_rast)' % (raster)
    mapcalc(formula, overwrite=True)
    formula = 'diff = overlay - vec_rast'
    mapcalc(formula, overwrite=True)
    perc_0 = perc_of_overlay('diff', '0')
    return perc_0


def check_overlay_rr(raster1, raster2):
    """
    check the overlay between rasters
    :param raster1: grass raster name
    :type raster: string
    :param raster2: grass raster name
    :type vector: string
    """
    pid = os.getpid()
    tmp_diff = "tmprgreen_%i_diff" % pid
    tmp_overlay = "tmprgreen_%i_overlay" % pid
    formula = '%s = if( %s>0  && %s>0 , %s)' % (tmp_overlay, raster1,
                                                raster2, raster2)
    mapcalc(formula, overwrite=True)
    formula = "%s = if(isnull(%s), if(%s, 10), %s - %s)" % (tmp_diff,
                                                            tmp_overlay,
                                                            raster2,
                                                            tmp_overlay,
                                                            raster2)
    formula = '%s = %s - %s' % (tmp_diff, tmp_overlay, raster2)
    mapcalc(formula, overwrite=True)
    perc_0 = perc_of_overlay(tmp_diff, '0')
    return perc_0


def perc_of_overlay(raster, val):
    """
    split the output of r.report and give the percentage of a value
    :param raster: grass raster name
    :type raster: string
    :param val: value to compute the percentage
    :type val: string
    """
    temp = 0
    info = gcore.parse_command('r.report', flags='nh', map=raster, units='p')
    for somestring in info.keys():
        if ((' %s|' % val) in somestring) or (('|%s|' % val) in somestring):
            temp = somestring.split('|')[-2]
            return temp


def raster2compressM(A):
    """Return a compress matrix from a raster map"""
    with RasterRow(A, mode='r') as A_ar:
        A_sparse = np.array(A_ar)
    A_sparse[A_sparse == -2147483648] = 0
    A_sparse = csr_matrix(A_sparse)
    return A_sparse


def raster2numpy(A):
    """Return a numpy array from a raster map"""
    with RasterRow(A, mode='r') as array:
        return np.array(array)


def numpy2raster(array, mtype, name):
    """Save a numpy array to a raster map"""
    reg = Region()
    if (reg.rows, reg.cols) != array.shape:
        msg = "Region and array are different: %r != %r"
        raise TypeError(msg % ((reg.rows, reg.cols), array.shape))
    with RasterRow(name, mode='w', mtype=mtype) as new:
        newrow = Buffer((array.shape[1],), mtype=mtype)
        for row in array:
            newrow[:] = row[:]
            new.put_row(newrow)


def remove_pixel_from_raster(lakes, stream):
    """
    Remove pixel belonged to a raster from the second one
    """
    gcore.run_command("v.to.rast", overwrite=True, input=lakes,
                      output="lakes", use="val")
    stream, mset = stream.split('@') if '@' in stream else (stream, '')
    del_lake = '%s=if(%s,if(isnull(lakes),%s,null()),null())' % (stream,
                                                                 stream,
                                                                 stream)
    mapcalc(del_lake, overwrite=True)


def dissolve_lines(in_vec, out_vec):
    """
    If more lines are present for the same category
    it merges them
    """
    gcore.run_command('v.clean', overwrite=True,
                      input=in_vec, output=out_vec,
                      tool='break,snap,rmdupl,rmarea,rmline,rmsa')
    info = gcore.parse_command('v.category',
                               input=out_vec, option='print')
    for i in info.keys():
        #import ipdb; ipdb.set_trace()
        gcore.run_command('v.edit', map=out_vec, tool='merge',
                          cats=i)


def get_coo(raster, i, j):
    """
    Given a raster map and the index i and j of the
    corresponded array obtained with Raster Row
    it computes the coordinate p_x and p_y
    """
    info = gcore.parse_command('r.info', flags='g', map=raster)
    p_y = ((float(info['north'])) - i * (float(info['nsres'])) -
           0.5 * (float(info['nsres'])))
    p_x = ((float(info['west'])) + j * (float(info['ewres'])) +
           0.5 * (float(info['ewres'])))
    return p_x, p_y


if __name__ == "__main__":
    import doctest
    doctest.testmod()
