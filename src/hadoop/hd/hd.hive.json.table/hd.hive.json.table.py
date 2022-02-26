#!/usr/bin/env python

############################################################################
#
# MODULE:       hd.hive.json.table
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
# % description: Creating Hive spatial tables for storing Json map
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
# % options: hive_cli,hiveserver2
# % guisection: table
# %end
# %option
# % key: table
# % type: string
# % required: yes
# % description: name of table
# % guisection: table
# %end
# %option
# % key: columns
# % type: string
# % guisection: table
# %end
# %option
# % key: stored
# % type: string
# % required: no
# % description: output
# % guisection: table
# %end
# %option
# % key: serde
# % type: string
# % required: yes
# % answer: org.openx.data.jsonserde.JsonSerDe
# % description: java class for serialization of json
# % guisection: table
# %end
# %option
# % key: outformat
# % type: string
# % description: java class for handling output format
# % guisection: table
# %end
# %option
# % key: jsonpath
# % type: string
# % description: hdfs path specifying input data
# % guisection: data
# %end
# %flag
# % key: o
# % description: Possible if filepath for loading data is delcared. True-overwrite all data in table.
# % guisection: data
# %end
# %flag
# % key: d
# % description: Firstly drop table if exists
# % guisection: table
# %end
# %flag
# % key: e
# % description: The EXTERNAL keyword lets you create a table and provide a LOCATION so that Hive does not use a default location for this table. This comes in handy if you already have data generated. When dropping an EXTERNAL table, data in the table is NOT deleted from the file system.
# % guisection: table
# %end

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    if not options["columns"] and not options["struct"]:
        grass.fatal("Must be defined <attributes> or <struct> parameter")

    conn = ConnectionManager()
    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()
    hive.create_geom_table(
        table=options["table"],
        field=options["columns"],
        stored=options["stored"],
        serde=options["serde"],
        outputformat=options["outformat"],
        external=flags["e"],
        recreate=flags["d"],
        filepath=options["jsonpath"],
        overwrite=flags["o"],
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
