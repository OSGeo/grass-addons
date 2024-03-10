#!/usr/bin/env python

############################################################################
#
# MODULE:       v.what.rast.multi
# AUTHOR(S):    Pierre Roudier
# PURPOSE:      Uploads values of multiple rasters at positions of vector
#               points to the table.
# COPYRIGHT:    (C) 2017 by Pierre Roudier, and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %module
# % description: Uploads values of multiple rasters at positions of vector points to the table.
# % keyword: vector
# % keyword: sampling
# % keyword: raster
# % keyword: position
# % keyword: querying
# % keyword: attribute table
# % keyword: surface information
# %end

# %flag
# % key: i
# % description: Interpolate values from the nearest four cells
# %end

# %option
# % key: map
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % label: Name of vector points map for which to edit attributes
# % description: Or data source for direct OGR access
# % gisprompt: old,vector,vector
# %end

# %option
# % key: layer
# % type: string
# % required: no
# % multiple: no
# % label: Layer number or name
# % description: Vector features can have category values in different layers.
# This number determines which layer to use. When used with direct OGR access
# this is the layer name.
# % answer: 1
# % gisprompt: old,layer,layer
# %end

# %option
# % key: type
# % type: string
# % required: no
# % multiple: yes
# % options: point,centroid
# % description: Input feature type
# % answer: point
# %end

# %option
# % key: raster
# % type: string
# % required: yes
# % multiple: yes
# % key_desc: name
# % description: Name of existing raster map to be queried
# % gisprompt: old,cell,raster
# %end

# %option
# % key: columns
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Names of attribute columns to be updated with the query result
# % gisprompt: old,dbcolumn,dbcolumn
# %end

# %option
# % key: where
# % type: string
# % required: no
# % multiple: no
# % key_desc: sql_query
# % label: WHERE conditions of SQL statement without 'where' keyword
# % description: Example: income < 1000 and population >= 10000
# %end

# %flag
# % key: m
# % label: Retain mapset name
# % description: When no column names are provided, the column names are created using the names of the input layers. Using this flag will retain the mapset part of the name (if given), but replacing the @ for an underscore.
# %end

import sys
import os
import grass.script as grass
from grass.pygrass.modules.shortcuts import vector as v

if "GISBASE" not in os.environ:
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def strip_mapset(name, join_char="@"):
    """Strip mapset part of the layer name"""
    return name.split(join_char)[0] if join_char in name else name


def main():
    # Get options
    vmap = options["map"]  # Vector points
    layer = options["layer"]
    vtype = options["type"]
    rasters = options["raster"].split(",")  # List of rasters to sample
    columns = options["columns"].split(",")  # List of column names
    where = options["where"]

    # If length(columns) != length(rasters), throw error
    if columns != [""]:
        if len(columns) != len(rasters):
            grass.fatal(
                _("The number of rasters and the number of column names do not match")
            )

    # Get flags
    if flags["i"]:
        fl = "i"
    else:
        fl = ""

    # For each raster
    for i in range(len(rasters)):
        # Determine column name
        r = rasters[i]
        if columns != [""]:
            c = columns[i]
        else:
            if flags["m"]:
                c = r.replace("@", "_")
            else:
                c = strip_mapset(r)

        # Sample using v.what.rast
        v.what_rast(
            map=vmap, layer=layer, type=vtype, raster=r, column=c, where=where, flags=fl
        )

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
