#!/usr/bin/env python

############################################################################
#
# MODULE:       hd.hdfs.out.vector
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
# % description: Module for creting map from HIVE table. Module convert esri GeoJson to Grass map
# % keyword: database
# % keyword: hdfs
# % keyword: hive
# %end
# %option
# % key: driver
# % type: string
# % required: yes
# % options: webhdfs
# % description: HDFS driver
# %end
# %option
# % key: table
# % type: string
# % description: Name of table for import
# %end
# %option
# % key: hdfs
# % type: string
# % description: Hdfs path to the table. See hive.info table -h
# %end
# %option G_OPT_V_OUTPUT
# % key: out
# % required: yes
# %end
# %flag
# % key: r
# % description: remove temporal file
# % guisection: data
# %end
# %option
# % key: attributes
# % type: string
# % description: list of attributes with datatype
# % guisection: data
# %end

import os
import sys

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import (
    GrassMapBuilderEsriToEsri,
    GrassHdfs,
    ConnectionManager,
)
from hdfsgrass.hdfs_grass_util import get_tmp_folder


import shutil


def main():
    tmp_dir = os.path.join(get_tmp_folder(), options["out"])

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    transf = GrassHdfs(options["driver"])
    table_path = options["hdfs"]

    if options["table"]:
        conn = ConnectionManager()
        conn.get_current_connection("hiveserver2")

        if not conn.get_current_connection("hiveserver2"):
            grass.fatal(
                "Cannot connet to hive for table description. "
                "Use param hdfs without param table"
            )

        hive = conn.get_hook()
        table_path = hive.find_table_location(options["table"])
        tmp_dir = os.path.join(tmp_dir, options["table"])

    if not transf.download(hdfs=table_path, fs=tmp_dir):
        return

    files = os.listdir(tmp_dir)
    map_string = ""
    for block in files:
        map = "%s_%s" % (options["out"], block)
        block = os.path.join(tmp_dir, block)

        map_build = GrassMapBuilderEsriToEsri(block, map, options["attributes"])
        try:
            map_build.build()
            map_string += "%s," % map
        except Exception as e:
            grass.warning("Error: %s\n     Map < %s >  conversion failed" % (e, block))

    path, folder_name = os.path.split(tmp_dir)
    grass.message(
        "For merge map: v.patch output=%s -e --overwrite input=%s"
        % (folder_name, map_string)
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
