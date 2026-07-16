#!/usr/bin/env python

############################################################################
#
# MODULE:       hd.hive.execute
# AUTHOR(S):    Matej Krejci (matejkrejci@gmail.com)
#
# SPDX-FileCopyrightText: 2016 Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
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
# %option
# % key: schema
# % type: string
# % required: no
# % description: hive db schema
# %end
# %G_OPT_F_OUTPUT
# % key: out
# % type: string
# % required: no
# % description: Name for output file (if omitted output to stdout)
# %end

import grass.script as gs

from hdfsgrass.hdfs_grass_lib import ConnectionManager


def main():
    conn = ConnectionManager()

    conn.get_current_connection(options["driver"])
    hive = conn.get_hook()

    if not options["schema"]:
        options["schema"] = "default"

    out = hive.get_results(hql=options["hql"], schema=options["schema"])

    if options["out"]:
        with open(out, "w") as io:
            io.writelines(out)
            io.close()
    else:
        print(out)


if __name__ == "__main__":
    options, flags = gs.parser()
    main()

