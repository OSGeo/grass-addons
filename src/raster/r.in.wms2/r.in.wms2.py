#!/usr/bin/env python
"""
MODULE:    r.in.wms2

AUTHOR(S): Stepan Turek <stepan.turek AT seznam.cz>

PURPOSE:   Downloads and imports data from WMS server.

COPYRIGHT: (C) 2012 Stepan Turek, and by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

#%module
#% description: Downloads and imports data from WMS servers.
#% keywords: raster
#% keywords: import
#% keywords: wms
#%end
#%option
#% key: url
#% type: string
#% label: URL of the WMS server
#% description: Typically starts with "http://" and ends in a "?". Include both.
#% required: yes
#%end
#%option
#% key: output
#% type: string
#% description: Name for output raster map
#% gisprompt: new,cell,raster
#% required: yes
#% key_desc: name
#%end
#%option
#% key: layers
#% type: string
#% description: Layer(s) to request from the map server
#% multiple: yes
#% required: yes
#%end
#%option
#% key: styles
#% type: string
#% description: Layer style(s) to request from the map server
#% multiple: yes
#% guisection: Map style
#%end
#%option
#% key: format
#% type: string
#% description: Image format requested from the server
#% options: geotiff,tiff,jpeg,gif,png
#% answer: geotiff
#% guisection: Request
#%end
#%option
#% key: srs
#% type: integer
#% description: EPSG code of requested source projection
#% answer: 4326
#% guisection: Request
#%end
#%option
#% key: driver
#% type: string
#% description: Driver used to communication with server
#% options: WMS_GDAL,WMS_GRASS,WMTS_GRASS,OnEarth_GRASS
#% answer: WMS_GRASS
#% guisection: Connection
#%end
#%option
#% key: wms_version
#% type: string
#% description: WMS standard version
#% options: 1.1.1,1.3.0
#% answer: 1.1.1
#% guisection: Request
#%end
#%option
#% key: maxcols
#% type: integer
#% description: Maximum columns to request at a time
#% answer: 512
#% guisection: Request
#%end
#%option
#% key: maxrows
#% type: integer
#% description: Maximum rows to request at a time
#% answer: 512
#% guisection: Request
#%end
#%option
#% key: urlparams
#% type: string
#% description: Additional query parameters to pass to the server
#% guisection: Connection
#%end
#%option
#% key: username
#% type: string
#% description: Username for server connection
#% guisection: Connection
#%end
#%option
#% key: password
#% type: string
#% description: Password for server connection
#% guisection: Connection
#%end
#%option
#% key: method
#% type: string
#% description: Interpolation method to use in reprojection
#% options: nearest,bilinear,cubic,cubicspline
#% answer: nearest
#%end
#%option
#% key: region
#% type: string
#% description: Request data for this named region instead of the current region bounds
#% guisection: Request
#%end
#%option
#% key: bgcolor
#% type: string
#% description: Background color
#% guisection: Map style
#%end
#%option
#% key: capfile
#% type: string
#% key_desc: name
#% required: no
#% gisprompt: old_file,file,xml
#% description: Capabilities file to parse (input)
#%end
#%option
#% key: capfile_output
#% required: no
#% gisprompt: new_file,file,file
#% description: File in which the server capabilities will be saved ('c' flag)
#% type: string
#% key_desc: name
#%end
#%flag
#% key: c
#% description: Get the server capabilities then exit
#% guisection: Request
##% suppress_required: yes
#%end
#%flag
#% key: s
#% description: Skip requests for fully transparent data
#% guisection: Map style
#%end


import os
import sys
import grass.script as grass

# add r.in.wms2.py support files to the PYTHONPATH:
addon_module_path = os.path.join(os.path.dirname(sys.path[0]), 'etc', 'r.in.wms2')
system_module_path = os.path.join(os.getenv('GISBASE'), 'etc', 'r.in.wms2')
if os.path.isdir(addon_module_path) and addon_module_path not in sys.path:
    sys.path.append(addon_module_path)
elif os.path.isdir(system_module_path) and system_module_path not in sys.path:
    sys.path.append(system_module_path)


def GetRegionParams(opt_region):

    # set region
    if opt_region:
        if not grass.find_file(name = opt_region, element = 'windows', mapset = '.' )['name']:
            grass.fatal(_("Region <%s> not found") % opt_region)

    if opt_region:
        s = grass.read_command('g.region',
                                quiet = True,
                                flags = 'ug',
                                region = opt_region)
        region_params = grass.parse_key_val(s, val_type = float)
    else:
        region_params = grass.region()

    return region_params


def main():

    if 'GRASS' in options['driver']:
        grass.debug("Using GRASS driver")
        from wms_drv import WMSDrv
        wms = WMSDrv()
    elif 'GDAL' in options['driver']:
        grass.debug("Using GDAL WMS driver")
        from wms_gdal_drv import WMSGdalDrv
        wms = WMSGdalDrv()

    if flags['c']:
        wms.GetCapabilities(options)
    else:
        from wms_base import GRASSImporter
        options['region'] = GetRegionParams(options['region'])
        importer = GRASSImporter(options['output'])
        fetched_map = wms.GetMap(options, flags)
        importer.ImportMapIntoGRASS(fetched_map)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
