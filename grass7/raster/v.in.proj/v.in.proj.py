#!/usr/bin/env python

############################################################################
#
# MODULE:       v.in.proj
#
# AUTHOR(S):    Markus Metz
#
# PURPOSE:      Import and reproject on the fly
#
# COPYRIGHT:    (C) 2015 GRASS development team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Import vector data using OGR library and reproject on the fly.
#% keyword: vector
#% keyword: import
#% keyword: projection
#%end
#%option G_OPT_F_INPUT
#% key: input_file
#% required: no
#% multiple: no
#% description: Name of OGR datasource (file) to be imported
#% guisection: Input
#%end
#%option G_OPT_M_DIR
#% key: input_directory
#% required: no
#% multiple: no
#% description: Name of OGR datasource (directory) to be imported
#% guisection: Input
#%end
#%option
#% key: layer
#% type: string
#% required: no
#% multiple: yes
#% description: OGR layer name. If not given, all available layers are imported
#% guisection: Input
#%end
#%option G_OPT_V_OUTPUT
#% required: yes
#% multiple: no
#% key_desc: name
#% description: Name for output vector map
#% guisection: Output
#%end
#%option
#% key: extents
#% type: string
#% required: yes
#% multiple: no
#% options: region,input
#% description: Ouput vector map extents
#% descriptions: region;extents of current region;input;extents of input map
#% guisection: Output
#%end


import sys
import os
import shutil
import atexit
import math

import grass.script as grass

    
def cleanup():
    # remove temp location
    if tmploc:
        path = os.path.join(gisdbase, tmploc)
        grass.try_rmdir(path)
    if srcgisrc:
        grass.try_remove(srcgisrc)

def main():
    global tmploc, srcgisrc, gisdbase

    output = options['output']

    layers = None
    if options['layer']:
        layers = options['layer']

    # initialize global vars
    tmploc = None
    srcgisrc = None
    gisdbase = None

    # make sure current location is not xy
    if grass.parse_command('g.proj', flags = 'g')['name'] == 'xy_location_unprojected':
        grass.fatal(_("The current location is a XY location (unprojected)"))
        sys.exit(1)
        

    OGRdatasource = None
    if options['input_file']:
        OGRdatasource = options['input_file']
    
    if not OGRdatasource:
        OGRdatasource = options['input_directory']

    if not OGRdatasource:
        grass.fatal(_("Either option 'input_file' or option 'input_directory' must be given"))

    # TODO: check if input is a dataset recognized by OGR */

    # try v.in.ogr directly
    vflags = None
    if options['extents'] == 'region':
        vflags = 'r'
    grass.message(_("Trying direct import of <%s>...") % OGRdatasource) 
    ps = grass.start_command('v.in.ogr', input = OGRdatasource,
                            layer = layers, output = output, flags = vflags)
    returncode = ps.wait()
    
    # if it succeeds, return
    if returncode == 0:
        grass.message(_("Input <%s> successfully imported without reprojection") % OGRdatasource) 
        sys.exit(0)

    grassenv = grass.gisenv()
    tgtloc = grassenv['LOCATION_NAME']
    tgtmapset = grassenv['MAPSET']
    gisdbase = grassenv['GISDBASE']
    tgtgisrc = os.environ['GISRC']
    srcgisrc = grass.tempfile()

    tmploc = 'temp_import_location_' + str(os.getpid())

    f = open(srcgisrc, 'w')
    f.write('DEBUG: 0\n')
    f.write('MAPSET: PERMANENT\n')
    f.write('GISDBASE: %s\n' % gisdbase)
    f.write('LOCATION_NAME: %s\n' % tmploc);
    f.write('GUI: text\n')
    f.close()

    grass.message(_("Importing <%s> ...") % OGRdatasource)
    if options['extents'] == 'input':
    
        # v.in.ogr with location=temp location
        ps = grass.start_command('v.in.ogr', input = OGRdatasource,
                                 layer = layers, output = output,
                                 location = tmploc, verbose = True)
        returncode = ps.wait()
        
        # if it fails, return
        if returncode != 0:
            grass.fatal(_("Unable to import OGR datasource <%s>") % OGRdatasource)
            sys.exit(1)

        # switch to temp location
        os.environ['GISRC'] = str(srcgisrc)

        # make sure input is not xy
        if grass.parse_command('g.proj', flags = 'g')['name'] == 'xy_location_unprojected':
            grass.fatal(_("Coordinate reference system not available for input <%s>") % OGRdatasource)
            sys.exit(1)

        # switch to target location
        os.environ['GISRC'] = str(tgtgisrc)

        # v.proj
        grass.message(_("Reprojecting <%s>...") % output)
        ps = grass.start_command('v.proj', location = tmploc,
                                 mapset = 'PERMANENT', input = output,
                                 quiet = True)
        returncode = ps.wait()
        if returncode != 0:
            grass.fatal(_("Unable to to reproject vector <%s>") % output)
            sys.exit(1)

        sys.exit(0)


    # options['extents'] == 'region'

    # create location
    ps = grass.start_command('v.in.ogr', input = OGRdatasource,
                             layer = layers, output = output,
                             location = tmploc, flags = 'i', quiet = True)
    returncode = ps.wait()
    
    # if it fails, return
    if returncode != 0:
        grass.fatal(_("Unable to create location from OGR datasource <%s>") % OGRdatasource)
        sys.exit(1)

    # switch to temp location
    os.environ['GISRC'] = str(srcgisrc)

    # make sure input is not xy
    if grass.parse_command('g.proj', flags = 'g')['name'] == 'xy_location_unprojected':
        grass.fatal(_("Coordinate reference system not available for input <%s>") % OGRdatasource)
        sys.exit(1)

    # switch to target location
    os.environ['GISRC'] = str(tgtgisrc)

    # v.in.region in tgt
    vreg = 'vreg_' + str(os.getpid())
    grass.run_command('v.in.region', output = vreg, quiet = True)

    # reproject to src
    # switch to temp location
    os.environ['GISRC'] = str(srcgisrc)
    ps = grass.start_command('v.proj', input = vreg, output = vreg, 
                      location = tgtloc, mapset = tgtmapset, quiet = True)

    returncode = ps.wait()

    if returncode != 0:
        grass.fatal(_("Unable to reproject to source location"))
        sys.exit(1)
    
    # set region from region vector
    grass.run_command('g.region', res = '1')
    grass.run_command('g.region', vector = vreg)

    grass.message(_("Importing <%s> ...") % OGRdatasource)
    ps = grass.start_command('v.in.ogr', input = OGRdatasource,
                             layer = layers, output = output,
                             flags = 'r', verbose = True)

    returncode = ps.wait()
    
    # if it fails, return
    if returncode != 0:
        grass.fatal(_("Unable to import OGR datasource <%s>") % OGRdatasource)
        sys.exit(1)

    # switch to target location
    os.environ['GISRC'] = str(tgtgisrc)

    grass.run_command('g.remove', type = 'vector', name = vreg,
                      flags = 'f', quiet = True)

    # v.proj
    grass.message(_("Reprojecting <%s>...") % output)
    ps = grass.start_command('v.proj', location = tmploc,
                             mapset = 'PERMANENT', input = output,
                             quiet = True)
    returncode = ps.wait()
    if returncode != 0:
        grass.fatal(_("Unable to to reproject vector <%s>") % output)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
