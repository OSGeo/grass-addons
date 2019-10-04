#!/usr/bin/env python
#
############################################################################
#
# MODULE:      i.sentinel.import
# AUTHOR(S):   Martin Landa
# PURPOSE:     Imports Sentinel data downloaded from Copernicus Open Access Hub
#              using i.sentinel.download.
# COPYRIGHT:   (C) 2018-2019 by Martin Landa, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%Module
#% description: Imports Sentinel satellite data downloaded from Copernicus Open Access Hub using i.sentinel.download.
#% keyword: imagery
#% keyword: satellite
#% keyword: Sentinel
#% keyword: import
#%end
#%option G_OPT_M_DIR
#% key: input
#% description: Name of input directory with downloaded Sentinel data
#% required: yes
#%end
#%option
#% key: pattern
#% description: File name pattern to import
#% guisection: Filter
#%end
#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% label: Maximum memory to be used (in MB)
#% description: Cache size for raster rows
#% answer: 300
#%end
#%option G_OPT_F_OUTPUT
#% key: register_output
#% description: Name for output file to use with t.register
#% required: no
#%end
#%flag
#% key: r
#% description: Reproject raster data using r.import if needed
#% guisection: Settings
#%end
#%flag
#% key: l
#% description: Link raster data instead of importing
#% guisection: Settings
#%end
#%flag
#% key: c
#% description: Import cloud masks as vector maps
#% guisection: Settings
#%end
#%flag
#% key: p
#% description: Print raster data to be imported and exit
#% guisection: Print
#%end
#%rules
#% exclusive: -l,-r,-p
#%end
import os
import sys
import re
import glob
import shutil
import io
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
            gs.fatal(_('Input directory <{}> not exists').format(input_dir))

    def __del__(self):
        if flags['l']:
            # unzipped files are required when linking
            return

        # otherwise unzipped directory can be removed (?)
        for dirname in self._dir_list:
            dirpath = os.path.join(self.input_dir, dirname)
            gs.debug('Removing <{}>'.format(dirpath))
            try:
                shutil.rmtree(dirpath)
            except OSError:
                pass
            
    def filter(self, pattern=None):
        if pattern:
            filter_p = '.*' + options['pattern'] + '.*.jp2$'
        else:
            filter_p = r'.*_B.*.jp2$'

        gs.debug('Filter: {}'.format(filter_p), 1)
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
            args['memory'] = options['memory']
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

    @staticmethod
    def _map_name(filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def _import_file(self, filename, module, args):
        mapname = self._map_name(filename)
        gs.message(_('Processing <{}>...').format(mapname))
        if module == 'r.import':
            args['resolution_value'] = self._raster_resolution(filename)
        try:
            gs.run_command(module, input=filename, output=mapname, **args)
            gs.raster_history(mapname)
        except CalledModuleError as e:
            pass # error already printed

    def import_cloud_masks(self):
        from osgeo import ogr

        files = self._filter("MSK_CLOUDS_B00.gml")

        for f in files:
            safe_dir = os.path.dirname(f).split(os.path.sep)[-4]
            items = safe_dir.split('_')
            map_name = '_'.join([items[5],items[2], 'MSK', 'CLOUDS'])
            # check if any OGR layer
            dsn = ogr.Open(f)
            layer_count = dsn.GetLayerCount()
            dsn.Destroy()
            if layer_count < 1:
                gs.info('No clouds layer found in <{}>. Import skipped'.format(f))
                continue
            try:
                gs.run_command('v.import', input=f,
                               flags='o', # same SRS as data
                               output=map_name,
                               quiet=True)
                gs.vector_history(map_name)
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

    @staticmethod
    def _read_timestamp_from_mtd_file(mtd_file):
        try:
            from xml.etree import ElementTree
            from datetime import datetime
        except ImportError as e:
            gs.fatal(_("Unable to parse metadata file. {}").format(e))

        timestamp = None
        with io.open(mtd_file, encoding='utf-8') as fd:
            root = ElementTree.fromstring(fd.read())
            nsPrefix = root.tag[:root.tag.index('}')+1]
            nsDict = {'n1':nsPrefix[1:-1]}
            node = root.find('n1:General_Info', nsDict)
            if node is not None:
                try:
                    # check S2
                    tile_id = [subnode.text for subnode in node.getchildren() if subnode.tag.startswith('TILE_ID')][0]
                    if not tile_id.startswith('S2'):
                        gs.fatal(_("Register file can be created only for Sentinel-2 data."))

                    # get timestamp
                    ts_str = node.find('SENSING_TIME', nsDict).text
                    timestamp = datetime.strptime(
                        ts_str, "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                except (AttributeError, IndexError):
                    # error is reported below
                    pass

        if not timestamp:
            gs.error(_("Unable to determine timestamp from <{}>").format(mtd_file))

        return timestamp

    @staticmethod
    def _ip_from_path(path):
        return os.path.basename(path[:path.find('.SAFE')])

    def create_register_file(self, filename):
        gs.message(_("Creating register file <{}>...").format(filename))
        ip_timestamp = {}
        for mtd_file in self._filter("MTD_TL.xml"):
            ip = self._ip_from_path(mtd_file)
            ip_timestamp[ip] = self._read_timestamp_from_mtd_file(mtd_file)

        if not ip_timestamp:
            gs.warning(_("Unable to determine timestamps. No metadata file found"))
        has_band_ref = gs.version()['version'] == '7.9.dev'
        sep = '|'
        with open(filename, 'w') as fd:
            for img_file in self.files:
                map_name = self._map_name(img_file)
                ip = self._ip_from_path(img_file)
                timestamp = ip_timestamp[ip]
                if timestamp:
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
                else:
                    timestamp_str = ''
                fd.write('{img}{sep}{ts}'.format(
                    img=map_name,
                    sep=sep,
                    ts=timestamp_str
                ))
                if has_band_ref:
                    try:
                        band_ref = re.match(
                            r'.*_B([0-18][0-9A]).*', map_name
                        ).groups()[0].lstrip('0')
                    except AttributeError:
                        gs.warning(
                            _("Unable to determine band reference for <{}>").format(
                                map_name))
                        continue
                    fd.write('{sep}{br}'.format(
                        sep=sep,
                        br='S2_{}'.format(band_ref)
                    ))
                fd.write(os.linesep)
def main():
    importer = SentinelImporter(options['input'])

    importer.filter(options['pattern'])

    if flags['p']:
        if options['register_output']:
            gs.warning(_("Register output file name is not created "
                         "when -{} flag given").format('p'))
        importer.print_products()
        return 0
    
    importer.import_products(flags['r'], flags['l'])

    if flags['c']:
        # import cloud mask if requested
        importer.import_cloud_masks()

    if options['register_output']:
        # create t.register file if requested
        importer.create_register_file(
            options['register_output']
        )

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
