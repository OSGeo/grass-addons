#!/usr/bin/env python

############################################################################
#
# MODULE:       db.hive.load
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
# % description: Load data to Hive table
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
# % key: table
# % type: string
# % required: yes
# % description: name of table
# %end
# %option
# % key: path
# % type: string
# % required: yes
# % description: path of hdfs file
# %end
# %option
# % key: partition
# % type: string
# % required: no
# % description:  partition as a dict of  columns and values
# %end

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    conn = ConnectionManager()

    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()
    hive.data2table(
        filepath=options["path"],
        table=options["table"],
        overwrite=options["path"],  # TODO
        partition=options["partition"],
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
