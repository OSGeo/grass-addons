#!/usr/bin/env python
#
############################################################################
#
# MODULE:      i.sentinel.import
# AUTHOR(S):   Martin Landa
# PURPOSE:     Imports Sentinel data downloaded from Copernicus Open Access Hub
#              using i.sentinel.download.
# COPYRIGHT:   (C) 2018 by Martin Landa, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%Module
#% description: Imports Sentinel data downloaded from Copernicus Open Access Hub using i.sentinel.download.
#% keyword: imagery
#% keyword: sentinel
#% keyword: import
#%end
#%option G_OPT_M_DIR
#% key: input
#% description: Name for input directory where downloaded Sentinel data lives
#% required: yes
#%end
#%option
#% key: pattern
#% description: File name pattern to import
#%end
#%flag
#% key: r
#% description: Reproject raster data using r.import if needed
#%end
#%flag
#% key: l
#% description: Link raster data instead of importing
#%end
#%flag
#% key: c
#% description: Import cloud masks as vector maps
#%end
#%flag
#% key: p
#% description: Print raster data to be imported and exit
#%end
#%rules
#% exclusive: -l,-r,-p
#%end
import os
import sys
import re
import glob
import shutil
from zipfile import ZipFile

import grass.script as gs
from grass.exceptions import CalledModuleError

class SentinelImporter(object):
    def __init__(self, input_dir):
        # list of directories to cleanup
        self._dir_list = []

        # check if input dir exists
        self.input_dir = input_dir
        if not os.path.exists(input_dir):
            gs.fatal(_('{} not exists').format(input_dir))

    def __del__(self):
        for dirname in self._dir_list:
            dirpath = os.path.join(self.input_dir, dirname)
            gs.debug('Removing <{}>'.format(dirpath))
            shutil.rmtree(dirpath)
            
    def filter(self, pattern=None):
        if pattern:
            filter_p = '.*' + options['pattern'] + '.*.jp2$'
        else:
            filter_p = r'.*_B.*.jp2$'

        self.files = self._filter(filter_p)

    @staticmethod
    def _read_zip_file(filepath):
        # scan zip file, return first member (root directory)
        with ZipFile(filepath) as fd:
            file_list = fd.namelist()

        return file_list

    def _unzip(self):
        # extract all zip files from input directory
        for filepath in glob.glob(os.path.join(self.input_dir, '*.zip')):
            gs.verbose('Reading <{}>...'.format(filepath))
            self._dir_list.append(self._read_zip_file(filepath)[0])

            with ZipFile(filepath) as fd:
                fd.extractall(path=self.input_dir)

    def _filter(self, filter_p):
        # unzip archives before filtering
        self._unzip()

        pattern = re.compile(filter_p)
        files = []
        for rec in os.walk(self.input_dir):
            if not rec[-1]:
                continue

            match = filter(pattern.match, rec[-1])
            if match is None:
                continue

            for f in match:
                files.append(os.path.join(rec[0], f))

        return files

    def import_products(self, reproject=False, link=False):
        args = {}
        if link:
            module = 'r.external'
        else:
            if reproject:
                module = 'r.import'
                args['resample'] = 'bilinear'
                args['resolution'] = 'value'
            else:
                module = 'r.in.gdal'

        for f in self.files:
            if link or (not link and not reproject):
                if not self._check_projection(f):
                    gs.fatal(_('Projection of dataset does not appear to match current location. '
                               'Force reprojecting dataset by -r flag.'))

            self._import_file(f, module, args)

    def _check_projection(self, filename):
        try:
            with open(os.devnull) as null:
                gs.run_command('r.in.gdal', flags='j',
                               input=filename, quiet=True, stderr=null)
        except CalledModuleError as e:
            return False

        return True

    def _raster_resolution(self, filename):
        try:
            from osgeo import gdal
        except ImportError as e:
            gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
        dsn = gdal.Open(filename)
        trans = dsn.GetGeoTransform()
        
        ret = int(trans[1])
        dsn = None

        return ret
    
    def _raster_epsg(self, filename):
        try:
            from osgeo import gdal, osr
        except ImportError as e:
            gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
        dsn = gdal.Open(filename)

        srs = osr.SpatialReference()
        srs.ImportFromWkt(dsn.GetProjectionRef())
    
        ret = srs.GetAuthorityCode(None)
        dsn = None

        return ret
        
    def _import_file(self, filename, module, args):
        mapname = os.path.splitext(os.path.basename(filename))[0]
        gs.message(_('Processing <{}>...').format(mapname))
        if module == 'r.import':
            args['resolution_value'] = self._raster_resolution(filename)
        try:
            gs.run_command(module, input=filename, output=mapname, **args)
        except CalledModuleError as e:
            pass # error already printed

    def import_cloud_masks(self):
        files = self._filter("MSK_CLOUDS_B00.gml")

        for f in files:
            safe_dir = os.path.dirname(f).split(os.path.sep)[-4]
            items = safe_dir.split('_')
            map_name = '_'.join([items[5],items[2], 'MSK', 'CLOUDS'])
            try:
                gs.run_command('v.import', input=f,
                               flags='o', # same SRS as data
                               output=map_name,
                               quiet=True
                )
            except CalledModuleError as e:
                pass # error already printed

    def print_products(self):
        for f in self.files:
            sys.stdout.write('{} {} (EPSG: {}){}'.format(
                f,
                '1' if self._check_projection(f) else '0',
                self._raster_epsg(f),
                os.linesep
            ))

def main():
    importer = SentinelImporter(options['input'])

    importer.filter(options['pattern'])

    if flags['p']:
        importer.print_products()
        return 0
    
    importer.import_products(flags['r'], flags['l'])

    if flags['c']:
        importer.import_cloud_masks()

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
