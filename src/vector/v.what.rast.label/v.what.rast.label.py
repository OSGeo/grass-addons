#!/usr/bin/env python

##############################################################################
#
# MODULE:       v.what.rast.label
# AUTHOR(S):    Paulo van Breugel <paulo at ecodiv dot earth>
# PURPOSE:      Upload raster values and labels at positions of vector points
#               to the vector attribute table.
#
# COPYRIGHT: (C) 2016-2022 by Paulo van Breugel and the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
##############################################################################

#%module
#% description: Uploads raster values and labels to vector point layer
#% keyword: vector
#% keyword: sampling
#% keyword: raster
#% keyword: position
#% keyword: querying
#% keyword: attribute table
#% keyword: surface information
#%end

#%option G_OPT_V_MAP
#% key: vector
#% description: Name vector points map for which to add raster values & labels
#% guisection: Input
#% required: yes
#%end

#%option G_OPT_R_INPUTS
#% key: raster
#% description: Name of raster map(s) with labels to be queried
#% guisection: Input
#% required: yes
#% multiple: yes
#%end

#%option G_OPT_R_INPUTS
#% key: raster2
#% description: Name of raster map(s) without labels to be queried
#% guisection: Input
#% required: no
#% multiple: yes
#%end

#%option G_OPT_V_OUTPUT
#% description: Name of output point layer
#% key_desc: name
#% guisection: Input
#% required: yes
#%end

#%flag
#% key: o
#% description: Include columns of input vector map
#%end

#%flag
#% key: c
#% description: Include point coordinates
#%end
# import libraries
import os
import sys
import atexit
from subprocess import PIPE
import grass.script as gs
from grass.pygrass.modules import Module

# create set to store names of temporary maps to be deleted upon exit
clean_layers = []


def tmpname():
    """Generate a tmp name and stores it in the global list."""
    tmpf = gs.tempname(12)
    clean_layers.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps specified in the global list"""
    list_temporary_layers = list(reversed(clean_layers))
    for temporary_layer in list_temporary_layers:
        ffile = gs.find_file(
            name=temporary_layer, element="vector", mapset=gs.gisenv()["MAPSET"]
        )
        if ffile["file"]:
            gs.run_command(
                "g.remove", flags="f", type="vector", name=temporary_layer, quiet=True
            )


def main(options, flags):

    # Variables
    raster_cat = options["raster"]
    raster_cat = raster_cat.split(",")
    raster_cat_names = [z.split("@")[0] for z in raster_cat]
    raster_cat_names = [x.lower() for x in raster_cat_names]
    raster_cont = options["raster2"]
    raster_cont = raster_cont.split(",")
    raster_cont_names = [z.split("@")[0] for z in raster_cont]
    raster_cont_names = [x.lower() for x in raster_cont_names]
    input_vector = options["vector"]
    output_vector = options["output"]

    if flags["o"]:
        tmp_layer = tmpname()
        Module("g.copy", vector=[input_vector, output_vector], quiet=True)
    else:
        tmp_layer = output_vector
    # Create vector with column names
    base_column_names = ["x double precision, y double precision, label integer"]
    for i, raster_name in enumerate(raster_cat):
        data_types = gs.parse_command("r.info", flags="g", map=raster_name, quiet=True)[
            "datatype"
        ]
        if data_types == "CELL":
            base_column_names.append(
                "{0}_ID integer, {0} varchar(255)".format(raster_cat_names[i])
            )
        else:
            base_column_names.append(
                "ID_{0} double precision, {0} varchar(255)".format(raster_cat_names[i])
            )
    column_names = ",".join(base_column_names)

    # Get raster points of raster layers with labels
    # Export point map to text file first and use that as input in r.what
    point_to_ascii = Module(
        "v.out.ascii",
        input=input_vector,
        format="point",
        separator="space",
        precision=12,
        stdout_=PIPE,
    ).outputs.stdout
    raster_cats = Module(
        "r.what", flags="f", map=raster_cat, stdin_=point_to_ascii, stdout_=PIPE
    ).outputs.stdout
    ascii_to_point = raster_cats.replace("|*|", "||")
    Module(
        "v.in.ascii",
        input="-",
        stdin_=ascii_to_point,
        output=tmp_layer,
        columns=column_names,
        separator="pipe",
        format="point",
        x=1,
        y=2,
        quiet=True,
    )

    # In- or exclude coordinates
    if not flags["c"]:
        Module("v.db.dropcolumn", map=tmp_layer, columns=["x", "y"])
    # Get raster points of raster layers without labels (optional)
    if options["raster2"]:
        for j, raster_cont_values in enumerate(raster_cont):
            Module(
                "v.what.rast",
                map=tmp_layer,
                raster=raster_cont_values,
                column=raster_cont_names[j],
                quiet=True,
            )
    # Join table of original layer (and drop label columns)

    if flags["o"]:

        cols = Module("db.columns", table=tmp_layer, stdout_=PIPE).outputs.stdout.split(
            "\n"
        )
        cols.pop()
        del cols[:1]

        sqlstat = "CREATE INDEX {0}_label ON {0} (label);".format(tmp_layer)
        Module("db.execute", sql=sqlstat)
        Module(
            "v.db.join",
            map=output_vector,
            column="cat",
            other_table=tmp_layer,
            other_column="label",
            subset_columns=cols,
        )
    # Remove label column
    Module("v.db.dropcolumn", map=output_vector, columns=["label"])

    # Write metadata
    gs.vector_history(output_vector, replace=True)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
