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
#%Module
#% description: Evaluates minimum, maximum and mean thickness of objects of a given category on a raster map.
#% keyword: raster
#% keyword: algebra
#% keyword: size
#% keyword: clumps
#%end
#%option G_OPT_R_INPUT
#%end
#%option
#% key: category
#% type: integer
#% required: yes
#% multiple: no
#% description: Category to evaluate
#%end
#%option
#% key: tsize
#% type: double
#% required: yes
#% multiple: no
#% description: Expected maximum size in map units
#% answer: 100
#%end
#%option
#% key: tspace
#% type: double
#% required: yes
#% multiple: no
#% description: Transect spacing in map units
#% answer: 2
#%end
#%option
#% key: resolutiondir
#% type: string
#% description: Resolution for output in pixels
#% required: yes
#% options: N-S,E-W
#% answer: N-S
#%end
#%option G_OPT_R_OUTPUT
#% key: rmedian
#% description: Raster map of median lines
#% required: no
#% guisection: Optional
#%end
#%option G_OPT_V_OUTPUT
#% key: vmedian
#% description: Vector map of median lines
#% required: no
#% guisection: Optional
#%end
#%option G_OPT_V_OUTPUT
#% key: transects
#% description: Vector map of complete transects
#% required: no
#% guisection: Optional
#%end
#%option G_OPT_V_OUTPUT
#% key: itransects
#% description: Vector map of inner transects
#% required: no
#% guisection: Optional
#%end
#%option G_OPT_F_OUTPUT
#% key: csvfilename
#% description: CSV output file
#% required: no
#% guisection: Optional
#%end


import sys
import os
import atexit
import csv

import grass.script as gscript
from grass.exceptions import CalledModuleError

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))


def main():
    options, flags = gscript.parser()

    # required input
    input = options["input"]
    category = int(options["category"])
    tsize = float(options["tsize"])
    tspace = float(options["tspace"])

    # optional output
    rmedian = options["rmedian"]
    vmedian = options["vmedian"]
    transects = options["transects"]
    itransects = options["itransects"]
    csv_file_out = options["csvfilename"]
    resolutiondir = options["resolutiondir"]

    overwrite_flag = ""
    if gscript.overwrite():
        overwrite_flag = "t"

    # check if v.transects is installed
    if not gscript.find_program("v.transects", "--help"):
        message = _("You need to install the addon v.transects to be able")
        message += _(" to run r.object.thickness.\n")
        message += _(" You can install the addon with 'g.extension v.transects'")
        gscript.fatal(message)

    # check if input file exists
    if not gscript.find_file(input)["file"]:
        gscript.fatal(_("Raster map <%s> not found") % input)

    # strip mapset name
    in_name_strip = options["input"].split("@")
    in_name = in_name_strip[0]

    tmp = str(os.getpid())

    # create a map containing only the category to replace and NULL
    categorymap = "{}".format(in_name) + "_bin_" + "{}".format(tmp)
    gscript.verbose(_("Category map: <%s>") % categorymap)
    gscript.verbose(_("Extracting category: <%d>") % category)

    gscript.run_command(
        "r.mapcalc",
        expression="{outmap}=if({inmap}=={cat}, 1, null())".format(
            outmap=categorymap, inmap=input, cat=category
        ),
        quiet=True,
        overwrite="t",
    )

    # create a map containing midlines for each clump
    gscript.verbose(_("Finding median lines"))
    categorymap_thin = "{}".format(categorymap) + "_thin"
    gscript.run_command(
        "r.thin", input=categorymap, output=categorymap_thin, quiet=True, overwrite="t"
    )

    # convert to vector
    gscript.verbose(_("Creating vector map of median lines"))
    gscript.run_command(
        "r.to.vect",
        input=categorymap_thin,
        output=categorymap_thin,
        type="line",
        quiet=True,
        overwrite="t",
    )

    # create transects
    # half size (left and right) of the transect, must be larger than the larger expected hslf size of objects
    dsize = tsize / 2
    categorymap_transects = "{}".format(categorymap) + "_transects"
    gscript.verbose(_("Creating transects"))
    gscript.run_command(
        "v.transects",
        input=categorymap_thin,
        output=categorymap_transects,
        transect_spacing=tspace,
        dleft=dsize,
        dright=dsize,
        quiet=True,
        overwrite="t",
    )

    # clip transects with the clumps
    # convert binarymap to vector
    gscript.verbose(_("Creating vector area map"))
    gscript.run_command(
        "r.to.vect",
        input=categorymap,
        output=categorymap,
        type="area",
        quiet=True,
        overwrite="t",
    )

    # drop unneeded column "label" from the table
    gscript.run_command(
        "v.db.dropcolumn", map=categorymap, columns="label", quiet=True, overwrite="t"
    )

    # clip transects with object
    categorymap_transects_inside = "{}".format(categorymap) + "_transects_inside"
    gscript.verbose(_("Clipping transects"))
    # exit if no transect has been created
    try:
        testrun = gscript.run_command(
            "v.overlay",
            ainput=categorymap_transects,
            binput=categorymap,
            output=categorymap_transects_inside,
            operator="and",
            quiet=True,
            overwrite="t",
        )
    except CalledModuleError:
        # cleanup
        # raster
        temp_raster_maps = [categorymap, categorymap_thin]
        for temp_map in temp_raster_maps:
            gscript.run_command(
                "g.remove", type="raster", name=temp_map, flags="f", quiet=True
            )
        # vector
        temp_vector_maps = [categorymap, categorymap_thin, categorymap_transects]
        for temp_map in temp_vector_maps:
            gscript.run_command(
                "g.remove", type="vector", name=temp_map, flags="f", quiet=True
            )

        message = _("No transects created:")
        message += _(" lower transects spacing.")
        gscript.fatal(message)

    # add a column for the transects length
    gscript.verbose(_("Evaluating transects lengths"))
    gscript.run_command(
        "v.db.addcolumn",
        map=categorymap_transects_inside,
        columns="length double",
        quiet=True,
        overwrite="t",
    )
    # upload transects' lengths
    gscript.run_command(
        "v.to.db",
        map=categorymap_transects_inside,
        option="length",
        columns="length",
        quiet=True,
        overwrite="t",
    )

    # CSV manipulation
    # create csv file
    csv_file = "./" + "{}".format(categorymap_transects_inside) + ".csv"

    gscript.verbose(_("Creating CSV file"))
    gscript.run_command(
        "v.out.ogr",
        input=categorymap_transects_inside,
        output=csv_file,
        format="CSV",
        quiet=True,
        overwrite="t",
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

    # region resolution in map units
    region = gscript.region()

    if resolutiondir == "N-S":
        resolution = region.nsres
    else:
        resolution = region.ewres

    # thickness in pixels
    min_thickness_pixel = min_thickness / resolution
    max_thickness_pixel = max_thickness / resolution
    mean_thickness_pixel = mean_thickness / resolution

    gscript.message(
        _("Thickness in map units: min %f  max %f  mean %f")
        % (min_thickness, max_thickness, mean_thickness)
    )
    gscript.message(
        _("Thickness in pixels: min %f  max %f  mean %f")
        % (min_thickness_pixel, max_thickness_pixel, mean_thickness_pixel)
    )

    # If the maximum thickness is equal to the expected maximum size print a warning
    if max_thickness >= tsize:
        message = _(
            "maximum thickness %f is larger or equal to the imput expected maximum size %f:"
            % (max_thickness, tsize)
        )
        message += _(
            " the border of the largest object has not been reached, rise the expected maximum size value."
        )
        gscript.warning(message)

    # copy the maps if the user has provided a name
    if rmedian:
        gscript.run_command(
            "g.copy",
            raster="{inmap},{outmap}".format(inmap=categorymap_thin, outmap=rmedian),
            overwrite="{}".format(overwrite_flag),
            quiet=True,
        )
    if vmedian:
        gscript.run_command(
            "g.copy",
            vector="{inmap},{outmap}".format(inmap=categorymap_thin, outmap=vmedian),
            overwrite="{}".format(overwrite_flag),
            quiet=True,
        )
    if transects:
        gscript.run_command(
            "g.copy",
            vector="{inmap},{outmap}".format(
                inmap=categorymap_transects, outmap=transects
            ),
            overwrite="{}".format(overwrite_flag),
            quiet=True,
        )
    if itransects:
        gscript.run_command(
            "g.copy",
            vector="{inmap},{outmap}".format(
                inmap=categorymap_transects_inside, outmap=itransects
            ),
            overwrite="{}".format(overwrite_flag),
            quiet=True,
        )
    if csv_file_out:
        gscript.run_command(
            "v.out.ogr",
            input=categorymap_transects_inside,
            output=csv_file_out,
            format="CSV",
            quiet=True,
            overwrite="t",
        )

    # cleanup
    # raster
    temp_raster_maps = [categorymap, categorymap_thin]
    for temp_map in temp_raster_maps:
        gscript.run_command(
            "g.remove", type="raster", name=temp_map, flags="f", quiet=True
        )
    # vector
    temp_vector_maps = [
        categorymap,
        categorymap_thin,
        categorymap_transects,
        categorymap_transects_inside,
    ]
    for temp_map in temp_vector_maps:
        gscript.run_command(
            "g.remove", type="vector", name=temp_map, flags="f", quiet=True
        )

    # remove temporary csv_file
    os.remove(csv_file)


if __name__ == "__main__":

    options, flags = gscript.parser()
    # atexit.register(cleanup)
    main()
