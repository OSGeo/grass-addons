#!/usr/bin/env python

############################################################################
#
# MODULE:    r.local.relief
# AUTHOR(S): Vaclav Petras <wenzeslaus gmail.com>,
#            Eric Goddard <egoddard memphis.edu>
# PURPOSE:   Create a local relief models from elevation map
# COPYRIGHT: (C) 2013 by the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

#%module
#% description: Creates a local relief models from elevation map.
#% keywords: raster
#% keywords: elevation
#% keywords: terrain
#% keywords: relief
#%end
#%option
#% type: string
#% gisprompt: old,cell,raster
#% key: input
#% description: Name of the input elevation raster map
#% required: yes
#%end
#%option
#% type: string
#% gisprompt: new,cell,raster
#% key: output
#% description: Name for output local relief map
#% required: yes
#%end
#%option
#% key: neighborhood_size
#% type: integer
#% description: Neighborhood size used when smoothing the elevation model
#% options: 0-
#% answer: 3
#%end

# TODO: The step 5 (contours to smooth elevation) can be replaced by using
# vector tools (v.surf.*), this needs further testing.
# Note, that quality of interpolation highly determines the result.

# TODO: implement save intermediate results flag
# (code is ready, but consider also outputting only some useful ones)

import os
import atexit

import grass.script as gscript
import grass.script.core as gcore


RREMOVE = []
VREMOVE = []


def cleanup():
    if RREMOVE or VREMOVE:
        gcore.info(_("Cleaning temporary maps..."))
    for rast in RREMOVE:
        gscript.run_command('g.remove', rast=rast, quiet=True)
    for vect in VREMOVE:
        gscript.run_command('g.remove', vect=vect, quiet=True)


def create_tmp_map_name(name):
    return '{mod}_{pid}_{map_}_tmp'.format(mod='r_shaded_pca',
                                           pid=os.getpid(),
                                           map_=name)


def create_persistent_map_name(basename, name):
    return '{basename}_{name}'.format(basename=basename,
                                      name=name)


def check_map_name(name, mapset, element_type):
    if gscript.find_file(name, element=element_type, mapset=mapset)['file']:
        gscript.fatal(_("Raster map <%s> already exists. "
                        "Change the base name or allow overwrite.") % name)


def main():
    atexit.register(cleanup)
    options, unused = gscript.parser()

    elevation_input = options['input']
    local_relief_output = options['output']
    neighborhood_size = int(options['neighborhood_size'])
    fill_method = 'cubic'

    color_table = 'differences'
    save_intermediates = True

    if save_intermediates:
        def local_create(name):
            """create_persistent_map_name with hard-coded first argument"""
            basename = local_relief_output.split('@')[0]
            return create_persistent_map_name(basename=basename, name=name)
        create_map_name = local_create
    else:
        create_map_name = create_tmp_map_name

    smooth_elevation = create_map_name('smooth_elevation')
    subtracted_smooth_elevation = create_map_name('subtracted_smooth_elevation')
    vector_contours = create_map_name('vector_contours')
    raster_contours = create_map_name('raster_contours')
    raster_contours_with_values = create_map_name('raster_contours_with_values')
    purged_elevation = create_map_name('purged_elevation')

    if not save_intermediates:
        RREMOVE.append(smooth_elevation)
        RREMOVE.append(subtracted_smooth_elevation)
        VREMOVE.append(vector_contours)
        RREMOVE.append(raster_contours)
        RREMOVE.append(raster_contours_with_values)
        RREMOVE.append(purged_elevation)

    # check even for the temporary maps
    # (although, in ideal world, we should always fail if some of them exists)
    if not gcore.overwrite():
        check_map_name(smooth_elevation, gscript.gisenv()['MAPSET'], 'cell')
        check_map_name(subtracted_smooth_elevation, gscript.gisenv()['MAPSET'], 'cell')
        check_map_name(vector_contours, gscript.gisenv()['MAPSET'], 'vect')
        check_map_name(raster_contours, gscript.gisenv()['MAPSET'], 'cell')
        check_map_name(raster_contours_with_values, gscript.gisenv()['MAPSET'], 'cell')
        check_map_name(purged_elevation, gscript.gisenv()['MAPSET'], 'cell')

    # algorithm according to Hesse 2010 (LiDAR-derived Local Relief Models)
    # step 1 (point cloud to digital elevation model) omitted

    # step 2
    gscript.info(_("Smoothing using r.neighbors..."))
    gscript.run_command('r.neighbors', input=elevation_input,
                        output=smooth_elevation,
                        size=neighborhood_size,
                        overwrite=gcore.overwrite())

    # step 3
    gscript.info(_("Subtracting smoothed from original elevation..."))
    gscript.mapcalc('{c} = {a} - {b}'.format(c=subtracted_smooth_elevation,
                                             a=elevation_input,
                                             b=smooth_elevation,
                                             overwrite=gcore.overwrite()))

    # step 4
    gscript.info(_("Finding zero contours in elevation difference map..."))
    gscript.run_command('r.contour', input=subtracted_smooth_elevation,
                        output=vector_contours,
                        levels=[0],
                        overwrite=gcore.overwrite())

    # step 5
    gscript.info(_("Extracting z value from the elevation"
                   " for difference zero contours..."))
    gscript.run_command('v.to.rast', input=vector_contours,
                        output=raster_contours,
                        type='line', use='val', value=1,
                        overwrite=gcore.overwrite())
    gscript.mapcalc('{c} = {a} * {b}'.format(c=raster_contours_with_values,
                                             a=raster_contours,
                                             b=elevation_input,
                                             overwrite=gcore.overwrite()))

    gscript.info(_("Interpolating elevation between"
                   " difference zero contours..."))
    gscript.run_command('r.fillnulls', input=raster_contours_with_values,
                        output=purged_elevation,
                        method=fill_method,
                        overwrite=gcore.overwrite())

    # step 6
    gscript.info(_("Subtracting purged from original elevation..."))
    gscript.mapcalc('{c} = {a} - {b}'.format(c=local_relief_output,
                                             a=elevation_input,
                                             b=purged_elevation,
                                             overwrite=gcore.overwrite()))

    if save_intermediates:
        # same color table as input
        gscript.run_command('r.colors', map=smooth_elevation,
                            raster=elevation_input, quiet=True)
        gscript.run_command('r.colors', map=raster_contours_with_values,
                            raster=elevation_input, quiet=True)
        gscript.run_command('r.colors', map=purged_elevation,
                            raster=elevation_input, quiet=True)

        # has only one color
        gscript.run_command('r.colors', map=raster_contours,
                            color='grey', quiet=True)

        # same color table as output
        gscript.run_command('r.colors', map=subtracted_smooth_elevation,
                            color=color_table, quiet=True)

    gscript.run_command('r.colors', map=local_relief_output,
                        color=color_table, quiet=True)


if __name__ == "__main__":
    main()
