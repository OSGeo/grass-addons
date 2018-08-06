#!/usr/bin/env python

############################################################################
#
# MODULE:	    r.in.pdal
#
# AUTHOR(S):    Anika Bettge <bettge at mundialis.de>
#               Thanks to Markus Neteler <neteler at mundialis.de> for help
#
# PURPOSE:      Creates a raster map from LAS LiDAR points using univariate statistics and r.in.xyz.
#
# COPYRIGHT:	(C) 2018 by mundialis and the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#% description:  Creates a raster map from LAS LiDAR points using univariate statistics and r.in.xyz.
#% keyword: raster
#% keyword: import
#% keyword: LIDAR
#% keyword: statistics
#% keyword: conversion
#% overwrite: yes
#%End

#%option G_OPT_R_INPUT
#% key: input
#% description: LAS input file
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% key: output
#% description: Name for output raster map
#% required: yes
#%end

#%option
#% key: resolution
#% type: double
#% description: 2D grid resolution (north-south and east-west)
#% answer: 1.0
#% required: no
#%end

#%option
#% key: raster_reference
#% label: Raster map to be used as pixel geometry reference
#% description: Raster map to align to, e.g. an orthophoto of the same region
#% required: no
#%end

#%option
#% key: raster_file
#% label: External raster map to be used as pixel geometry reference
#% description: External raster map to align to, e.g. an orthophoto of the same region
#% required: no
#%end

#%option
#% key: method
#% type: string
#% description: Statistic to use for raster values
#% options: n, min, max, range, sum, mean, stddev, variance, coeff_var, median, percentile, skewness, trimmean
#% answer: mean
#% descriptions: n;Number of points in cell;min;Minimum value of point values in cell;max;Maximum value of point values in cell;range;Range of point values in cell;sum;Sum of point values in cell;mean;Mean (average) value of point values in cell;stddev;Standard deviation of point values in cell;variance;Variance of point values in cell;coeff_var;Coefficient of variance of point values in cell;median;Median value of point values in cell;percentile;Pth (nth) percentile of point values in cell;skewness;Skewness of point values in cell
#% required: no
#%end

#%option
#% key: zrange
#% type: double
#% key_desc: min,max
#% description: Filter range for z data (min,max)
#% required: no
#%end

#%option
#% key: zscale
#% type: double
#% description: Scale to apply to z data
#% answer: 1.0
#% required: no
#%end

#%option
#% key: type
#% type: string
#% description: Type of raster map to be created / Storage type for resultant raster map
#% options: CELL, FCELL, DCELL
#% answer: FCELL
#% required: no
#% descriptions: CELL;Integer;FCELL;Single precision floating point;DCELL;Double precision floating point
#%end

#%option
#% key: percent
#% type: integer
#% description: Percent of map to keep in memory
#% options: 1-100
#% answer: 100
#% required: no
#%end

#%option
#% key: pth
#% type: integer
#% description: Pth percentile of the values
#% options: 1-100
#% required: no
#%end

#%option
#% key: trim
#% type: double
#% description: Discard <trim> percent of the smallest and <trim> percent of the largest observations
#% options: 1-50
#% required: no
#%end

#%option
#% key: footprint
#% type: string
#% description: Footprint of the data as vector map
#% required: no
#%end

#%flag
#% key: s
#% description: Scan data file for extent then exit
#%end

#%flag
#% key: g
#% description: In scan mode, print using shell script style
#%end

import os
import sys

import grass.script as grass
import tempfile
import json

# i18N
import gettext
gettext.install('grassmods', os.path.join(os.getenv("GISBASE"), 'locale'))

def footprintToVectormap(infile, footprint):
    if not grass.find_program('pdal', 'info --boundary'):
        grass.fatal(_("pdal info --boundary is not in the path and executable"))
    command_fp = ['pdal','info','--boundary',infile]
    tmp_fp = os.path.join(tempfile.gettempdir(), 'fp.txt')
    fh = open(tmp_fp, 'wb')
    p = grass.call(command_fp, stdout=fh)
    fh.close()
    if p != 0:
        # check to see if gdalwarp executed properly
        os.remove(tmp_fp)
        grass.fatal(_("pdal info broken..."))

    str1 = u'boundary'
    str2 = u'boundary_json'
    str3 = u'coordinates'
    data = json.load(open(tmp_fp))
    coord = data[str1][str2][str3][0][0]
    xy_in = ''
    for xy in coord:
        xy_in += str(xy[0]) + ',' + str(xy[1]) + '\n'
    tmp_xy = os.path.join(tempfile.gettempdir(), 'xy.txt')
    f = open(tmp_xy,'w')
    f.write(xy_in[:-1])
    f.close()
    grass.run_command('v.in.lines',input=tmp_xy,output='footprint_line',separator='comma')
    grass.run_command('g.region',vector='footprint_line')
    grass.run_command('v.type',input='footprint_line', out='footprint_boundary', from_type='line', to_type='boundary')
    grass.run_command('v.centroids',input='footprint_boundary', out=footprint)
    grass.run_command('v.db.addtable',map=footprint,columns='name varchar(50)')
    grass.run_command('v.db.update',map=footprint,column='name', value=infile)

    # Cleaning up
    grass.message(_("Cleaning up..."))
    os.remove(tmp_fp)
    os.remove(tmp_xy)
    grass.run_command('g.remove', flags='f', type='vector', name='footprint_line', quiet=True)
    grass.run_command('g.remove', flags='f', type='vector', name='footprint_boundary', quiet=True)
    grass.message(_("Generating output vactor map <%s>...") % footprint)

def main():
    # parameters
    infile = options['input']
    raster_reference = options['raster_reference']
    raster_file = options['raster_file']
    outfile = options['output']
    resolution = options['resolution']
    method = options['method']
    zrange = options['zrange']
    zscale = options['zscale']
    output_type = options['type']
    percent = options['percent']
    pth = options['pth']
    trim = options['trim']
    footprint = options['footprint']
    # flags
    scan = flags['s']
    shell_script_style = flags['g']

    # overwrite auf true setzen
    os.environ['GRASS_OVERWRITE'] = '1'

    # to hide non-error messages from subprocesses
    if grass.verbosity() <= 2:
        outdev = open(os.devnull, 'w')
    else:
        outdev = sys.stdout

    # scan -s or shell_script_style -g:
    if scan: # or shell_script_style:
        if not grass.find_program('pdal', 'info --summary'):
            grass.fatal(_("The pdal program is not in the path and executable. Please install first"))
        command_scan = ['pdal','info','--summary', infile]
        tmp_scan = os.path.join(tempfile.gettempdir(), 'scan.txt')
        fh = open(tmp_scan, 'wb')
        p = grass.call(command_scan, stdout=fh)
        fh.close()
        summary = True
        if p != 0:
            command_scan = ['pdal','info',infile]
            fh = open(tmp_scan, 'wb')
            p = grass.call(command_scan, stdout=fh)
            fh.close()
            summary = False
        if p != 0:
            # check to see if pdal executed properly
            os.remove(tmp_scan)
            grass.fatal(_("pdal cannot determine metadata for unsupported format of <%s>") %infile )
        data = json.load(open(tmp_scan))
        if summary:
            str1 = u'summary'
            str2 = u'bounds'
            y_str = u'Y'
            x_str = u'X'
            z_str = u'Z'
            min_str =  u'min'
            max_str = u'max'
            n = str(data[str1][str2][y_str][max_str])
            s = str(data[str1][str2][y_str][min_str])
            w = str(data[str1][str2][x_str][min_str])
            e = str(data[str1][str2][x_str][max_str])
            t = str(data[str1][str2][z_str][max_str])
            b = str(data[str1][str2][z_str][min_str])
        else:
            str1 = u'stats'
            str2 = u'bbox'
            str3 = u'native'
            str4 = u'bbox'
            n = str(data[str1][str2][str3][str4][u'maxy'])
            s = str(data[str1][str2][str3][str4][u'miny'])
            w = str(data[str1][str2][str3][str4][u'minx'])
            e = str(data[str1][str2][str3][str4][u'maxx'])
            t = str(data[str1][str2][str3][str4][u'maxz'])
            b = str(data[str1][str2][str3][str4][u'minz'])
        if not shell_script_style:
            print('north: ' + n + '\n' + 'south: ' + s + '\n' +
            'west:   ' + w + '\n' + 'east:   ' + e + '\n' +
            'top:     ' + t + '\n' + 'bottom:  ' + b)
        else:
            print('n=' + n + ' ' + 's=' + s + ' ' + 'w=' + w + ' ' +
            'e=' + e + ' ' + 't=' + t + ' ' + 'b=' + b)
    elif footprint:
        print 'footprint'
        footprintToVectormap(infile, footprint)
    else:
        # get region with pdal
        footprintToVectormap(infile, 'tiles')

        if raster_file:
            raster_reference = 'img.1'
            grass.run_command('r.external', input=raster_file, flags="o", output='img', overwrite=True)
        # first pass: set region to extent of tiles while aligning pixel geometry to raster_reference
        grass.run_command('g.region',vector='tiles', flags='p')
        if raster_reference:
            grass.run_command('g.region',vector='tiles', flags='ap', align=raster_reference)
        # second pass: change raster resolution to final resolution while best effort aligning to pixel geometry
        grass.run_command('g.region',vector='tiles', flags='ap', res=resolution)

        # . pdal pipline laz2json (STDOUT) | r.in.xyz
        bn=os.path.basename(infile)
        infile_format = bn.split('.')[-1]
        formatReader = '' # from https://pdal.io/stages/readers.html
        if infile_format.lower() == 'laz' or infile_format.lower() == 'las':
            formatReader = 'readers.las'
        elif infile_format.lower() == 'pts': # nicht getestet
            formatReader = 'readers.pts'
        else:
            # check to see if gdalwarp executed properly
            grass.run_command('g.remove', flags='f', type='vector', name='tiles', quiet=True)
            grass.fatal(_("Format .%s is not supported.." % infile_format))
        tmp_file_json = os.path.join(tempfile.gettempdir(), 'las2txt.json')
        data = {}
        data['pipeline'] = []
        data['pipeline'].append({'type': formatReader,'filename': infile})
        data['pipeline'].append({
            'type': 'writers.text',
            'format': 'csv',
            'order': 'X,Y,Z',
            'keep_unspecified':'false',
            'filename':'STDOUT',
            'quote_header':'false'})
        with open(tmp_file_json, 'w') as f:
            json.dump(data, f)

        tmp_xyz = os.path.join(tempfile.gettempdir(), 'tmp_xyz.txt')
        command_pdal1 = ['pdal','pipeline','--input',tmp_file_json]
        command_pdal2 = ['r.in.xyz','input=' + tmp_xyz,'output=' + outfile,
            'skip=1','separator=comma', 'method=' + method]

        if zrange:
            command_pdal2.append('zrange=' + zrange)
        if zscale:
            command_pdal2.append('zscale=' + zscale)
        if output_type:
            command_pdal2.append('type=' + output_type)
        if percent:
            command_pdal2.append('percent=' + percent)
        if pth:
            command_pdal2.append('pth=' + pth)
        if trim:
            command_pdal2.append('trim=' + trim)

        fh = open(tmp_xyz, 'wb')
        p2 = grass.call(command_pdal1,stdout=fh)
        fh.close()
        if p2 != 0:
            # check to see if gdalwarp executed properly
            grass.fatal(_("pdal pipeline is broken..."))

        p3 = grass.call(command_pdal2,stdout=outdev)
        if p3 != 0:
            # check to see if gdalwarp executed properly
            os.remove(tmp_xyz)
            grass.fatal(_("r.in.xyz is broken..."))

        # Cleanup
        grass.message(_("Cleaning up..."))
        grass.run_command('g.remove', flags='f', type='vector', name='tiles', quiet=True)
        os.remove(tmp_file_json)
        os.remove(tmp_xyz)
        grass.message(_("Generating output raster map <%s>...") % outfile)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
