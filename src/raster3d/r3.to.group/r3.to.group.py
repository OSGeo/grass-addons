#!/usr/bin/env python
#
############################################################################
#
# MODULE:        r3.to.group
# AUTHOR(S):     Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:       Create an imagery group from 3D raster
# COPYRIGHT:     (C) 2016 by Vaclav Petras, and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Convert a 3D raster map to imagery group
# % keyword: raster3d
# % keyword: conversion
# % keyword: raster
# % keyword: imagery
# % keyword: voxel
# % keyword: map management
# %end
# %option G_OPT_R3_INPUT
# %end
# %option G_OPT_I_GROUP
# %end
# %option G_OPT_I_SUBGROUP
# % required: no
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % key: basename
# % required: no
# %end
# %option G_OPT_R_TYPE
# % required: no
# %end
# %option
# % key: multiply
# % type: double
# % required: no
# % label: Value to multiply the raster values with
# % description: Coefficient a in the equation y = ax + b
# %end
# %option
# % key: add
# % type: double
# % required: no
# % label: Value to add to the raster values
# % description: Coefficient b in the equation y = ax + b
# %end
# %flag
# % key: a
# % description: Add to group or subgroup if it already exists
# %end


import grass.script as gs
from grass.exceptions import CalledModuleError


def remove(maps):
    """Remove raster maps"""
    if maps:
        gs.run_command("g.remove", flags="f", quiet=True, type="rast", name=maps)


def list_in_current_mapset(pattern):
    maps = gs.list_pairs(type="rast", mapset=".", pattern=pattern, flag="e")
    maps = [name for name, mapset in maps]
    return maps


def main():
    options, flags = gs.parser()

    input_ = options["input"]
    group = options["group"]
    subgroup = options["subgroup"]
    basename = options["basename"]
    add_to_group = flags["a"]

    # options to be passed to r3.to.rast
    additional_options = {}
    for option in ["type", "multiply", "add"]:
        if options[option]:
            additional_options[option] = options[option]

    if not subgroup:
        subgroup = group
    if not basename:
        basename = group
    basename_sep = "_"
    pattern = "%s%s[0-9]+" % (basename, basename_sep)

    overwrite = gs.overwrite()
    group_exists = gs.find_file(group, element="group")["file"]
    subgroup_exists = gs.find_file(group, element="subgroup")["file"]
    if group_exists and subgroup_exists:
        if not add_to_group:  # and not overwrite:
            gs.fatal(
                _(
                    "Group <%s> and subgroup <%s> exist, use"
                    " different name or -a flag"
                )
                % (group, subgroup)
            )
        # if overwrite:  # not implemented
        # TODO: remove group?
    # when just group exists, i.group should create new subgroup
    rasters = list_in_current_mapset(pattern)
    if not overwrite and rasters:
        if len(rasters) > 3:
            formatted = "%s,..." % ", ".join(rasters[:3])
        else:
            formatted = ", ".join(rasters)
        gs.fatal(
            _(
                "There are rasters with basename <%s> (%s), use"
                " different name or overwrite"
            )
            % (basename, formatted)
        )

    rasters = []
    try:
        gs.run_command(
            "r3.to.rast", input=input_, output=basename, **additional_options
        )
        # it's clear we created just the ones in the current mapset
        # and we need to make the command line as short as possible
        rasters = list_in_current_mapset(pattern)
        gs.run_command("i.group", input=rasters, group=group, subgroup=subgroup)
    except CalledModuleError as error:
        remove(rasters)
        gs.fatal(_("Module %s failed. Check the above error messages.") % error.cmd)


if __name__ == "__main__":
    main()
