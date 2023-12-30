#!/usr/bin/env python
#
#########################################################################
#
# MODULE:       v.sort.points
#
# AUTHOR(S):    Moritz Lennert
#
# PURPOSE:      Takes a point map and creates a new point map with the points
#               sorted according to a chosen numeric column with largest
#               values first
#
# DATE:         Wed May  4 18:44:05 2016
#
#########################################################################

# %module
# % description: Sorts a vector point map according to a numeric column
# %end
# %option G_OPT_V_INPUT
# % required: yes
# %end
# %option G_OPT_V_FIELD
# % required: yes
# % answer: 1
# %end
# %option G_OPT_V_OUTPUT
# % required: yes
# %end
# %option G_OPT_DB_COLUMN
# % description: Name of attribute column used for sorting
# % required: yes
# %end
# %flag
# % key: r
# % description: do not reverse sort
# %end

import sys
import os

import grass.script as gscript


def num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except:
            return s


def main():
    options, flags = gscript.parser()
    inputmap = options["input"]
    layer = options["layer"]
    outputmap = options["output"]
    sort_column = options["column"]
    reverse = True
    if flags["r"]:
        reverse = False

    columns = gscript.vector_columns(inputmap)
    key_column = gscript.vector_layer_db(inputmap, layer)["key"]
    sort_index = columns[sort_column]["index"] + 2
    sorted_cols = sorted(iter(columns.items()), key=lambda x_y: x_y[1]["index"])
    column_def = "x DOUBLE PRECISION, y DOUBLE PRECISION, cat INTEGER"
    colnames = []
    for colcount in range(1, len(sorted_cols)):
        name = sorted_cols[colcount][0]
        type = sorted_cols[colcount][1]["type"]
        if name == sort_column and (type != "INTEGER" and type != "DOUBLE PRECISION"):
            gscript.fatal("Sort column must be numeric")
        if name == key_column:
            continue
        colnames.append(name)
        column_def += ", %s %s" % (name, type)

    inpoints = gscript.read_command(
        "v.out.ascii", in_=inputmap, columns=colnames, quiet=True
    )

    points = []
    for line in inpoints.splitlines():
        data = [num(x) for x in line.split("|")]
        points.append(data)

    points_sorted = sorted(points, key=lambda x: x[sort_index], reverse=reverse)

    outpoints = ""
    for list in points_sorted:
        outpoints += "|".join([str(x) for x in list]) + "\n"

    gscript.write_command(
        "v.in.ascii",
        input="-",
        stdin=outpoints,
        output=outputmap,
        x=1,
        y=2,
        cat=3,
        columns=column_def,
        quiet=True,
    )

    gscript.run_command("v.db.dropcolumn", map=outputmap, columns="x,y", quiet=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
