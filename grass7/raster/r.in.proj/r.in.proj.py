#!/usr/bin/env python

############################################################################
#
# MODULE:       r.in.proj
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
#% description: Import raster data using GDAL library and reproject on the fly.
#% keyword: raster
#% keyword: import
#% keyword: projection
#%end
#%option G_OPT_F_INPUT
#% key: input_file
#% required: no
#% multiple: no
#% description: Name of GDAL dataset (file) to be imported
#% guisection: Input
#%end
#%option G_OPT_M_DIR
#% key: input_directory
#% required: no
#% multiple: no
#% description: Name of GDAL dataset (directory) to be imported
#% guisection: Input
#%end
#%option
#% key: band
#% type: integer
#% required: no
#% multiple: yes
#% description: Input band(s) to select (default is all bands)
#% guisection: Input
#%end
#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% options: 0-2047
#% label: Maximum memory to be used (in MB)
#% description: Cache size for raster rows
#% answer: 300
#%end
#%option G_OPT_R_OUTPUT
#% required: no
#% multiple: no
#% key_desc: name
#% description: Name for output raster map (default: same as 'input')
#% guisection: Output
#%end
#%option
#% key: resample
#% type: string
#% required: yes
#% multiple: no
#% options: nearest,bilinear,bicubic,lanczos,bilinear_f,bicubic_f,lanczos_f
#% description: Resampling method to use for reprojection
#% descriptions: nearest;nearest neighbor;bilinear;bilinear interpolation;bicubic;bicubic interpolation;lanczos;lanczos filter;bilinear_f;bilinear interpolation with fallback;bicubic_f;bicubic interpolation with fallback;lanczos_f;lanczos filter with fallback
#% guisection: Output
#%end
#%option
#% key: extents
#% type: string
#% required: yes
#% multiple: no
#% options: region,input
#% description: Ouput raster map extents
#% descriptions: region;extents of current region;input;extents of input map
#% guisection: Output
#%end
#%option
#% key: resolution
#% type: double
#% required: no
#% multiple: no
#% description: Resolution of output raster map (default: current region)
#% guisection: Output
#%end
#%flag
#% key: i
#% description: Import and reproject (default: estimate resolution only)
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
    method = options['resample']
    memory = options['memory']
    do_import = flags['i']

    bands = None
    if options['band']:
        bands = options['band']
    tgtres = None
    if options['resolution']:
        tgtres = options['resolution']

    # initialize global vars
    tmploc = None
    srcgisrc = None
    gisdbase = None

    # make sure current location is not xy
    if grass.parse_command('g.proj', flags = 'g')['name'] == 'xy_location_unprojected':
        grass.fatal(_("The current location is a XY location (unprojected)"))
        sys.exit(1)
        

    GDALdatasource = None
    if options['input_file']:
        GDALdatasource = options['input_file']
    
    if not GDALdatasource:
        GDALdatasource = options['input_directory']

    if not GDALdatasource:
        grass.fatal(_("Either option 'input_file' or option 'input_directory' must be given"))

    # TODO: check if input is a dataset recognized by GDAL */

    # compare output of g.proj -j and g.proj -j georef=GDALdatasource
    insrs = grass.read_command('g.proj', flags = 'j', georef = GDALdatasource, quiet = True)
    tgtsrs = grass.read_command('g.proj', flags = 'j', quiet = True)

    if insrs == tgtsrs:
        # try r.in.gdal directly
        grass.message(_("Trying direct import of <%s>...") % GDALdatasource) 
        ps = grass.start_command('r.in.gdal', input = GDALdatasource,
                                band = bands, output = output,
                                memory = memory, flags = 'k')
        returncode = ps.wait()
        
        # if it succeeds, return
        if returncode == 0:
            grass.message(_("Input <%s> successfully imported without reprojection") % GDALdatasource) 
            sys.exit(0)

    grassenv = grass.gisenv()
    tgtloc = grassenv['LOCATION_NAME']
    tgtmapset = grassenv['MAPSET']
    gisdbase = grassenv['GISDBASE']
    tgtgisrc = os.environ['GISRC']
    srcgisrc = grass.tempfile()
    
    tmploc = 'temp_import_location_' + str(os.getpid())

    # r.in.gdal with location=temp location
    grass.message(_("Importing <%s> ...") % GDALdatasource) 
    ps = grass.start_command('r.in.gdal', input = GDALdatasource,
                             band = bands, output = output,
                             memory = memory, flags = 'k',
                             location = tmploc)
    returncode = ps.wait()
    
    # if it fails, return
    if returncode != 0:
        grass.fatal(_("Unable to import GDAL dataset <%s>") % GDALdatasource)
        sys.exit(0)

    f = open(srcgisrc, 'w')
    f.write('DEBUG: 0\n')
    f.write('MAPSET: PERMANENT\n')
    f.write('GISDBASE: %s\n' % gisdbase)
    f.write('LOCATION_NAME: %s\n' % tmploc);
    f.write('GUI: text\n')
    f.close()
    
    # switch to temp location
    os.environ['GISRC'] = str(srcgisrc)
    outfiles = grass.list_grouped('rast')['PERMANENT']

    # make sure input is not xy
    if grass.parse_command('g.proj', flags = 'g')['name'] == 'xy_location_unprojected':
        grass.fatal(_("Coordinate reference system not available for input <%s>") % GDALdatasource)
        sys.exit(1)

    # is output a group?
    group = False
    path = os.path.join(gisdbase, tmploc, 'group', output)
    if os.path.exists(path):
        group = True
        path = os.path.join(gisdbase, tmploc, 'group', output, 'POINTS')
        if os.path.exists(path):
            grass.fatal(_("Input contains GCPs, rectification is required"))
            sys.exit(1)

    # switch to target location
    os.environ['GISRC'] = str(tgtgisrc)

    if tgtres is not None and float(tgtres) <= 0:
        tgtres = None

    region = grass.region()
    
    if tgtres is not None:
        outres = tgtres
    else:
        outres = (region['ewres'] + region['nsres']) / 2.0

    rflags = None
    if options['extents'] == 'input':
        rflags = 'n'

    for outfile in outfiles:

        n = region['n']
        s = region['s']
        e = region['e']
        w = region['w']

        if options['extents'] == 'input':
            # r.proj -g
            try:
                tgtextents = grass.read_command('r.proj', location = tmploc,
                                                mapset = 'PERMANENT',
                                                input = outfile, flags = 'g',
                                                memory = memory)
            except:
                grass.fatal(_("Unable to get reprojected map extents"))
                sys.exit(1)
            
            srcregion = grass.parse_key_val(tgtextents, vsep = ' ')
            n = srcregion['n']
            s = srcregion['s']
            e = srcregion['e']
            w = srcregion['w']
            
        grass.use_temp_region()

        grass.run_command('g.region', n = n, s = s, e = e, w = w)
        
        # v.in.region in tgt
        vreg = 'vreg_' + str(os.getpid())
        grass.run_command('v.in.region', output = vreg, quiet = True)
        
        grass.del_temp_region()

        # reproject to src
        # switch to temp location
        os.environ['GISRC'] = str(srcgisrc)
        ps = grass.start_command('v.proj', input = vreg, output = vreg, 
                          location = tgtloc, mapset = tgtmapset, quiet = True)
        returncode = ps.wait()
        if returncode != 0:
            grass.fatal(_("Unable to to reproject to source location"))
            sys.exit(1)
        
        # set region from region vector
        grass.run_command('g.region', raster = outfile)
        grass.run_command('g.region', vector = vreg)
        # align to fist band
        grass.run_command('g.region', align = outfile)
        # get number of cells
        cells = grass.region()['cells']
        
        # resolution = sqrt((n - s) * (e - w) / cells)
        estres = math.sqrt((n - s) * (e - w) / cells)

        os.environ['GISRC'] = str(tgtgisrc)
        grass.run_command('g.remove', type = 'vector', name = vreg,
                          flags = 'f', quiet = True)
        
        grass.message(_("Estimated target resolution for input band <%s>: %g") % (outfile, estres))
        grass.message(_("Specified target resolution: %g") % outres)

        if do_import:
            # r.proj
            grass.message(_("Reprojecting <%s>...") % outfile)
            ps = grass.start_command('r.proj', location = tmploc,
                                     mapset = 'PERMANENT', input = outfile,
                                     method = method, resolution = tgtres,
                                     memory = memory, flags = rflags, quiet = True)
            returncode = ps.wait()
            if returncode != 0:
                grass.fatal(_("Unable to to reproject raster <%s>") % outfile)
                sys.exit(1)
                
            if grass.raster_info(outfile)['min'] is None:
                grass.fatal(_("The reprojected raster <%s> is empty") % outfile)
                sys.exit(1)


    if do_import:
        if group:
            grass.run_command('i.group', group = output, input = ','.join(outfiles)) 


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
