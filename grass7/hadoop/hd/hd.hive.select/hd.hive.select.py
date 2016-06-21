#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       hd.hive.execute
# AUTHOR(S):    Matej Krejci (matejkrejci@gmail.com)
#
# COPYRIGHT:    (C) 2016 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Execute HIVEsql command
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
#% options: hive_cli, hiveserver2
#%end
#%option
#% key: hql
#% type: string
#% required: yes
#% description: hive sql command
#%end
#%option
#% key: schema
#% type: string
#% required: no
#% description: hive db schema
#%end
#%G_OPT_F_OUTPUT
#% key: out
#% type: string
#% required: no
#% description: Name for output file (if omitted output to stdout)
#%end

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    conn = ConnectionManager()

    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()

    if not options['schema']:
        options['schema'] = 'default'

    out = hive.get_results(hql=options['hql'],
                           schema=options['schema'])

    if options['out']:
        with open(out, 'rw') as io:
            io.writelines(out)
            io.close()
    else:
        print out


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
