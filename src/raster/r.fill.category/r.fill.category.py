#!/usr/bin/env python
#
############################################################################
#
# MODULE:    r.fill.category
# AUTHOR(S): Stefano Gobbi and Paolo Zatelli
# PURPOSE:   Replaces the values of pixels of a given category with values
#            of the surrounding pixels
#
# COPYRIGHT: (C) 2019 by Stefano Gobbi and Paolo Zatelli
#
#   This program is free software under the GNU General Public
#   License (>=v2). Read the file COPYING that comes with GRASS
#   for details.
#
#############################################################################
# %Module
# % description: Replaces the values of pixels of a given category with values of the surrounding pixels.
# % keyword: raster
# % keyword: algebra
# % keyword: category
# %end
# %flag
# % key: k
# % description: Keep intermediate maps
# %end
# %option G_OPT_R_INPUT
# %end
# %option G_OPT_R_OUTPUT
# %end
# %option
# % key: category
# % type: integer
# % required: yes
# % multiple: no
# % description: Category to replace
# %end
# %option
# % key: nsize
# % type: integer
# % required: no
# % multiple: no
# % description: Neighborhood size in pixel
# % answer: 19
# % guisection: Parameters
# %end
# %option
# % key: maxiter
# % type: integer
# % required: no
# % multiple: no
# % description: Maximum number of iterations
# % answer: 100
# % options: 1-999
# % guisection: Parameters
# %end
# %option G_OPT_F_OUTPUT
# % key: animationfile
# % description: Name for animation output file
# % required: no
# % guisection: Optional
# %end
# %option
# % key: quality
# % type: integer
# % required: no
# % multiple: no
# % description: Quality factor for animation (1 = highest quality, lowest compression)
# % answer: 3
# % options: 1-5
# % guisection: Optional
# %end

import sys
import os
import atexit

import grass.script as gscript
from grass.exceptions import CalledModuleError

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))


def main():
    options, flags = gscript.parser()

    keep = flags["k"]
    input = options["input"]
    output = options["output"]
    category = int(options["category"])

    nsize = int(options["nsize"])
    maxiter = int(options["maxiter"])
    animationfile = options["animationfile"]
    quality = int(options["quality"])

    overwrite_flag = ""
    if gscript.overwrite():
        overwrite_flag = "t"

    # keep intermediate maps
    keepintmaps = False
    if flags["k"]:
        keepintmaps = True

    # to generate the animation file, intermediate files must be kept
    # they will be removed at the end of the process if the 'k' flag is not set
    if animationfile:
        keepintmaps = True

    # check if input file exists
    if not gscript.find_file(input)["file"]:
        gscript.fatal(_("Raster map <%s> not found") % input)

    # strip mapset name
    in_name_strip = options["input"].split("@")
    in_name = in_name_strip[0]
    out_name_strip = options["output"].split("@")
    out_name = out_name_strip[0]

    tmp = str(os.getpid())

    # maps to bootstrap the loop
    # create a map containing only the category to replace and NULL
    categorymap = "{}".format(in_name) + "_bin_" + "{}".format(tmp)
    gscript.verbose(_("Category map: <%s>") % categorymap)
    gscript.run_command(
        "r.mapcalc",
        expression="{outmap}=if({inmap}=={cat}, 1, null())".format(
            outmap=categorymap, inmap=input, cat=category
        ),
        quiet=True,
        overwrite="t",
    )
    # create a copy of the input map to be used as a selection map in r.neighbors,
    # it will be replaced by the map with category replacement in the loop
    stepmap_old = "{}".format(in_name) + "_step_000"
    gscript.run_command(
        "g.copy",
        raster="{inmap},{outmap}".format(inmap=input, outmap=stepmap_old),
        quiet=True,
        overwrite="t",
    )

    gscript.verbose(_("Category to remove: %d") % category)
    gscript.verbose(_("Maxiter: %d") % maxiter)
    gscript.verbose(_("Quality for animation: %d") % quality)

    pixel_num = 1
    iteration = 1

    # iterate until no pixel of the category to be replaced is left
    # or the maximum number of iterations is reached
    while (pixel_num > 0) and (iteration <= maxiter):
        stepmap = "{}".format(in_name)
        stepmap += "_step_"
        stepmap += "{:03d}".format(iteration)
        gscript.verbose(_("Step map: <%s>") % stepmap)

        # substitute pixels of the category to remove with the mode of the surrounding pixels
        gscript.run_command(
            "r.neighbors",
            input=stepmap_old,
            selection=categorymap,
            size=nsize,
            output=stepmap,
            method="mode",
            overwrite="true",
            quiet=True,
        )

        # remove intermediate map unless the k flag is set
        if keepintmaps is False:
            gscript.run_command(
                "g.remove", type="raster", name=stepmap_old, flags="f", quiet=True
            )

        # the r.neighbors output map is the input map for the next step
        stepmap_old = stepmap

        # create the new map containing only the category to replace and NULL
        gscript.run_command(
            "r.mapcalc",
            expression="{outmap}=if({inmap}=={cat},1,null())".format(
                outmap=categorymap, inmap=stepmap, cat=category
            ),
            quiet=True,
            overwrite="t",
        )

        # evaluate the number of the remaining pixels of the category to relace
        pixel_stat = gscript.parse_command(
            "r.stats",
            input="{inmap}".format(inmap=stepmap),
            flags="c",
            sep="=",
            quiet=True,
        )
        # parse the output, if the category is not in the list raise an exception and set pixel_num = 0
        try:
            pixel_num = float(pixel_stat["{}".format(category)])
        except KeyError as e:
            pixel_num = 0
            # print(e.message)

        gscript.verbose(
            _("Iteration: %d  Remaining pixels: %d") % (iteration, pixel_num)
        )

        iteration = iteration + 1

    # the last value stopped the loop
    iteration = iteration - 1

    # if the loop ended before reaching pixel_num=0
    if pixel_num > 0:
        gscript.warning(
            _(
                "the process stopped after %d iterations with %d pixels of category %d left"
            )
            % (iteration, pixel_num, category)
        )

    # copy the output of the last iteration to the output map
    gscript.run_command(
        "g.copy",
        raster="{inmap},{outmap}".format(inmap=stepmap, outmap=out_name),
        overwrite="{}".format(overwrite_flag),
        quiet=True,
    )

    # remove the last intermediate map unless the k flag is set
    if keepintmaps is False:
        gscript.run_command(
            "g.remove", type="raster", name=stepmap_old, flags="f", quiet=True
        )

    gscript.run_command(
        "g.remove", type="raster", name=categorymap, flags="f", quiet=True
    )

    # optionally create an mpeg animation of the replacement sequence
    if animationfile:
        gscript.message(_("Generating mpeg file %s...") % animationfile)
        gscript.run_command(
            "r.out.mpeg",
            view1="{}_step_[0-9][0-9][0-9]".format(in_name),
            output="{}".format(animationfile),
            quality="{}".format(quality),
            overwrite="{}".format(overwrite_flag),
        )

    # remove intermediate maps if they have been kept for generating the animation
    # but the 'k' flag is not set
    if animationfile and not flags["k"]:
        gscript.message(
            _("Removing intermediate files after generating %s...") % animationfile
        )
        newiter = 0
        while newiter <= iteration:
            stepmap = "{}".format(in_name)
            stepmap += "_step_"
            stepmap += "{:03d}".format(newiter)
            gscript.verbose(_("Removing step map: <%s>") % stepmap)
            gscript.run_command(
                "g.remove", type="raster", name=stepmap, flags="f", quiet=True
            )
            newiter = newiter + 1


if __name__ == "__main__":
    options, flags = gscript.parser()
    # atexit.register(cleanup)
    main()
