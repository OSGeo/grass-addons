#!/usr/bin/env python3
############################################################################
#
# MODULE:       v.to.rast.multi
# AUTHOR(S):    Stefan Blumentrath
# PURPOSE:      Create multiple raster maps from attribute columns in a vector map
# COPYRIGHT:    (C) 2022 by Stefan Blumentrath, and the GRASS Development Team
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

#%module
#% description: Create raster maps for multiple numeric attribute columns of a vector map
#% keyword: vector
#% keyword: conversion
#% keyword: raster
#% keyword: rasterization
#% keyword: reclassify
#% keyword: multiple
#%end

#%flag
#% key: d
#% label: Create densified lines (default: thin lines)
#% description: All cells touched by the line will be set, not only those on the render path
#%end

#%option
#% key: input
#% type: string
#% required: yes
#% multiple: no
#% key_desc: name
#% label: Name of input vector map
#% description: Or data source for direct OGR access
#% gisprompt: old,vector,vector
#%end

#%option
#% key: layer
#% type: string
#% required: no
#% multiple: no
#% label: Layer number or name
#% description: Vector features can have category values in different layers. This number determines which layer to use. When used with direct OGR access this is the layer name.
#% answer: 1
#% gisprompt: old,layer,layer
#%end

#%option
#% key: type
#% type: string
#% required: no
#% multiple: yes
#% options: point,line,boundary,centroid,area
#% description: Input feature type
#% answer: point,line,area
#% guisection: Selection
#%end

#%option
#% key: cats
#% type: string
#% required: no
#% multiple: no
#% key_desc: range
#% label: Category values
#% description: Example: 1,3,7-9,13
#% gisprompt: old,cats,cats
#% guisection: Selection
#%end

#%option
#% key: where
#% type: string
#% required: no
#% multiple: no
#% key_desc: sql_query
#% label: WHERE conditions of SQL statement without 'where' keyword
#% description: Example: income < 1000 and population >= 10000
#% gisprompt: old,sql_query,sql_query
#% guisection: Selection
#%end

#%option
#% key: output
#% type: string
#% required: yes
#% multiple: no
#% key_desc: prefix
#% description: Prefix for output raster maps
#% gisprompt: new,cell,raster
#%end

#%option
#% key: key_column
#% type: string
#% required: yes
#% multiple: no
#% answer: cat
#% key_desc: name
#% description: Name of the key column (default: cat, data type must be integer)
#% gisprompt: old,dbcolumn,dbcolumn
#% guisection: Attributes
#%end

#%option
#% key: attribute_columns
#% type: string
#% required: yes
#% multiple: yes
#% key_desc: names
#% description: Names of columns for 'attr' parameter (data type must be numeric)
#% gisprompt: old,dbcolumn,dbcolumn
#% guisection: Attributes
#%end

#%option
#% key: label_columns
#% type: string
#% required: no
#% multiple: yes
#% key_desc: names
#% description: Names of columns used as raster category labels
#% gisprompt: old,dbcolumn,dbcolumn
#% guisection: Attributes
#%end

#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% key_desc: memory in MB
#% label: Maximum memory to be used (in MB)
#% description: Cache size for raster rows
#% answer: 300
#%end

#%option
#% key: ndigits
#% type: integer
#% required: no
#% multiple: yes
#% key_desc: number of digits
#% label: Number of significant digits per attribute column
#% description: Number of significant digits per attribute column (for columns with floating point data)
#%end

#%option G_OPT_M_SEP
#% key: separator
#% key_desc: Separator
#% description: Separator used for parsing attribute table (it should not occur in any selected column)
#%end

import sys
import numpy as np
import grass.script as gscript


def check_columns(module_options):
    """Check if column is numeric"""
    supported_numeric = ["INTEGER", "DOUBLE PRECISION"]
    vmap_cols = gscript.vector.vector_columns(
        module_options["input"], layer=module_options["layer"]
    )
    for at in ["attribute_columns", "label_columns"]:  # , "rgb_columns"
        if module_options[at]:
            for col in module_options[at].split(","):
                if col and not col in vmap_cols.keys():
                    gscript.fatal(
                        _(
                            "Column {col} not in attribute table of map <{m}> with layer <{l}>".format(
                                m=module_options["input"],
                                l=module_options["layer"],
                                col=col,
                            )
                        )
                    )
                if at == "attribute_columns":
                    if vmap_cols[col]["type"] not in supported_numeric:
                        gscript.fatal(
                            _(
                                "Type {t} of column {col} is not a numeric type supportedby this module".format(
                                    t=vmap_cols[at]["type"], col=col
                                )
                            )
                        )
    if module_options["key_column"] not in vmap_cols:
        gscript.fatal(
            _(
                "Key column <{col}> not found in attribute table of map <{m}> at layer <{l}>".format(
                    m=module_options["input"],
                    l=module_options["layer"],
                    col=module_options["key_column"],
                )
            )
        )
    if vmap_cols[module_options["key_column"]]["type"] != "INTEGER":
        gscript.fatal(
            _(
                "The key column has to be integer, but column <{col}> is of "
                "type {t}".format(
                    t=vmap_cols[module_options["key_column"]]["type"],
                    col=module_options["key_column"],
                )
            )
        )


def main():
    # Parse options
    attribute_columns = (
        options["attribute_columns"].split(",")
        if options["attribute_columns"]
        else None
    )
    label_columns = (
        options["label_columns"].split(",") if options["label_columns"] else None
    )
    ndigits = (
        list(map(int, options["ndigits"].split(","))) if options["ndigits"] else None
    )
    output = options["output"]
    key_column = options["key_column"]
    sep = options["separator"]

    if key_column in attribute_columns:
        gscript.fatal(
            _(
                "A raster map for the <key_column> is always produced "
                "it thus should not be given in the <attribute_columns> option."
            )
        )

    if label_columns and len(label_columns) != len(attribute_columns):
        gscript.fatal(
            _(
                "If the <label_columns> option is used it has to have the same "
                "length (number of commas) as the <attribute_columns> option."
            )
        )

    if ndigits and len(ndigits) != len(attribute_columns):
        gscript.fatal(
            _(
                "If the <ndigits> option is used it has to have the same "
                "length (number of commas) as the <attribute_columns> option."
            )
        )

    # Check if valid columns are selected
    check_columns(options)

    # Rasterize key_kolumn
    v_to_rast_kwargs = {
        k: options[k] for k in ["input", "layer", "type", "cats", "where", "memory"]
    }

    if options["key_column"] and options["key_column"] != "cat":
        v_to_rast_kwargs["use"] = "attr"
        v_to_rast_kwargs["attr_column"] = options["key_column"]
    else:
        v_to_rast_kwargs["use"] = "cat"

    gscript.run_command(
        "v.to.rast",
        quiet=True,
        output=f"{output}_{key_column}",
        flags="d" if flags["d"] else None,
        **v_to_rast_kwargs,
    )

    # Write raster history for key_column map
    gscript.raster.raster_history(f"{output}_{key_column}", overwrite=True)

    # Load attribute data to numpy
    columns = [key_column]
    columns.extend(attribute_columns)
    if label_columns:
        columns.extend([col for col in label_columns if col])

    select_kwargs = {
        "map": options["input"],
        "layer": options["layer"],
        "null_value": "*",
        "columns": ",".join(set(columns)),
    }
    attributes = np.genfromtxt(
        gscript.read_command("v.db.select", separator=sep, **select_kwargs)
        .rstrip()
        .split("\n"),
        encoding=None,
        delimiter=sep,
        dtype=None,
        names=True,
        missing_values="*",
    )

    # Create raster map for each selected attribute column
    for idx, col in enumerate(attribute_columns):
        # Scale to the user-given significant digit input as r.reclass only suppoerts int
        if ndigits and ndigits[idx] and ndigits[idx] > 0:
            attributes[col] = attributes[col] * 10 ** ndigits[idx]
        # Create reclass rules
        if label_columns and label_columns[idx]:
            rules = "\n".join(
                [
                    "{} = {} {}".format(
                        a[key_column], int(a[col]), a[label_columns[idx]]
                    )
                    for a in attributes
                ]
            )
        else:
            rules = "\n".join(
                [
                    "{} = {}".format(a[key_column], int(a[col]))
                    for a in attributes[[key_column, col]]
                ]
            )
        # Reclassify key_column map
        gscript.write_command(
            "r.reclass",
            input=f"{output}_{key_column}",
            output=f"{output}_{col}",
            rules="-",
            stdin=rules,
        )
        # Write raster history
        gscript.raster.raster_history(f"{output}_{col}", overwrite=True)

    return 0


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
