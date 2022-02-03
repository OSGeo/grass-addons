#!/usr/bin/env python
############################################################################
#
# MODULE:       v.gsflow.mapdata
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Generalized interface for data import into GSFLOW data
#               structures: HRUs, MODFLOW grid cells, gravity reservoirs,
#               segments, and reaches.
#
# COPYRIGHT:    (c) 2018 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  uses inputs from r.stream.extract

# More information
# Started December 2016

# %module
# % description: Upload data to PRMS data
# % keyword: vector
# % keyword: import
# % keyword: hydrology
# % keyword: GSFLOW
# %end

# %option G_OPT_V_INPUT
# %  key: map
# %  label: GSFLOW vect: HRUs, MODFLOW grid, gravres, segments, or reaches
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_V_INPUT
# %  key: vector_area
# %  label: Input vector area (polygon) data set (e.g., geologic map)
# %  required: no
# %  guidependency: layer,column
# %end

# %option G_OPT_V_INPUT
# %  key: vector_points
# %  label: Input vector points data set (e.g., field surveys at points)
# %  required: no
# %  guidependency: layer,column
# %end

# %option G_OPT_R_INPUT
# %  key: raster
# %  label: Input raster gridded data set (e.g., gridded soils data)
# %  required: no
# %  guidependency: layer,column
# %end

# %option
# %  key: dxy
# %  type: string
# %  description: Cell size for rasterization of vector_area, if needed
# %  answer: 100
# %  required: no
# %end

# %option
# %  key: column
# %  type: string
# %  description: Column to which to upload data (will create if doesn't exist)
# %  required: no
# %end

# %option
# %  key: from_column
# %  type: string
# %  description: Column from which to upload data (for vector input)
# %  required: no
# %end

# %option
# %  key: attrtype
# %  type: string
# %  description: Data type in column; user may treat int as float
# %  options: int,float,string
# %  required: no
# %end

# %rules
# % exclusive: vector_area, vector_points, raster
# % requires: vector_area, column, from_column, attrtype
# % requires: vector_points, column, from_column, attrtype
# %end


##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np

# GRASS
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.modules.shortcuts import miscellaneous as m
from grass.pygrass.gis import region
from grass.pygrass import vector  # Change to "v"?
from grass.script import vector_db_select
from grass.pygrass.vector import Vector, VectorTopo
from grass.pygrass.raster import RasterRow
from grass.pygrass import utils
from grass import script as gscript

###############
# MAIN MODULE #
###############


def main():
    """
    Import any raster or vector data set and add its attribute
    to a GSFLOW data object
    """

    ##################
    # OPTION PARSING #
    ##################

    options, flags = gscript.parser()

    # Parsing
    if options["attrtype"] == "int":
        attrtype = "integer"
    elif options["attrtype"] == "float":
        attrtype = "double precision"
    elif options["attrtype"] == "string":
        attrtype = "varchar"
    else:
        attrtype = ""

    ########################################
    # PROCESS AND UPLOAD TO DATABASE TABLE #
    ########################################

    if options["vector_area"] is not "":
        gscript.use_temp_region()
        g.region(vector=options["map"], res=options["dxy"])
        v.to_rast(
            input=options["vector_area"],
            output="tmp___tmp",
            use="attr",
            attribute_column=options["from_column"],
            quiet=True,
            overwrite=True,
        )
        try:
            gscript.message("Checking for existing column to overwrite")
            v.db_dropcolumn(map=options["map"], columns=options["column"], quiet=True)
        except:
            pass
        if attrtype is "double precision":
            try:
                gscript.message("Checking for existing column to overwrite")
                v.db_dropcolumn(map=options["map"], columns="tmp_average", quiet=True)
            except:
                pass
            v.rast_stats(
                map=options["map"],
                raster="tmp___tmp",
                column_prefix="tmp",
                method="average",
                flags="c",
                quiet=True,
            )
            g.remove(type="raster", name="tmp___tmp", flags="f", quiet=True)
            v.db_renamecolumn(
                map=options["map"],
                column=["tmp_average", options["column"]],
                quiet=True,
            )

        else:
            try:
                v.db_addcolumn(
                    map=options["map"],
                    columns=options["column"] + " " + attrtype,
                    quiet=True,
                )
            except:
                pass
            gscript.run_command(
                "v.distance",
                from_=options["map"],
                to=options["vector_area"],
                upload="to_attr",
                to_column=options["from_column"],
                column=options["column"],
                quiet=True,
            )
    elif options["vector_points"] is not "":
        try:
            gscript.message("Checking for existing column to overwrite")
            v.db_dropcolumn(map=options["map"], columns=options["column"], quiet=True)
            v.db_addcolumn(
                map=options["map"],
                columns=options["column"] + " " + attrtype,
                quiet=True,
            )
        except:
            pass
        gscript.run_command(
            "v.distance",
            from_=options["map"],
            to=options["vector_points"],
            upload="to_attr",
            to_column=options["from_column"],
            column=options["column"],
            quiet=True,
        )

    elif options["raster"] is not "":
        try:
            gscript.message("Checking for existing column to overwrite")
            v.db_dropcolumn(map=options["map"], columns=options["column"], quiet=True)
        except:
            pass
        v.rast_stats(
            map=options["map"],
            raster=options["raster"],
            column_prefix="tmp",
            method="average",
            flags="c",
            quiet=True,
        )
        v.db_renamecolumn(
            map=options["map"], column=["tmp_average", options["column"]], quiet=True
        )

    gscript.message("Done.")


if __name__ == "__main__":
    main()
