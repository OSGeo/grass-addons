#!/usr/bin/env python

############################################################################
#
# MODULE:       hd.hive.info
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
# % description: Module for geting metadata of tables in hive
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
# % options: hiveserver2, hiveserver2
# %end
# %option
# % key: table
# % type: string
# % required: no
# % description: Name of table
# % guisection: Connection
# %end
# %option
# %flag
# % key: p
# % description: print tables
# % guisection: table
# %end
# %flag
# % key: d
# % description: describe table
# % guisection: table
# %end
# %flag
# % key: h
# % description: print hdfs path of table
# % guisection: table
# %end


import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    conn = ConnectionManager()
    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()
    if flags["p"]:
        hive.show_tables()
    if flags["d"]:
        if not options["table"]:
            grass.fatal("With flag <d> table must be defined")
        hive.describe_table(options["table"], True)

    if flags["h"]:
        if not options["table"]:
            grass.fatal("With flag <h> table must be defined")
        print(hive.find_table_location(options["table"]))

    if options["path"]:
        hive.check_for_content(options["path"])


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
