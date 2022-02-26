#!/usr/bin/env python

############################################################################
#
# MODULE:       t.rast.out.xyz
# AUTHOR(S):    Luca Delucchi
#
# PURPOSE:      Export space time raster dataset to a CSV file.
# COPYRIGHT:    (C) 2011-2014 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (version 2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Export space time raster dataset to a CSV file.
# % keyword: temporal
# % keyword: raster
# % keyword: export
# % keyword: ASCII
# % keyword: conversion
# %end

# %option G_OPT_STRDS_INPUT
# % key: strds
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# % description: Name for the output file or "-" in case stdout should be used
# % answer: -
# %end

# %option G_OPT_T_WHERE
# %end

# %option G_OPT_F_SEP
# %end

# %flag
# % key: i
# % description: Include no data values
# %end

import grass.script as gscript
import grass.temporal as tgis


def main(options, flags):
    strds = options["strds"]
    out_name = options["output"]
    where = options["where"]
    sep = options["separator"]
    donodata = ""
    if flags["i"]:
        donodata = "i"
    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    sp = tgis.open_old_stds(strds, "strds", dbif)
    maps = sp.get_registered_maps_as_objects(where, "start_time", None)
    if maps is None:
        gscript.fatal(
            _("Space time raster dataset {st} seems to be " "empty".format(st=strds))
        )
        return 1
    mapnames = [mapp.get_name() for mapp in maps]
    try:
        gscript.run_command(
            "r.out.xyz",
            input=",".join(mapnames),
            output=out_name,
            separator=sep,
            flags=donodata,
            overwrite=gscript.overwrite(),
        )
        gscript.message(
            _(
                "Space time raster dataset {st} exported to "
                "{pa}".format(st=strds, pa=out_name)
            )
        )
    except:
        gscript.fatal(
            _("Unable to export space time raster dataset " "{st}".format(st=strds))
        )
        return 1


if __name__ == "__main__":
    options, flags = gscript.parser()
    main(options, flags)
