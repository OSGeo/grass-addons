#!/usr/bin/env python3
############################################################################
#
# MODULE:       i.sentinel.parallel.download
# AUTHOR(S):    Guido Riembauer
# PURPOSE:      Downloads Sentinel-2 images parallely using i.sentinel.download.
# COPYRIGHT: (C) 2020 by mundialis and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

#%module
#% description: Downloads Sentinel-2 images parallely using i.sentinel.download.
#% keyword: imagery
#% keyword: satellite
#% keyword: Sentinel
#% keyword: download
#% keyword: parallel
#%end

#%option G_OPT_F_INPUT
#% key: settings
#% label: Full path to settings file (user, password)
#%end

#%option
#% key: scene_name
#% required: no
#% multiple: yes
#% label: Names of the scenes to be downloaded, in the format: S2A_MSIL1C_20180822T155901_N0206_R097_T17SPV_20180822T212023.SAFE
#%end

#%option G_OPT_M_DIR
#% key: output
#% description: Name for output directory where to store downloaded Sentinel data
#% required: no
#% guisection: Output
#%end

#%option
#% key: clouds
#% type: integer
#% description: Maximum cloud cover percentage for Sentinel scene
#% required: no
#% guisection: Filter
#% answer: 20
#%end

#%option
#% key: producttype
#% type: string
#% description: Sentinel product type to filter
#% required: no
#% options: SLC,GRD,OCN,S2MSI1C,S2MSI2A,S2MSI2Ap
#% answer: S2MSI2A
#% guisection: Filter
#%end

#%option
#% key: start
#% type: string
#% description: Start date ('YYYY-MM-DD')
#% guisection: Filter
#%end

#%option
#% key: end
#% type: string
#% description: End date ('YYYY-MM-DD')
#% guisection: Filter
#%end

#%option
#% key: nprocs
#% type: integer
#% required: no
#% multiple: no
#% label: Number of parallel processes
#% description: Number of used CPUs
#% answer: 1
#%end

#%flag
#% key: s
#% description: Use scenename/s instead of start/end/producttype to download specific S2 data (specify in the scene_name field).
#%end

#%flag
#% key: f
#% description: Download each Sentinel-2 datasat into an individual folder within the output folder
#%end

import sys
import os
import multiprocessing as mp
import grass.script as grass
from grass.pygrass.modules import Module, ParallelModuleQueue
from datetime import datetime,timedelta

def scenename_split(scenename):
    '''
    When using the query option in i.sentinel.filename and defining
    specific filenames, the parameters Producttype, Start-Date, and End-Date
    have to be definied as well.This function extracts these parameters from a
    Sentinel-2 filename and returns the proper string to be passed to the query
    option.
    Args:
        scenename(string): Name of the scene in the format
                           S2A_MSIL1C_20180822T155901_N0206_R097_T17SPV_20180822T212023
    Returns:
        producttype(string): Sentinel-2 producttype in the required parameter
                             format for i.sentinel.download, e.g. S2MSI2A
        start_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date -1 day
        end_day(string): Date in the format YYYY-MM-DD, it is the acquisition
                           date +1 day
        query_string(string): string in the format "filename=..."

    '''
    ### get producttype
    name_split = scenename.split('_')
    type_string = name_split[1]
    level_string = type_string.split('L')[1]
    producttype = 'S2MSI' + level_string
    ### get dates
    date_string = name_split[2].split('T')[0]
    dt_obj = datetime.strptime(date_string,"%Y%m%d")
    start_day_dt = dt_obj - timedelta(days=1)
    end_day_dt = dt_obj + timedelta(days=1)
    start_day = start_day_dt.strftime('%Y-%m-%d')
    end_day = end_day_dt.strftime('%Y-%m-%d')
    ### get query string
    if not scenename.endswith('.SAFE'):
        scenename = scenename + '.SAFE'
    query_string = 'filename=%s' %(scenename)
    return producttype, start_day, end_day, query_string

def main():

    settings = options['settings']
    scene_names = options['scene_name'].split(',')
    output = options['output']
    nprocs = int(options['nprocs'])
    clouds = int(options['clouds'])
    producttype = options['producttype']
    start = options['start']
    end   = options['end']
    use_scenenames=flags['s']
    ind_folder=flags['f']

    ### check if we have the i.sentinel.download + i.sentinel.import addons
    if not grass.find_program('i.sentinel.download', '--help'):
        grass.fatal(_("The 'i.sentinel.download' module was not found, install it first:") +
                    "\n" +
                    "g.extension i.sentinel")

    ### Test if all required data are there
    if not os.path.isfile(settings):
        grass.fatal(_("Settings file <%s> not found" % (settings)))

    ### set some common environmental variables, like:
    os.environ.update(dict(GRASS_COMPRESS_NULLS='1',
                           GRASS_COMPRESSOR='ZSTD',
                           GRASS_MESSAGE_FORMAT='plain'))

    ### test nprocs Settings
    if nprocs > mp.cpu_count():
        grass.fatal("Using %d parallel processes but only %d CPUs available."
                    %(nprocs,mp.cpu_count()))

    ### sentinelsat allows only three parallel downloads
    elif nprocs > 2:
        grass.message("Maximum number of parallel processes for Downloading" +
                      " fixed to 2 due to sentinelsat API restrictions")
        nprocs = 2

    if use_scenenames:
        scenenames = scene_names
        ### check if the filename is valid
        ### TODO: refine check, it's currently a very lazy check
        if len(scenenames[0])<10:
            grass.fatal("No scene names indicated. Please provide scenenames in \
                        the format S2A_MSIL1C_20180822T155901_N0206_R097_T17SPV_20180822T212023.SAFE")
    else:
        ### get a list of scenenames to download
        i_sentinel_download_string = grass.parse_command(
            'i.sentinel.download',
            settings=settings,
            producttype=producttype,
            start=start,
            end=end,
            clouds=clouds,
            flags='l'
        )
        i_sentinel_keys = i_sentinel_download_string.keys()
        scenenames = [item.split(' ')[1] for item in i_sentinel_keys]

    ### parallelize download
    grass.message(_("Downloading Sentinel-2 data..."))

    ### adapt nprocs to number of scenes
    if len(scenenames)==1:
        nprocs=1

    queue_download = ParallelModuleQueue(nprocs=nprocs)

    for idx,scenename in enumerate(scenenames):
        producttype, start_date, end_date, query_string = scenename_split(scenename)
        ### output into separate folders, easier to import in a parallel way:
        if ind_folder:
            outpath = os.path.join(output, 'dl_s2_%s' % str(idx+1))
        else:
            outpath = output
        i_sentinel_download = Module(
            'i.sentinel.download',
            settings=settings,
            start=start_date,
            end=end_date,
            producttype=producttype,
            query=query_string,
            output=outpath,
            run_=False
        )
        queue_download.put(i_sentinel_download)
    queue_download.wait()

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
