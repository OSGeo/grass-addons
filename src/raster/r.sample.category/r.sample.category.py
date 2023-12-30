#!/usr/bin/env python


##############################################################################
#
# MODULE:     r.sample.category
# AUTHOR(S):  Vaclav Petras <wenzeslaus gmail com>
#             Anna Petrasova <kratochanna gmail com>
# PURPOSE:    Sample points from each category
# COPYRIGHT:  (C) 2015 by Vaclav Petras, and the GRASS Development Team
#
#             This program is free software under the GNU General Public
#             License (>=v2). Read the COPYING file that comes with GRASS
#             for details.
#
##############################################################################


# %module
# % description: Create sampling points from each category in a raster map
# % keyword: raster
# % keyword: sampling
# % keyword: random
# % keyword: points
# % keyword: vector
# % keyword: stratified random sampling
# % keyword: category
# %end
# %option G_OPT_R_INPUT
# % description: Name of input raster map with categories (classes)
# %end
# %option G_OPT_V_OUTPUT
# % description: Name of output vector map with points at random locations
# %end
# %option G_OPT_R_INPUTS
# % description: Names of input raster maps to be sampled
# % key: sampled
# % required: no
# %end
# %option
# % label: Number of sampling points per category in the input map
# % description: You can provide multiple numbers, one for each category in input raster (sorted ascending)
# % key: npoints
# % required: yes
# % multiple: yes
# % type: integer
# %end
# %option
# % key: random_seed
# % type: integer
# % required: no
# % multiple: no
# % description: Seed for random number generator
# %end
# %flag
# % key: s
# % description: If number of cells in category < npoints, skip category
# %end

# TODO: Python tests for more advanced things such as overwrite or attributes
# TODO: only optional sampling of the category raster
# TODO: preserver original raster categories as vector point categories
# TODO: specify number of points and distribute them uniformly
# TODO: specify number of points and distribute them according to histogram
# TODO: ensure/check minimum and maximum number of of points when doing histogram
# TODO: create function to check for mask
# TODO: move escape and mask functions to library

import os
import atexit

import grass.script as gscript


TMP = []


def cleanup():
    if TMP:
        gscript.run_command(
            "g.remove", flags="f", type=["raster", "vector"], name=TMP, quiet=True
        )


def escape_sql_column(name):
    """Escape string to create a safe name of column for SQL

    >>> escape_sql_column("elevation.10m")
    elevation_10m
    """
    name = name.replace(".", "_")
    return name


def strip_mapset(name):
    """Strip Mapset name and '@' from map name

    >>> strip_mapset('elevation@PERMANENT')
    elevation
    """
    if "@" in name:
        return name.split("@")[0]
    return name


def main():
    options, flags = gscript.parser()

    input_raster = options["input"]
    points = options["output"]
    if options["sampled"]:
        sampled_rasters = options["sampled"].split(",")
    else:
        sampled_rasters = []
    npoints = [int(num) for num in options["npoints"].split(",")]

    seed = None
    if options["random_seed"]:
        seed = int(options["random_seed"])
    flag_s = flags["s"]

    # we clean up mask too, so register after we know that mask is not present
    atexit.register(cleanup)

    temp_name = "tmp_r_sample_category_{}_".format(os.getpid())
    points_nocats = temp_name + "points_nocats"
    TMP.append(points_nocats)

    # input must be CELL
    rdescribe = gscript.read_command(
        "r.stats", flags="lnc", input=input_raster, separator="pipe"
    )
    catlab = rdescribe.splitlines()
    categories = list(map(int, [z.split("|")[0] for z in catlab]))
    pixlab = dict([z.split("|")[::2] for z in catlab])
    catlab = dict([z.split("|")[:2] for z in catlab])
    if len(npoints) == 1:
        npoints = npoints * len(categories)
    else:
        if len(categories) != len(npoints):
            gscript.fatal(
                _(
                    "Number of categories in raster does not match the number of provided sampling points numbers."
                )
            )

    # Create sample points per category
    vectors = []
    for i, cat in enumerate(categories):
        # skip generating points if none are required
        if npoints[i] == 0:
            continue

        # Check number of cells in category
        nrc = int(pixlab[str(cat)])
        if nrc < npoints[i]:
            if flag_s:
                gscript.info(
                    _("Not enough points in category {cat}. Skipping").format(
                        cat=categories[i]
                    )
                )
                continue
            gscript.warning(
                _(
                    "Number of raster cells in category {cat} < {np}. Sampling {n} points"
                ).format(cat=categories[i], np=npoints[i], n=nrc)
            )
            npoints[i] = nrc

        gscript.info(
            _("Selecting {n} sampling locations at category {cat}...").format(
                n=npoints[i], cat=cat
            )
        )

        # Create reclass map with only pixels of current category
        rc_rule = "{0} = {0}\n* = NULL".format(cat)
        gscript.write_command(
            "r.reclass",
            input=input_raster,
            output=temp_name,
            rules="-",
            stdin=rc_rule,
            overwrite=True,
            quiet=True,
        )

        if temp_name not in TMP:
            TMP.append(temp_name)

        # Create the points
        vector = temp_name + str(cat)
        vectors.append(vector)
        if seed is None:
            gscript.run_command(
                "r.random",
                input=temp_name,
                npoints=npoints[i],
                vector=vector,
                flags="s",
                quiet=True,
            )
        else:
            gscript.run_command(
                "r.random",
                input=temp_name,
                npoints=npoints[i],
                vector=vector,
                seed=seed,
                quiet=True,
            )
        TMP.append(vector)

    gscript.run_command("v.patch", input=vectors, output=points, quiet=True)
    # remove and add gain cats so that they are unique
    gscript.run_command(
        "v.category",
        input=points,
        option="del",
        cat=-1,
        output=points_nocats,
        quiet=True,
    )
    # overwrite to reuse the map
    gscript.run_command(
        "v.category",
        input=points_nocats,
        option="add",
        output=points,
        overwrite=True,
        quiet=True,
    )

    # Sample layers
    columns = []
    column_names = []
    sampled_rasters.insert(0, input_raster)
    for raster in sampled_rasters:
        column = escape_sql_column(strip_mapset(raster).lower())
        column_names.append(column)
        datatype = gscript.parse_command("r.info", flags="g", map=raster)["datatype"]
        if datatype == "CELL":
            datatype = "integer"
        else:
            datatype = "double precision"
        columns.append("{column} {datatype}".format(column=column, datatype=datatype))
    gscript.run_command(
        "v.db.addtable", map=points, columns=",".join(columns), quiet=True
    )
    for raster, column in zip(sampled_rasters, column_names):
        gscript.info(_("Sampling raster map %s...") % raster)
        gscript.run_command(
            "v.what.rast",
            map=points,
            type="point",
            raster=raster,
            column=column,
            quiet=True,
        )

    # Add category labels
    if not list(set(catlab.values()))[0] and len(set(catlab.values())) == 1:
        gscript.verbose(_("There are no category labels in the raster to add"))
    else:
        gscript.run_command("v.db.addcolumn", map=points, columns="label varchar(250)")
        table_name = escape_sql_column(strip_mapset(points).lower())
        for i in categories:
            sqlstat = (
                "UPDATE "
                + table_name
                + " SET label='"
                + catlab[str(i)]
                + "' WHERE "
                + column_names[0]
                + " == "
                + str(i)
            )
            gscript.run_command("db.execute", sql=sqlstat)

    gscript.vector_history(points, replace=True)


if __name__ == "__main__":
    main()
