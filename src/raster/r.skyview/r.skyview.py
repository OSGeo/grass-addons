#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       r.skyview
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#               Vaclav Petras <wenzeslaus gmail com> (colorize addition)
#
# PURPOSE:      Implementation of Sky-View Factor visualization technique
#
# COPYRIGHT:    (C) 2013-2020 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (version 2). Read the file COPYING that comes with GRASS
# 		for details.
#
##############################################################################

# %module
# % description: Computes skyview factor visualization technique.
# % keyword: raster
# % keyword: visualization
# %end
# %option G_OPT_R_INPUT
# %end
# %option G_OPT_R_OUTPUT
# %end
# %option
# % key: ndir
# % description: Number of directions (8 to 32 recommended)
# % type: integer
# % required: yes
# % answer: 16
# % options: 2-360
# %end
# %option
# % key: maxdistance
# % description: The maximum distance to consider when finding the horizon height
# % type: double
# % required: no
# %end
# %option
# % key: color_source
# % type: string
# % label: Source raster for colorization
# % description: Input and color_input are taken from input and color_input options respectively. The rest is computed using r.slope.aspect
# % descriptions: input; use the raster from the input option;color_input;use the raster from the color_input option;slope;compute and use slope;aspect;compute and use aspect;dxy;compute and use second order partial derivative dxy
# % multiple: no
# % required: no
# % options: input, color_input, slope, aspect, dxy
# % answer: input
# % guisection: Colorize
# %end
# %option G_OPT_R_INPUT
# % key: color_input
# % required: no
# % description: Custom raster map to be used for colorization
# % guisection: Colorize
# %end
# %option
# % key: color_table
# % type: string
# % label: Color table for colorization raster (preset color table by default)
# % description: If empty, the color table of the created raster is used (not used at all for input and color_input)
# % multiple: no
# % required: no
# % options: reds, blues, greens, oranges, sepia, aspectcolr
# % guisection: Colorize
# %end
# %option G_OPT_R_OUTPUT
# % key: colorized_output
# % required: no
# % description: Colorized sky-view factor
# % guisection: Colorize
# %end
# %option
# %  key: basename
# %  type: string
# %  multiple: no
# %  description: Set the basename for the intermediate maps
# %end
# %flag
# % key: o
# % label: Compute openness instead of skyview factor
# % description: Openness considers zenith angles > 90 degrees
# %end
# %flag
# % key: n
# % label: Invert color table for colorization raster
# % description: Ignored for input and color_input
# % guisection: Colorize
# %end


import sys
import os
import atexit

from grass.exceptions import CalledModuleError
import grass.script.core as gcore
import grass.script.raster as grast
from grass.pygrass.messages import get_msgr


# TODO: also used for r.slope.aspect result
TMP_NAME = "tmp_horizon_" + str(os.getpid())
CLEANUP = True


def cleanup():
    if CLEANUP:
        gcore.verbose(_("Cleaning temporary maps..."))
        gcore.run_command(
            "g.remove", flags="f", type="raster", pattern=TMP_NAME + "*", quiet=True
        )


def main():
    elev = options["input"]
    output = options["output"]
    n_dir = int(options["ndir"])
    global TMP_NAME, CLEANUP
    if options["basename"]:
        TMP_NAME = options["basename"]
        CLEANUP = False
    colorized_output = options["colorized_output"]
    colorize_color = options["color_table"]
    if colorized_output:
        color_raster_tmp = TMP_NAME + "_color_raster"
    else:
        color_raster_tmp = None
    color_raster_type = options["color_source"]
    color_input = options["color_input"]
    if color_raster_type == "color_input" and not color_input:
        gcore.fatal(_("Provide raster name in color_input option"))
    if color_raster_type != "color_input" and color_input:
        gcore.fatal(
            _(
                "The option color_input is not needed"
                " when not using it as source for color"
            )
        )
    # this would be needed only when no value would allowed
    if not color_raster_type and color_input:
        color_raster_type = "color_input"  # enable for convenience
    if (
        color_raster_type == "aspect"
        and colorize_color
        and colorize_color not in ["default", "aspectcolr"]
    ):
        gcore.warning(
            _(
                "Using possibly inappropriate color table <{}>"
                " for aspect".format(colorize_color)
            )
        )

    horizon_step = 360.0 / n_dir
    msgr = get_msgr()

    # checks if there are already some maps
    old_maps = _get_horizon_maps()
    if old_maps:
        if not gcore.overwrite():
            CLEANUP = False
            msgr.fatal(
                _(
                    "You have to first check overwrite flag or remove"
                    " the following maps:\n"
                    "{names}"
                ).format(names=",".join(old_maps))
            )
        else:
            msgr.warning(
                _("The following maps will be overwritten: {names}").format(
                    names=",".join(old_maps)
                )
            )
    if not gcore.overwrite() and color_raster_tmp:
        check_map_name(color_raster_tmp)
    try:
        params = {}
        if options["maxdistance"]:
            params["maxdistance"] = options["maxdistance"]
        gcore.run_command(
            "r.horizon",
            elevation=elev,
            step=horizon_step,
            output=TMP_NAME,
            flags="d",
            **params
        )

        new_maps = _get_horizon_maps()
        if flags["o"]:
            msgr.message(_("Computing openness ..."))
            expr = "{out} = 1 - (sin({first}) ".format(first=new_maps[0], out=output)
            for horizon in new_maps[1:]:
                expr += "+ sin({name}) ".format(name=horizon)
            expr += ") / {n}.".format(n=len(new_maps))
        else:
            msgr.message(_("Computing skyview factor ..."))
            expr = "{out} = 1 - (sin( if({first} < 0, 0, {first}) ) ".format(
                first=new_maps[0], out=output
            )
            for horizon in new_maps[1:]:
                expr += "+ sin( if({name} < 0, 0, {name}) ) ".format(name=horizon)
            expr += ") / {n}.".format(n=len(new_maps))

        grast.mapcalc(exp=expr)
        gcore.run_command("r.colors", map=output, color="grey")
    except CalledModuleError:
        msgr.fatal(
            _(
                "r.horizon failed to compute horizon elevation "
                "angle maps. Please report this problem to developers."
            )
        )
        return 1
    if colorized_output:
        if color_raster_type == "slope":
            gcore.run_command("r.slope.aspect", elevation=elev, slope=color_raster_tmp)
        elif color_raster_type == "aspect":
            gcore.run_command("r.slope.aspect", elevation=elev, aspect=color_raster_tmp)
        elif color_raster_type == "dxy":
            gcore.run_command("r.slope.aspect", elevation=elev, dxy=color_raster_tmp)
        elif color_raster_type == "color_input":
            color_raster_tmp = color_input
        else:
            color_raster_tmp = elev
        # don't modify user's color table for inputs
        if colorize_color and color_raster_type not in ["input", "color_input"]:
            rcolors_flags = ""
            if flags["n"]:
                rcolors_flags += "n"
            gcore.run_command(
                "r.colors",
                map=color_raster_tmp,
                color=colorize_color,
                flags=rcolors_flags,
            )
        gcore.run_command(
            "r.shade", shade=output, color=color_raster_tmp, output=colorized_output
        )
        grast.raster_history(colorized_output)
    grast.raster_history(output)
    return 0


def _get_horizon_maps():
    return gcore.list_grouped("rast", pattern=TMP_NAME + "*")[gcore.gisenv()["MAPSET"]]


def check_map_name(name):
    # cell means any raster in this context
    # mapset needs to retrieved in very call, ok for here
    if gcore.find_file(name, element="cell", mapset=gcore.gisenv()["MAPSET"])["file"]:
        gcore.fatal(
            _(
                "Raster map <%s> already exists. "
                "Remove the existing map or allow overwrite."
            )
            % name
        )


if __name__ == "__main__":
    options, flags = gcore.parser()
    atexit.register(cleanup)
    sys.exit(main())
