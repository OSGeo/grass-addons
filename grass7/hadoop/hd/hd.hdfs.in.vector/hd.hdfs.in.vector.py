#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       hd.hdfs.in.vector
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
#% description: Module for export vector feature to hdfs(JSON)
#% keyword: database
#% keyword: hdfs
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
#% options: webhdfs,hdfs
#% description: HDFS driver
#%end
#%option G_OPT_V_MAP
#% key: map
#% required: yes
#% label: Name of vector map to export to hdfs
#%end
#%option G_OPT_V_TYPE
#% key: type
#% required: yes
#%end
#%option G_OPT_V_FIELD
#% key: layer
#% required: yes
#%end



import grass.script as grass

from hdfsgrass.hdfs_grass_lib import JSONBuilder, GrassHdfs


def main():
    transf = GrassHdfs(options['driver'])
    if options['hdfs'] == '@grass_data_hdfs':
        options['hdfs'] = transf.get_path_grass_dataset()

    grass.message(options['hdfs'])
    grass_map = {"map": options['map'],
                 "layer": options['layer'],
                 "type": options['type'],
                 }

    json = JSONBuilder(grass_map)
    json = json.get_JSON()

    grass.message('upload %s' % json)

    transf.upload(json, options['hdfs'])


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
