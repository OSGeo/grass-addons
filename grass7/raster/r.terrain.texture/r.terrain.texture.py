#! /usr/bin/env python
##############################################################################
#
# MODULE:       Unsupervised nested-means algorithm for terrain classification
#
# AUTHOR(S):    Steven Pawley
#
# PURPOSE:      Divides topography based on terrain texture and curvature.
#               Based on the methodology of Iwahashi & Pike (2007)
#               Automated classifications of topography from DEMs by an unsupervised
#               nested-means algorithm and a three-part geometric signature.
#               Geomorphology. 86, 409-440
#
# COPYRIGHT:    (C) 2017 Steven Pawley and by the GRASS Development Team
#
##############################################################################

#%module
#% description: Unsupervised nested-means algorithm for terrain classification
#% keyword: raster
#% keyword: terrain 
#% keyword: classification
#%end

#%option G_OPT_R_INPUT
#% description: Input elevation raster:
#% key: elevation
#% required: yes
#%end

#%option G_OPT_R_INPUT
#% description: Input slope raster:
#% key: slope
#% required: no
#%end

#%option
#% key: flat_thres
#% type: double
#% description: Height threshold for pit and peak detection:
#% answer: 1
#% required: no
#%end

#%option
#% key: curv_thres
#% type: double
#% description: Curvature threshold for convexity and concavity detection:
#% answer: 0
#% required: no
#%end

#%option
#% key: filter_size
#% type: integer
#% description: Size of smoothing filter window:
#% answer: 3
#% guisection: Optional
#%end

#%option
#% key: counting_size
#% type: integer
#% description: Size of counting window:
#% answer: 21
#% guisection: Optional
#%end


#%option
#% key: classes
#% type: integer
#% description: Number of classes in nested terrain classification:
#% options: 8,12,16
#% answer: 8
#% guisection: Optional
#%end

#%option G_OPT_R_OUTPUT
#% description: Output terrain texture:
#% key: texture
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Output terrain convexity:
#% key: convexity
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Output terrain concavity:
#% key: concavity
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Output terrain classification:
#% key: features
#% required : no
#%end

import os
import sys
import random
import string
import math
import numpy as np
from subprocess import PIPE
import atexit
import grass.script as gs
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.script.utils import parse_key_val

TMP_RAST = []

def cleanup():
    gs.message("Deleting intermediate files...")

    for f in TMP_RAST:
        gs.run_command(
            "g.remove", type="raster", name=f, flags="f", quiet=True)

def temp_map(name):
    tmp = name + ''.join(
        [random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST.append(tmp)

    return (tmp)

def parse_tiles(tiles):
    # convert r.tileset output into list of dicts
    tiles = [i.split(';') for i in tiles]
    tiles = [[parse_key_val(i) for i in t] for t in tiles]

    tiles_reg = []
    for index, tile in enumerate(tiles):
        tiles_reg.append({})
        for param in tile:
            tiles_reg[index].update(param)

    return(tiles_reg)


def laplacian_matrix(w):
    s = """TITLE Laplacian filter
    MATRIX {w}
    """.format(w=w)
    
    x = np.zeros((w,w))
    x[:] = -1
    x[w/2, w/2] = (np.square(w))-1
    x_str=str(x)    
    x_str = x_str.replace(' [', '')
    x_str = x_str.replace('[', '')
    x_str = x_str.replace(']', '')
    x_str = x_str.replace('.', '')
    s += x_str
    s += """
    DIVISOR 1
    TYPE P"""
    return s


def categories(nclasses):
    if nclasses == 8:
        s = """1|steep, high convexity, fine-textured
        2|steep, high convexity, coarse-textured
        3|steep, low convexity, fine-textured
        4|steep, low convexity, coarse-textured
        5|gentle, high convexity, fine-textured
        6|gentle, high convexity, coarse-textured
        7|gentle, low convexity, fine-textured
        8|gentle, low convexity, coarse-textured"""
    elif nclasses == 12:
        s = """1|steep, high convexity, fine-textured
        2|steep, high convexity, coarse-textured
        3|steep, low convexity, fine-textured
        4|steep, low convexity, coarse-textured
        5|moderately steep, high convexity, fine-textured
        6|moderately steep, high convexity, coarse-textured
        7|moderately steep, low convexity, fine-textured
        8|moderately steep, low convexity, coarse-textured
        9|gentle, high convexity, fine-textured
        10|gentle, high convexity, coarse-textured
        11|gentle, low convexity, fine-textured
        12|gentle, low convexity, coarse-textured"""
    elif nclasses == 16:
        s = """1|steep, high convexity, fine-textured
        2|steep, high convexity, coarse-textured
        3|steep, low convexity, fine-textured
        4|steep, low convexity, coarse-textured
        5|moderately steep, high convexity, fine-textured
        6|moderately steep, high convexity, coarse-textured
        7|moderately steep, low convexity, fine-textured
        8|moderately steep, low convexity, coarse-textured
        9|slightly steep, high convexity, fine-textured
        10|slightly steep, high convexity, coarse-textured
        11|slightly steep, low convexity, fine-textured
        12|slightly steep, low convexity, coarse-textured
        13|gentle, high convexity, fine-textured
        14|gentle, high convexity, coarse-textured
        15|gentle, low convexity, fine-textured
        16|gentle, low convexity, coarse-textured"""
    return s

def colors(nclasses):
    if nclasses == 8:
        s = """
        1 139:92:20
        2 255:0:0
        3 255:165:0
        4 255:255:0
        5 0:0:255
        6 30:144:255
        7 0:128:0
        8 0:255:3
        nv 255:255:255
        default 255:255:255
        """
    elif nclasses == 12:
        s = """
        1 165:42:42
        2 255:0:0
        3 255:165:0
        4 255:255:0
        5 0:128:0
        6 11:249:11
        7 144:238:144
        8 227:255:227
        9 0:0:255
        10 30:144:255
        11 0:255:231
        12 173:216:230
        nv 255:255:255
        default 255:255:255
        """
    elif nclasses == 16:
        s = """
        1 165:42:42
        2 255:0:0
        3 255:165:0
        4 255:255:0
        5 0:128:0
        6 11:249:11
        7 144:238:144
        8 227:255:227
        9 128:0:128
        10 244:7:212
        11 234:109:161
        12 231:190:225
        13 0:0:255
        14 30:144:255
        15 0:255:231
        16 173:216:230
        nv 255:255:255
        default 255:255:255
        """
    return s


def main():
    elevation = options['elevation']
    slope = options['slope']
    flat_thres = float(options['flat_thres'])
    curv_thres = float(options['curv_thres'])
    filter_size = int(options['filter_size'])
    counting_size = int(options['counting_size'])
    nclasses = int(options['classes'])
    texture = options['texture']
    convexity = options['convexity']
    concavity = options['concavity']
    features = options['features']

    # remove mapset from output name in case of overwriting existing map
    texture = texture.split('@')[0]
    convexity = convexity.split('@')[0]
    concavity = concavity.split('@')[0]
    features = features.split('@')[0]

    # error checking
    if flat_thres < 0:
        gs.fatal('Parameter thres cannot be negative')

    if filter_size % 2 == 0 or counting_size % 2 == 0:
        gs.fatal('Filter or counting windows require an odd-numbered window size')

    if filter_size >= counting_size:
        gs.fatal('Filter size needs to be smaller than the counting window size')

    # store current region settings
    current_reg = parse_key_val(
        g.region(flags='pg', stdout_=PIPE).outputs.stdout)
    del current_reg['projection']
    del current_reg['zone']
    del current_reg['cells']
    
    # check for existing mask
    mask_test = gs.list_grouped(
        type='rast', pattern='MASK')[gs.gisenv()['MAPSET']]
    if mask_test:
        # backup old mask
        original_mask = temp_map('tmp_original_mask')
        g.copy(raster=['MASK', original_mask])
        
        # create mask of input elevation
        elevation_mask = temp_map('tmp_elevation_mask')
        tmp = gs.tempfile()
        rc = open('%s' % (tmp), 'wt')
        rc.write('* = 0')
        rc.close()
        
        r.reclass(input=elevation, output=elevation_mask, rules=tmp)
        new_mask = temp_map('tmp_new_mask')
        r.mapcalc(expression='{a}={b}'.format(a=new_mask, b=elevation_mask))
        
    # Terrain Surface Texture -------------------------------------------------
    # smooth the dem
    gs.message("Calculating terrain surface texture...")
    gs.message("1. Smoothing input DEM with a {n}x{n} median filter...".format(n=filter_size))
    filtered_dem = temp_map('tmp_filtered_dem')
    gs.run_command("r.neighbors", input = elevation, method = "median",
                   size = filter_size, output = filtered_dem, flags='c',
                   quiet=True)

    # extract the pits and peaks based on the threshold
    pitpeaks = temp_map('tmp_pitpeaks')
    gs.message("2. Extracting pits and peaks with difference > thres...")
    r.mapcalc(expression='{x} = if ( abs({dem}-{median})>{thres}, 1, 0)'.format(
                x=pitpeaks, dem=elevation, thres=flat_thres, median=filtered_dem),
                quiet=True)

    # calculate density of pits and peaks
    gs.message("3. Using resampling filter to create terrain texture...")
    window_radius = (counting_size-1)/2
    y_radius = float(current_reg['ewres'])*window_radius
    x_radius = float(current_reg['nsres'])*window_radius

    resample = temp_map('tmp_density')
    r.resamp_filter(input=pitpeaks, output=resample, filter=['bartlett','gauss'],
                    radius=[x_radius,y_radius], quiet=True)

    # convert to percentage
    if mask_test:
        r.mask(raster=new_mask, overwrite=True, quiet=True)
    else:
        r.mask(raster=elevation, overwrite=True, quiet=True)

    gs.message("4. Converting to percentage...")
    r.mapcalc(expression='{x} = float({y} * 100)'.format(x=texture, y=resample),
               quiet=True)
    if mask_test:
        r.mask(raster=original_mask, overwrite=True, quiet=True)
    else:
        r.mask(flags='r', quiet=True)

    # set colors
    r.colors(map=texture, color='haxby', quiet=True)

    # Terrain convexity/concavity ---------------------------------------------
    # surface curvature using lacplacian filter
    gs.message("Calculating terrain convexity and concavity...")
    gs.message("1. Calculating terrain curvature using laplacian filter...")
    
    # grow the map to remove border effects
    dem_grown = temp_map('tmp_elevation_grown')
    g.region(n=float(current_reg['n']) + (float(current_reg['nsres']) * filter_size),
             s=float(current_reg['s']) - (float(current_reg['nsres']) * filter_size),
             w=float(current_reg['w']) - (float(current_reg['ewres']) * filter_size),
             e=float(current_reg['e']) + (float(current_reg['ewres']) * filter_size))
    r.grow(input=elevation, output=dem_grown, radius=filter_size, quiet=True)
    
    # write matrix filter to tempfile
    tmp = gs.tempfile()
    lmatrix = open('%s' % (tmp), 'wt')
    lmatrix.write(laplacian_matrix(filter_size))
    lmatrix.close()
    
    laplacian = temp_map('tmp_laplacian')
    r.mfilter(input=dem_grown, output=laplacian, filter=tmp, quiet=True)

    # extract convex and concave pixels
    gs.message("2. Extracting convexities and concavities...")
    convexities = temp_map('tmp_convexities')
    concavities = temp_map('tmp_concavities')

    r.mapcalc(
        expression='{x} = if({laplacian}>{thres}, 1, 0)'\
        .format(x=convexities, laplacian=laplacian, thres=curv_thres),
        quiet=True)
    r.mapcalc(
        expression='{x} = if({laplacian}<-{thres}, 1, 0)'\
        .format(x=concavities, laplacian=laplacian, thres=curv_thres),
        quiet=True)

    # calculate density of convexities and concavities
    gs.message("3. Using resampling filter to create surface convexity/concavity...")
    resample_convex = temp_map('tmp_convex')
    resample_concav = temp_map('tmp_concav')
    r.resamp_filter(input=convexities, output=resample_convex,
                    filter=['bartlett','gauss'], radius=[x_radius,y_radius],
                    quiet=True)
    r.resamp_filter(input=concavities, output=resample_concav,
                    filter=['bartlett','gauss'], radius=[x_radius,y_radius],
                    quiet=True)

    # convert to percentages
    g.region(**current_reg)
    if mask_test:
        r.mask(raster=new_mask, overwrite=True, quiet=True)
    else:
        r.mask(raster=elevation, overwrite=True, quiet=True)
    gs.message("4. Converting to percentages...")
    r.mapcalc(expression='{x} = float({y} * 100)'.format(x=convexity, y=resample_convex),
               quiet=True)
    r.mapcalc(expression='{x} = float({y} * 100)'.format(x=concavity, y=resample_concav),
               quiet=True)
    if mask_test:
        r.mask(raster=original_mask, overwrite=True, quiet=True)
    else:
        r.mask(flags='r', quiet=True)

    # set colors
    r.colors_stddev(map=convexity, quiet=True)
    r.colors_stddev(map=concavity, quiet=True)

    # Terrain classification Flowchart-----------------------------------------
    if features != '':
        gs.message("Performing terrain surface classification...")
        # output result as final classification if nclasses == 8
        # else pass temporary result to next threshold
        if nclasses >= 8:
            if nclasses == 8:
                cla1_8=features
            else:
                cla1_8 = temp_map('tmp_classes1_8')

            # gather univariate statistics for terrain maps
            slope_mean = parse_key_val(r.univar(
                map=slope, flags='g', stdout_=PIPE).outputs.stdout)['mean']
            convex_mean = parse_key_val(r.univar(
                map=convexity, flags='g', stdout_=PIPE).outputs.stdout)['mean']
            texture_mean = parse_key_val(r.univar(
                map=texture, flags='g', stdout_=PIPE).outputs.stdout)['mean']

            # calculate first threshold
            r.mapcalc(
                expression='{x} = if({s}>{smean}, if({c}>{cmean}, if({t}<{tmean}, 1, 2), if({t}<{tmean}, 3,4)), if({c}>{cmean}, if({t}<{tmean}, 5, 6), if({t}<{tmean}, 7, 8)))'\
                .format(x=cla1_8,
                        s=slope, smean=slope_mean,
                        t=texture, tmean=texture_mean,
                        c=convexity, cmean=convex_mean))

        if nclasses >= 12:
            cla9_12 = temp_map('tmp_classes9_12')

            # output result as final classification if nclasses == 12
            # else pass temporary result to next threshold
            if nclasses == 12:
                cla1_12 = features
            else:
                cla1_12 = temp_map('tmp_classes1_12')

            # get projection and create tiles
            proj = g.proj(flags='jf', stdout_=PIPE).outputs.stdout.strip(os.linesep)
            tiles = r.tileset(
                sourceproj=proj,
                maxcols=int(math.ceil(float(current_reg['cols'])+1 / 2)),
                maxrows=int(math.ceil(float(current_reg['rows'])+2)),
                flags='g', quiet=True, stdout_=PIPE).outputs.stdout.split(os.linesep)[:-1]
            tiles_reg = parse_tiles(tiles)

            # get image means in each tile
            slope_stats, convex_stats, texture_stats = [],[],[]
            for tile in tiles_reg:
                g.region(**tile)
                slope_stats.append(parse_key_val(r.univar(
                    map=slope, flags='g', stdout_=PIPE).outputs.stdout)['mean'])
                convex_stats.append(parse_key_val(r.univar(
                    map=convexity, flags='g', stdout_=PIPE).outputs.stdout)['mean'])
                texture_stats.append(parse_key_val(r.univar(
                    map=texture, flags='g', stdout_=PIPE).outputs.stdout)['mean'])

            # calculate second threshold classes
            g.region(**current_reg)
            r.mapcalc(
                expression='{x} = if({s}>{smean}, if({c}>{cmean}, if({t}<{tmean}, 5, 6), if({t}<{tmean}, 7,8)), if({c}>{cmean}, if({t}<{tmean}, 9, 10), if({t}<{tmean}, 11, 12)))'\
                .format(x=cla9_12,
                        s=slope, smean=min(slope_stats),
                        t=texture, tmean=min(texture_stats),
                        c=convexity, cmean=min(convex_stats)))

            r.mapcalc(
                expression='{x} = if({a}>5, {b}, {a})'.format(x=cla1_12, a=cla1_8,  b=cla9_12))

        if nclasses == 16:
            cla9_16 = temp_map('tmp_classes9_16')

            # get projection and create tiles
            tiles = r.tileset(
                sourceproj=proj,
                maxcols=int(math.ceil(float(current_reg['cols'])+1 / 2)),
                maxrows=int(math.ceil(float(current_reg['rows'])+1 / 2)),
                flags='g', quiet=True, stdout_=PIPE).outputs.stdout.split(os.linesep)[:-1]
            tiles_reg = parse_tiles(tiles)

            # get image means in each tile
            slope_mean, convex_mean, texture_mean = [],[],[]
            for tile in tiles_reg:
                g.region(**tile)
                slope_mean.append(parse_key_val(r.univar(
                    map=slope, flags='g', stdout_=PIPE).outputs.stdout)['mean'])
                convex_mean.append(parse_key_val(r.univar(
                    map=convexity, flags='g', stdout_=PIPE).outputs.stdout)['mean'])
                texture_mean.append(parse_key_val(r.univar(
                    map=texture, flags='g', stdout_=PIPE).outputs.stdout)['mean'])

            # third threshold
            g.region(**current_reg)
            r.mapcalc(
                expression='{x} = if({s}>{smean}, if({c}>{cmean}, if({t}<{tmean}, 9, 10), if({t}<{tmean}, 11, 12)), if({c}>{cmean}, if({t}<{tmean}, 13, 14), if({t}<{tmean}, 15, 16)))'\
                .format(x=cla9_16,
                        s=slope, smean=min(slope_mean),
                        t=texture, tmean=min(texture_mean),
                        c=convexity, cmean=min(convex_mean)))

            r.mapcalc(
                expression='{x} = if({a}>8, {b}, {a})'.format(x=features, a=cla1_12, b=cla9_16))


    # Write metadata ----------------------------------------------------------
    history = 'r.terrain.texture '
    for key,val in options.iteritems():
        history += key + '=' + str(val) + ' '

    r.support(map=texture,
              title=texture,
              description='generated by r.terrain.texture',
              history=history)
    r.support(map=convexity,
              title=convexity,
              description='generated by r.terrain.texture',
              history=history)
    r.support(map=concavity,
              title=concavity,
              description='generated by r.terrain.texture',
              history=history)

    if features != '':
        r.support(map=features,
                  title=features,
                  description='generated by r.terrain.texture',
                  history=history)
        
        # write color and category rules to tempfiles
        tmp_col = gs.tempfile()
        col = open('%s' % (tmp_col), 'wt')
        col.write(colors(nclasses))
        col.close()
        
        tmp_cat = gs.tempfile()
        cat = open('%s' % (tmp_cat), 'wt')
        cat.write(categories(nclasses))
        cat.close()
        
        r.category(map=features, rules=tmp_cat, separator='pipe')
        r.colors(map=features, rules=tmp_col, quiet=True)

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
