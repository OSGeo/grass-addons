#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# MODULE:     r.sample.category
# AUTHOR(S):  Vaclav Petras <wenzeslaus gmail com>
#             Anna Petrasova <kratochanna gmail com>
# PURPOSE:    Sample points from each category
# COPYRIGHT:  (C) 2015 by Vaclav Petras, and the GRASS Development Team
#
#             This program is free software under the GNU General Public
#             License (>=v2). Read the COPYING file that comes with GRASS
#             for details.
#
##############################################################################


#%module
#% description: Create sampling points from each category in a raster map
#% keyword: raster
#% keyword: sampling
#% keyword: random
#% keyword: points
#% keyword: vector
#% keyword: stratified sampling
#%end
#%option G_OPT_R_INPUT
#% description: Name of input raster map with categories (classes)
#%end
#%option G_OPT_V_OUTPUT
#% description: Name of output vector map with points at random locations
#%end
#%option G_OPT_R_INPUTS
#% description: Names of input raster maps to be sampled
#% key: sampled
#% required: no
#%end
#%option
#% label: Number of sampling points per category in the input map
#% description: You can provide multiple numbers, one for each category in input raster (sorted ascending)
#% key: npoints
#% required: yes
#% multiple: yes
#% type: integer
#%end

# TODO: Python tests for more advanced things such as overwrite or attributes
# TODO: only optional sampling of the category raster
# TODO: preserver original raster categories as vector point categories
# TODO: ensure/check minimum number of points in each category
# TODO: specify number of points and distribute them uniformly
# TODO: specify number of points and distribute them according to histogram
# TODO: ensure/check minimum and maximum number of of points when doing histogram
# TODO: create function to check for mask
# TODO: move escape and mask functions to library

import os
import atexit

import grass.script as gscript


TMP = []


def cleanup():
    if gscript.find_file(name='MASK', element='cell', mapset=gscript.gisenv()['MAPSET'])['name']:
        gscript.run_command('r.mask', flags='r')
    if TMP:
        gscript.run_command('g.remove', flags='f', type=['raster', 'vector'], name=TMP)


def escape_sql_column(name):
    """Escape string to create a safe name of column for SQL

    >>> escape_sql_column("elevation.10m")
    elevation_10m
    """
    name = name.replace('.', '_')
    return name


def strip_mapset(name):
    """Strip Mapset name and '@' from map name

    >>> strip_mapset('elevation@PERMANENT')
    elevation
    """
    if '@' in name:
        return name.split('@')[0]
    return name


def main():
    options, flags = gscript.parser()

    input_raster = options['input']
    points = options['output']
    if options['sampled']:
        sampled_rasters = options['sampled'].split(',')
    else:
        sampled_rasters = []
    npoints = [int(num) for num in options['npoints'].split(',')]

    if gscript.find_file(name='MASK', element='cell', mapset=gscript.gisenv()['MAPSET'])['name']:
        gscript.fatal(_("MASK is active. Please remove it before proceeding."))

    # we clean up mask too, so register after we know that mask is not present
    atexit.register(cleanup)

    temp_name = 'tmp_r_sample_category_{}_'.format(os.getpid())
    points_nocats = temp_name + 'points_nocats'
    TMP.append(points_nocats)

    # input must be CELL
    rdescribe = gscript.read_command('r.describe', map=input_raster, flags='d1', quiet=True)
    categories = []
    for line in rdescribe.splitlines():
        try:
            categories.append(int(line))
        except ValueError:
            pass
    if len(npoints) == 1:
        npoints = npoints * len(categories)
    else:
        if len(categories) != len(npoints):
            gscript.fatal(_("Number of categories in raster does not match the number of provided sampling points numbers."))

    vectors = []
    for i, cat in enumerate(categories):
        # skip generating points if none are required
        if npoints[i] == 0:
            continue
        gscript.info(_("Selecting {n} sampling locations at category {cat}...").format(n=npoints[i], cat=cat))
        # change mask to sample zeroes and then change again to sample ones
        # overwrite mask for an easy loop
        gscript.run_command('r.mask', raster=input_raster, maskcats=cat, overwrite=True, quiet=True)
        vector = temp_name + str(cat)
        vectors.append(vector)
        gscript.run_command('r.random', input=input_raster, npoints=npoints[i], vector=vector, quiet=True)
        TMP.append(vector)

    gscript.run_command('r.mask', flags='r', quiet=True)

    gscript.run_command('v.patch', input=vectors, output=points, quiet=True)
    # remove and add gain cats so that they are unique
    gscript.run_command('v.category', input=points, option='del', cat=-1, output=points_nocats, quiet=True)
    # overwrite to reuse the map
    gscript.run_command('v.category', input=points_nocats, option='add', output=points, overwrite=True, quiet=True)

    columns = []
    column_names = []
    sampled_rasters.insert(0, input_raster)
    for raster in sampled_rasters:
        column = escape_sql_column(strip_mapset(raster).lower())
        column_names.append(column)
        # TODO: column type according to map type
        columns.append("{column} double precision".format(column=column))
    gscript.run_command('v.db.addtable', map=points, columns=','.join(columns), quiet=True)
    for raster, column in zip(sampled_rasters, column_names):
        gscript.info(_("Sampling raster map %s...") % raster)
        gscript.run_command('v.what.rast', map=points, type='point', raster=raster, column=column, quiet=True)


if __name__ == '__main__':
    main()
