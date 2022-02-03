#!/usr/bin/env python

############################################################################
#
# MODULE:       hd.esri2vector
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
# % description:  Module for conversion Esri GeoJson to GRASS vector
# % keyword: database
# % keyword: hdfs
# % keyword: hive
# %end
# %option G_OPT_V_OUTPUT
# % key: out
# % required: yes
# %end
# %option
# % key: path
# % type: string
# % description:  path to the folder with files.
# %end
# %option
# % key: attributes
# % type: string
# % description: list of attributes with datatype
# %end


import os
import sys

import grass.script as grass

from hdfsgrass.hdfs_grass_lib import GrassMapBuilderEsriToEsri


def main():

    files = os.listdir(options["path"])
    map_string = ""
    # download and convert  blocks of table
    for block in files:
        map = "%s_0%s" % (options["out"], block)
        block = os.path.join(options["path"], block)
        map_build = GrassMapBuilderEsriToEsri(block, map, options["attributes"])
        try:
            map_build.build()
            map_string += "%s," % map
        except Exception, e:
            grass.warning("Error: %s\n     Map < %s >  conversion failed" % (e, block))

    path, folder_name = os.path.split(options["path"])
    grass.message(
        "For merge map: v.patch output=%s -e --overwrite input=%s"
        % (folder_name, map_string)
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
