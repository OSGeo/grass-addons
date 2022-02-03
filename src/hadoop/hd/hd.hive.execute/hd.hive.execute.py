#!/usr/bin/env python

############################################################################
#
# MODULE:       db.hive.execute
# AUTHOR(S):    Matej Krejci (matejkrejci@gmail.com
#
# COPYRIGHT:    (C) 2016 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Execute HIVEsql command
# % keyword: database
# % keyword: hdfs
# % keyword: hive
# %end

# %option
# % key: driver
# % type: string
# % required: yes
# % answer: hiveserver2
# % description: Type of database driver
# % options: hive_cli, hiveserver2
# %end
# %option
# % key: hql
# % type: string
# % required: yes
# % description: hive sql command
# %end
# %flag
# % key: f
# % description: fetch results
# %end

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():

    conn = ConnectionManager()

    conn.get_current_connection(options["conn_type"])
    hive = conn.get_hook()
    result = hive.execute(options["hql"], options["fatch"])
    if flags["f"]:
        for i in result:
            print(i)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
