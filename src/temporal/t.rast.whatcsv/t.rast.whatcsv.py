#!/usr/bin/env python

############################################################################
#
# MODULE:       t.rast.whatcsv
# AUTHOR(S):    Soeren Gebbert
#
# PURPOSE:      Sample a space time raster dataset at specific vector point
#               coordinates and write the output to stdout using different
#               layouts
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (version 2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Sample a space time raster dataset at specific space-time point coordinates from a csv file and write the output to stdout
# % keyword: temporal
# % keyword: raster
# % keyword: sampling
# % keyword: time
# %end

# %option G_OPT_F_INPUT
# % key: csv
# % description: Name for the output input csv file
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

# %option G_OPT_M_NULL_VALUE
# %end

# %option G_OPT_F_SEP
# %end

# %option
# % key: skip
# % type: integer
# % description: Number of header lines to skip in the csv file
# % required: yes
# %end

# %flag
# % key: n
# % description: Output header row
# %end

## Temporary disabled the r.what flags due to test issues
##%flag
##% key: f
##% description: Show the category labels of the grid cell(s)
##%end

##%flag
##% key: r
##% description: Output color values as RRR:GGG:BBB
##%end

##%flag
##% key: i
##% description: Output integer category values, not cell values
##%end

import sys
import copy
import csv
import grass.script as gscript
from grass.script import core as gcore
import grass.temporal as tgis
import grass.pygrass.modules as pymod


############################################################################


def main(options, flags):

    # Get the options
    csv_file = options["csv"]
    strds = options["strds"]
    output = options["output"]
    where = options["where"]
    null_value = options["null_value"]
    separator = options["separator"]

    write_header = flags["n"]

    # output_cat_label = flags["f"]
    # output_color = flags["r"]
    # output_cat = flags["i"]

    overwrite = gscript.overwrite()

    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    sp = tgis.open_old_stds(strds, "strds", dbif)

    # Setup separator
    if separator == "pipe":
        separator = "|"
    if separator == "comma":
        separator = ","
    if separator == "space":
        separator = " "
    if separator == "tab":
        separator = "\t"
    if separator == "newline":
        separator = "\n"

    r_what = gcore.read_command(
        "r.what", map="dummy", output="-", separator=separator, quiet=True
    )
    if len(s) == 0:
        gcore.fatal(_("No data returned from query"))

    reader = csv.reader(open(csv_file, "r"), delimiter=separator)

    for line in reader:
        id_, x, y, timestamp = line

        start = tgis.string_to_datetime(timestamp)
        where = "start_time <= '" + str(start) + "' AND end_time > '" + str(start) + "'"
        rows = sp.get_registered_maps(columns="id", where=where, dbif=dbif)
        for entry in rows:
            r_what.inputs.map = entry[0]
            r_what.inputs.coordinates = [x, y]
            r_what.run()
            out = "%s%s%s" % (id_, separator, r_what.outputs.stdout)

            sys.stdout.write(out)

    dbif.close()


if __name__ == "__main__":
    options, flags = gscript.parser()
    main(options, flags)
