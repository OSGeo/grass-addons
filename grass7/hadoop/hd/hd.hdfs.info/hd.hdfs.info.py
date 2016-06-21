#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       hd.hdfs.info
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
#% description: Module for geting metadata of tables in hive
#% keyword: database
#% keyword: hdfs
#% keyword: hive
#%end

#%option
#% key: driver
#% type: string
#% required: yes
#% answer: hiveserver2
#% description: Type of database driver
#% options: webhdfs, hdfs
#%end
#%option
#% key: path
#% type: string
#% required: no
#% description: check path
#% guisection: Connection
#%end
#%flag
#% key: r
#% description: recursive
#%end

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    conn = ConnectionManager()
    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()

    if options['path']:

        for path in (hive.check_for_content(options['path'], flags['r'])):
            grass.message(path)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
