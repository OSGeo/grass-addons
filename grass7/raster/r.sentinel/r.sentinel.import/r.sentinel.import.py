#!/usr/bin/env python2
#
############################################################################
#
# MODULE:      r.sentinel.import
# AUTHOR(S):   Martin Landa
# PURPOSE:     Imports Sentinel data downloaded from Copernicus Open Access Hub
#              using r.sentinel.download.
# COPYRIGHT:   (C) 2018 by Martin Landa, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%Module
#% description: Imports Sentinel data downloaded from Copernicus Open Access Hub using r.sentinel.download.
#% keyword: raster
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
#% key: l
#% description: Link raster data instead of importing
#%end
#%flag
#% key: c
#% description: Import cloud masks as vector maps
#%end

import os
import sys
import re

import grass.script as gs
from grass.exceptions import CalledModuleError

class SentinelImporter(object):
    def __init__(self, input_dir):
        if not os.path.exists(input_dir):
            gs.fatal('{} not exists'.format(input_dir))
        self.input_dir = input_dir

    def filter(self, pattern=None):
        if pattern:
            filter_p = '.*' + options['pattern'] + '.jp2$'
        else:
            filter_p = r'.*_B.*.jp2$'

        self.files = self._filter(filter_p)

    def _filter(self, filter_p):
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

    def import_products(self, link=False):
        for f in self.files:
            self._import_file(f, link)

    def _import_file(self, filename, link=False):
        module = 'r.external' if link else 'r.import'
        mapname = os.path.splitext(os.path.basename(filename))[0]
        if link:
            gs.message('Linking <{}>...'.format(mapname))
        else:
            gs.message('Importing <{}>...'.format(mapname))
        try:
            gs.run_command(module, input=filename, output=mapname)
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

def main():
    importer = SentinelImporter(options['input'])

    importer.filter(options['pattern'])

    importer.import_products(flags['l'])

    if flags['c']:
        importer.import_cloud_masks()

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
