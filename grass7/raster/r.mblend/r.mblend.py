#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:       r.mblend
#
# AUTHOR(S):    Luís Moreira de Sousa
#
# PURPOSE:      Blends two rasters of different spatial resolution.
#
# COPYRIGHT:    (c) 2017 Luís Moreira de Sousa
#
#               This programme is released under the European Union Public
#               Licence v 1.1. Please consult the LICENCE file for details.
#
#############################################################################

#%module
#% description: Blends two rasters of different spatial resolution.
#% keyword: raster
#% keyword: resolution
#%end
#%option HIGH
#% key: high
#%end
#%option LOW
#% key: low
#%end
#%option OUTPUT
#% key: output
#%end
#%option FAR_EDGE
#% key: far_edge
#% key_desc: value
#% type: double
#% description: Percentage of distance to high resolution raster used to determine far edge. Number between 0 and 100.
#% answer: 95
#% multiple: no
#% required: no
#%end
#%option INTER_POINTS
#% key: inter_points
#% key_desc: value
#% type: integer
#% description: Number of points to use in interpolation. A higher number produces a smoother result but requires a lengthier computation.
#% answer: 50
#% multiple: no
#% required: no
#%end

import os
import atexit
from time import gmtime, strftime
import grass.script as gscript

index = 0
TMP_MAPS = []
WEIGHT_MAX = 10000
COL_VALUE = 'value'
COL_FLAG = 'flag'


def getTemporaryIdentifier():
    global index
    global TMP_MAPS
    id = 'tmp_' + str(os.getpid()) + str(index)
    index = index + 1
    TMP_MAPS.append(id)
    return id


def cleanup():
    while len(TMP_MAPS) > 0:
        gscript.run_command('g.remove', type='all', name=TMP_MAPS.pop(),
                            flags='f', quiet=True)


def main():

    options, flags = gscript.parser()
    high = options['high']
    low = options['low']
    output = options['output']
    far_edge = float(options['far_edge'])
    inter_points = int(options['inter_points'])

    if(high is None or high == ""):
        gscript.error(_("[r.mblend] ERROR: high is a mandatory parameter."))
        exit()

    if(low is None or low == ""):
        gscript.error(_("[r.mblend] ERROR: low is a mandatory parameter."))
        exit()

    if(output is None or output == ""):
        gscript.error(_("[r.mblend] ERROR: output is a mandatory parameter."))
        exit()

    if(far_edge < 0 or far_edge > 100):
        gscript.error(_("[r.mblend] ERROR: far_edge must be a percentage",
                        " between 0 and 100."))
        exit()

    if(inter_points < 0):
        gscript.error(_("[r.mblend] ERROR: inter_points must be a positive",
                        " integer."))
        exit()

    # Set the region to the two input rasters
    gscript.run_command('g.region', raster=high + "," + low)
    # Determine cell side
    region = gscript.region()
    if region['nsres'] > region['ewres']:
        cell_side = region['nsres']
    else:
        cell_side = region['ewres']

    # Make cell size compatible
    low_res_inter = getTemporaryIdentifier()
    gscript.message(_("[r.mblend] Resampling low resolution raster to higher" +
                      " resolution"))
    gscript.run_command('r.resamp.interp', input=low, output=low_res_inter,
                        method='nearest')

    # Obtain extent to interpolate
    low_extent_rast = getTemporaryIdentifier()
    high_extent_rast = getTemporaryIdentifier()
    low_extent = getTemporaryIdentifier()
    high_extent = getTemporaryIdentifier()
    interpol_area = getTemporaryIdentifier()
    gscript.message(_("[r.mblend] Multiplying low resolution by zero"))
    gscript.mapcalc(low_extent_rast + ' = ' + low + ' * 0')
    gscript.message(_("[r.mblend] Multiplying high resolution by zero"))
    gscript.mapcalc(high_extent_rast + ' = ' + high + ' * 0')
    gscript.message(_("[r.mblend] Computing extent of low resolution"))
    gscript.run_command('r.to.vect', input=low_extent_rast, output=low_extent,
                        type='area')
    gscript.message(_("[r.mblend] Computing extent of high resolution"))
    gscript.run_command('r.to.vect', input=high_extent_rast,
                        output=high_extent, type='area')
    gscript.message(_("[r.mblend] Computing area to interpolate"))
    gscript.run_command('v.overlay', ainput=low_extent, binput=high_extent,
                        output=interpol_area, operator='not')

    # Compute difference between the two rasters and vectorise to points
    diff = getTemporaryIdentifier()
    diff_points = getTemporaryIdentifier()
    gscript.mapcalc(diff + ' = ' + high + ' - ' + low_res_inter)
    gscript.message(_("[r.mblend] Vectorising differences between input" +
                      " rasters"))
    gscript.run_command('r.to.vect', input=diff, output=diff_points,
                        type='point')

    # Obtain edge points of the high resolution raster
    interpol_area_buff = getTemporaryIdentifier()
    diff_points_edge = getTemporaryIdentifier()
    # 1. buffer around area of interest - pixel size must be known
    gscript.message(_("[r.mblend] Computing buffer around interpolation area"))
    gscript.run_command('v.buffer', input=interpol_area,
                        output=interpol_area_buff, type='area',
                        distance=cell_side)
    # 2. get the points along the edge
    gscript.message(_("[r.mblend] Selecting points along the near edge"))
    gscript.run_command('v.select', ainput=diff_points,
                        binput=interpol_area_buff, output=diff_points_edge,
                        operator='overlap')

    # Get points in low resolution farther away from high resolution raster
    dist_high = getTemporaryIdentifier()
    weights = getTemporaryIdentifier()
    weight_points = getTemporaryIdentifier()
    interpol_area_in_buff = getTemporaryIdentifier()
    weight_points_all_edges = getTemporaryIdentifier()
    weight_points_edge = getTemporaryIdentifier()
    # 1. Distance to High resolution raster
    gscript.message(_("[r.mblend] Computing distance to high resolution" +
                      " raster"))
    gscript.run_command('r.grow.distance', input=high, distance=dist_high)
    # 2. Rescale to the interval [0,10000]: these are the weights
    gscript.message(_("[r.mblend] Rescaling distance to [0,10000] interval"))
    gscript.run_command('r.rescale', input=dist_high, output=weights,
                        to='0,' + str(WEIGHT_MAX))
    # 3. Vectorise distances to points
    gscript.message(_("[r.mblend] Vectorising distances to points"))
    gscript.run_command('r.to.vect', input=weights, output=weight_points,
                        type='point')
    # 4. Create inner buffer to interpolation area
    gscript.message(_("[r.mblend] Computing inner buffer to" +
                      " interpolation area"))
    gscript.run_command('v.buffer', input=interpol_area,
                        output=interpol_area_in_buff, type='area',
                        distance='-' + str(cell_side))
    # 5. Select points at the border
    gscript.message(_("[r.mblend] Selecting all points around inner buffer"))
    gscript.run_command('v.select', ainput=weight_points,
                        binput=interpol_area_in_buff,
                        output=weight_points_all_edges, operator='disjoint')
    # 6. Select those with higher weights
    cut_off = str(far_edge / 100 * WEIGHT_MAX)
    gscript.message(_("[r.mblend] Selecting far edge points (using cut-off" +
                      " percentage)"))
    gscript.run_command('v.extract', input=weight_points_all_edges,
                        output=weight_points_edge,
                        where=COL_VALUE + '>' + cut_off)

    # Merge the two point edges and set low res edge to zero
    points_edges = getTemporaryIdentifier()
    gscript.message(_("[r.mblend] Setting far edge weights to zero"))
    gscript.run_command('v.db.update', map=weight_points_edge,
                        column=COL_VALUE, value='0')
    gscript.message(_("[r.mblend] Patching the two edges"))
    gscript.run_command('v.patch',
                        input=weight_points_edge + ',' + diff_points_edge,
                        output=points_edges, flags='e')

    # Interpolate stitching raster
    stitching_full = getTemporaryIdentifier()
    interpol_area_mask = getTemporaryIdentifier()
    stitching = getTemporaryIdentifier()
    gscript.message(_("[r.mblend] Interpolating smoothing surface. This" +
                      " might take a while..."))
    gscript.run_command('v.surf.idw', input=points_edges, column=COL_VALUE,
                        output=stitching_full, power=2, npoints=inter_points)
    # Create mask
    gscript.message(_("[r.mblend] Creating mask for the interpolation area"))
    gscript.run_command('v.to.rast', input=interpol_area,
                        output=interpol_area_mask, use='val', value=1)
    # Crop to area of interest
    gscript.message(_("[r.mblend] Cropping the mask"))
    gscript.mapcalc(stitching + ' = if(' + interpol_area_mask + ',' +
                    stitching_full + ')')

    # Apply stitching
    smooth_low_res = getTemporaryIdentifier()
    # Sum to low res
    gscript.message(_("[r.mblend] Applying smoothing surface"))
    gscript.mapcalc(smooth_low_res + ' = ' + low_res_inter + ' + ' + stitching)
    # Add both rasters
    try:
        gscript.message(_("[r.mblend] Joining result into a single raster"))
        gscript.run_command('r.patch', input=smooth_low_res + ',' + high,
                            output=output)
    except Exception, ex:
        gscript.error(_("[r.mblend] ERROR: Failed to create smoothed raster."))
        exit()

    gscript.message(_("[r.mblend] SUCCESS: smoothed raster created."))


if __name__ == '__main__':
    atexit.register(cleanup)
    gscript.use_temp_region()
    main()
