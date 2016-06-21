#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       hd.hdfs.in.fs
# AUTHOR(S):    Matej Krejci (matejkrejci@gmail.com
#
# COPYRIGHT:    (C) 2016 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Module for transfer file to HDFS
#% keyword: database
#% keyword: hdfs
#% keyword: hive
#%end
#%option
#% key: hdfs
#% type: string
#% answer: @grass_data_hdfs
#% required: yes
#% description: HDFS path or default grass dataset
#%end
#%option
#% key: driver
#% type: string
#% required: yes
#% options: hdfs,webhdfs
#% description: HDFS driver
#%end
#%option G_OPT_F_INPUT
#% key: local
#% guisection: file input
#%end


import os

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import GrassHdfs


def main():
    if options['hdfs'] == '@grass_data_hdfs':
        LOCATION_NAME = grass.gisenv()['LOCATION_NAME']
        MAPSET = grass.gisenv()['MAPSET']
        MAPSET_PATH = os.path.join('grass_data_hdfs', LOCATION_NAME, MAPSET, 'external')
        options['hdfs'] = MAPSET_PATH

    if options['local']:
        transf = GrassHdfs(options['driver'])
        transf.upload(options['local'], options['hdfs'])


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
