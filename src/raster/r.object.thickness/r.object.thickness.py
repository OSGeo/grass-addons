#!/usr/bin/env python
#
############################################################################
#
# MODULE:    r.object.thickness
# AUTHOR(S): Paolo Zatelli
# PURPOSE:   Evaluates the maximum thickness of objects of a given category
#            on a raster map
#
# COPYRIGHT: (C) 2019 Paolo Zatelli
#
#   This program is free software under the GNU General Public
#   License (>=v2). Read the file COPYING that comes with GRASS
#   for details.
#
#############################################################################
# %Module
# % description: Evaluates minimum, maximum and mean thickness of objects of a given category on a raster map.
# % keyword: raster
# % keyword: algebra
# % keyword: size
# % keyword: clumps
# %end
# %option G_OPT_R_INPUT
# %end

# %option
# % key: category
# % type: integer
# % required: yes
# % multiple: no
# % description: Category to evaluate
# %end

# %option
# % key: tsize
# % type: double
# % required: yes
# % multiple: no
# % description: Expected maximum size in map units
# % answer: 100
# %end

# %option
# % key: tspace
# % type: double
# % required: yes
# % multiple: no
# % description: Transect spacing in map units
# % answer: 2
# %end

# %option
# % key: resolutiondir
# % type: string
# % description: Resolution for output in pixels
# % required: yes
# % options: N-S,E-W
# % answer: N-S
# %end

# %option G_OPT_R_OUTPUT
# % key: rmedian
# % description: Raster map of median lines
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_V_OUTPUT
# % key: vmedian
# % description: Vector map of median lines
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_V_OUTPUT
# % key: vcategories
# % description: Vector map of areas
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_V_OUTPUT
# % key: transects
# % description: Vector map of complete transects
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_V_OUTPUT
# % key: itransects
# % description: Vector map of inner transects
# % required: no
# % guisection: Optional
# %end

# %option G_OPT_F_OUTPUT
# % key: csvfilename
# % description: CSV output file
# % required: no
# % guisection: Optional
# %end

# %option
# % key: metric
# % type: string
# % description: Determines how transect spacing is measured
# % multiple: no
# % options: straight, along
# % descriptions: straight;Straight distance between transect points;along;Distance along the line (see v.transect for details)
# % answer: straight
# %end

# %option
# % key: transect_perpendicular
# % type: string
# % description: Determines which line is the transect perpendicular to
# % multiple: no
# % options: trend, line
# % descriptions: trend; Perpendicular to the line connecting transect points. line; Perpendicular to the particular segment of the original line  (see v.transect for details)
# % answer: trend
# %end

# %option
# % key: iterations
# % type: integer
# % description: Maximum number of iterations (used during thinning)
# % required: no
# % answer: 200
# %end

import sys
import os
import atexit
import csv
from statistics import median
import uuid
import grass.script as gs
from grass.exceptions import CalledModuleError

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))

# Cleanup
CLEAN_LAY = []
DBTABLE = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_LAY))
    for rast in cleanrast:
        gs.run_command(
            "g.remove", type=["raster", "vector"], name=rast, quiet=True, flags="f"
        )
    if len(DBTABLE) > 0:
        gs.run_command("db.droptable", flags="f", table=DBTABLE[0], quiet=True)


def create_unique_name(name):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    return gs.append_uuid(name)


def create_temporary_name(prefix):
    tmpf = create_unique_name(prefix)
    CLEAN_LAY.append(tmpf)
    return tmpf


def main():
    # required input
    input = options["input"]
    category = int(options["category"])
    tsize = float(options["tsize"])
    tspace = float(options["tspace"])

    # optional output
    rmedian = options["rmedian"]
    vcategories = options["vcategories"]
    vmedian = options["vmedian"]
    transects = options["transects"]
    itransects = options["itransects"]
    csv_file_out = options["csvfilename"]
    resolutiondir = options["resolutiondir"]

    # check if v.transects is installed
    if not gs.find_program("v.transects", "--help"):
        message = _("You need to install the addon v.transects to be able")
        message += _(" to run r.object.thickness.\n")
        message += _(" You can install the addon with 'g.extension v.transects'")
        gs.fatal(message)

    # check if input file exists
    if not gs.find_file(input)["file"]:
        gs.fatal(_("Raster map {} not found").format(input))

    # strip mapset name
    in_name_strip = options["input"].split("@")
    in_name = in_name_strip[0]

    # create a map containing only the category to replace and NULL
    categorymap = create_temporary_name(f"{in_name}_bin_")
    gs.verbose("Category map: {}".format(categorymap))
    gs.verbose(_("Extracting category: {}").format(category))

    gs.run_command(
        "r.mapcalc",
        expression="{outmap}=if({inmap}=={cat}, 1, null())".format(
            outmap=categorymap, inmap=input, cat=category
        ),
        quiet=True,
    )

    # create a map containing midlines for each clump
    gs.verbose(_("Finding median lines"))
    categorymap_thin = f"{categorymap}_thin"
    CLEAN_LAY.append(categorymap_thin)
    try:
        thin_message = gs.run_command(
            "r.thin",
            input=categorymap,
            output=categorymap_thin,
            iterations=int(options["iterations"]),
            quiet=True,
        )
        # convert to vector
        gs.verbose(_("Creating vector map of median lines"))
        gs.run_command(
            "r.to.vect",
            input=categorymap_thin,
            output=categorymap_thin,
            type="line",
            quiet=True,
        )
    except CalledModuleError:
        gs.fatal(
            "Creating the median lines failed. Try to increase the number of iterations"
        )

    # create transects
    # half size (left and right) of the transect, must be larger than the larger expected half size of objects
    dsize = tsize / 2
    categorymap_transects = f"{categorymap}_transects"
    CLEAN_LAY.append(categorymap_transects)
    gs.verbose(_("Creating transects"))
    gs.run_command(
        "v.transects",
        input=categorymap_thin,
        output=categorymap_transects,
        transect_spacing=tspace,
        dleft=dsize,
        dright=dsize,
        transect_perpendicular=options["transect_perpendicular"],
        metric=options["metric"],
        quiet=True,
    )

    # clip transects with the clumps
    # convert binarymap to vector
    gs.verbose(_("Creating vector area map"))
    gs.run_command(
        "r.to.vect", input=categorymap, output=categorymap, type="area", quiet=True
    )

    # drop unneeded column "label" from the table
    gs.run_command("v.db.dropcolumn", map=categorymap, columns="label", quiet=True)

    # clip transects with object
    categorymap_transects_inside = f"{categorymap}_transects_inside"
    CLEAN_LAY.append(categorymap_transects_inside)

    gs.verbose(_("Clipping transects"))
    # exit if no transect has been created
    try:
        testrun = gs.run_command(
            "v.overlay",
            ainput=categorymap_transects,
            binput=categorymap,
            output=categorymap_transects_inside,
            operator="and",
            quiet=True,
        )
    except CalledModuleError:
        # cleanup
        # raster
        temp_raster_maps = [categorymap, categorymap_thin]
        for temp_map in temp_raster_maps:
            gs.run_command(
                "g.remove", type="raster", name=temp_map, flags="f", quiet=True
            )
        # vector
        temp_vector_maps = [categorymap, categorymap_thin, categorymap_transects]
        for temp_map in temp_vector_maps:
            gs.run_command(
                "g.remove", type="vector", name=temp_map, flags="f", quiet=True
            )

        message = _("No transects created:")
        message += _(" lower transects spacing.")
        gs.fatal(message)

    # upload transects' lengths
    gs.run_command(
        "v.to.db",
        map=categorymap_transects_inside,
        option="length",
        columns="length",
        quiet=True,
    )

    # CSV manipulation
    # create temporary csv file
    csv_file = f"{gs.tempdir()}/{gs.tempname(8)}.csv"

    gs.verbose(_("Creating CSV file"))
    gs.run_command(
        "v.out.ogr",
        input=categorymap_transects_inside,
        output=csv_file,
        format="CSV",
        quiet=True,
    )

    # initializing the titles and rows list
    fields = []
    rows = []

    # reading csv file
    with open(csv_file, "r") as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting field names through first row
        fields = next(csvreader)

        # extracting each data row one by one
        for row in csvreader:
            rows.append(row)

    # transpose the list
    lengths = list(map(list, zip(*rows)))

    # convert to floats
    result = list(map(lambda x: float(x.replace(",", "")), lengths[4]))

    # find min, max and mean value
    min_thickness = min(result, key=float)
    max_thickness = max(result, key=float)
    mean_thickness = sum(result) / len(result)
    median_thickness = median(result)

    # region resolution in map units
    region = gs.region()

    if resolutiondir == "N-S":
        resolution = region.nsres
    else:
        resolution = region.ewres

    # thickness in pixels
    min_thickness_pixel = min_thickness / resolution
    max_thickness_pixel = max_thickness / resolution
    mean_thickness_pixel = mean_thickness / resolution
    median_thickness_pixel = median_thickness / resolution

    gs.message(
        _(
            "Thickness in map units:\nminimum = {0}\nmaximun = {1}\nmean    = {2}\nmedian  = {3}\n\n"
        ).format(min_thickness, max_thickness, mean_thickness, median_thickness)
    )
    gs.message(
        _(
            "Thickness in pixels:\nminimum = {0:.4f}\nmaximum = {1:.4f}\nmean   = {2:.4f}\nmedian = {3:.4f}"
        ).format(
            min_thickness_pixel,
            max_thickness_pixel,
            mean_thickness_pixel,
            median_thickness_pixel,
        )
    )

    # If the maximum thickness is equal to the expected maximum size print a warning
    if max_thickness >= tsize:
        gs.warning(
            _(
                "The maximum thickness {0} is larger or equal to the imput "
                "expected maximum size {1}. I.e., the border of the largest "
                "object has not been reached. Increase the expected maximum "
                "size value."
            ).format(str(max_thickness), str(tsize))
        )

    # copy the maps if the user has provided a name
    if rmedian:
        gs.run_command(
            "g.copy",
            raster="{inmap},{outmap}".format(inmap=categorymap_thin, outmap=rmedian),
            quiet=True,
        )
    if vcategories:
        gs.run_command(
            "g.copy",
            vector="{inmap},{outmap}".format(inmap=categorymap, outmap=vcategories),
            quiet=True,
        )
        gs.run_command(
            "v.db.dropcolumn", map=vcategories, columns=["value"], quiet=True
        )
        gs.run_command(
            "v.to.db",
            map=vcategories,
            option="area",
            columns="area",
            quiet=True,
        )

        def table_exists(table_name):
            tables = gs.read_command("db.tables", flags="p").splitlines()
            return table_name in tables

        # Create temporary table name
        temp_table = create_unique_name("tmp")
        DBTABLE.append(temp_table)

        # Create table with statistics
        sqlstat1 = (
            f"CREATE TABLE {temp_table} ("
            f"b_cat INTEGER PRIMARY KEY, "
            f"avg_width DOUBLE PRECISION, "
            f"min_width DOUBLE PRECISION, "
            f"max_width DOUBLE PRECISION);"
        )
        sqlstat2 = (
            f"INSERT INTO {temp_table} "
            f"(b_cat, avg_width, min_width, max_width) "
            f"SELECT b_cat, "
            f"AVG(length), "
            f"MIN(length), "
            f"MAX(length) "
            f"FROM {categorymap_transects_inside} "
            f"GROUP BY b_cat;"
        )
        gs.run_command("db.execute", sql=sqlstat1)
        gs.run_command("db.execute", sql=sqlstat2)

        # Link statistics to attribute table
        gs.run_command(
            "v.db.join",
            map=vcategories,
            column="cat",
            other_table=temp_table,
            other_column="b_cat",
        )
        gs.run_command(
            "v.colors",
            map=vcategories,
            use="attr",
            column="avg_width",
            color="bgyr",
            quiet=True,
        )

    if vmedian:
        gs.run_command(
            "g.copy",
            vector="{inmap},{outmap}".format(inmap=categorymap_thin, outmap=vmedian),
            quiet=True,
        )
        gs.run_command(
            "v.db.dropcolumn", map=vmedian, columns=["label", "value"], quiet=True
        )
        gs.run_command(
            "v.to.db",
            map=vmedian,
            option="length",
            columns="length",
            quiet=True,
        )

    if transects:
        gs.run_command(
            "g.copy",
            vector="{inmap},{outmap}".format(
                inmap=categorymap_transects, outmap=transects
            ),
            quiet=True,
        )
    if itransects:
        gs.run_command(
            "g.copy",
            vector="{inmap},{outmap}".format(
                inmap=categorymap_transects_inside, outmap=itransects
            ),
            quiet=True,
        )
        gs.run_command(
            "v.colors",
            map=itransects,
            use="attr",
            column="length",
            color="bgyr",
            quiet=True,
        )
    if csv_file_out:
        gs.run_command(
            "v.out.ogr",
            input=categorymap_transects_inside,
            output=csv_file_out,
            format="CSV",
            quiet=True,
        )

    # remove temporary csv_file
    os.remove(csv_file)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    main()
