#!/usr/bin/env python
#
############################################################################
#
# MODULE:        r3.count.categories
# AUTHOR(S):     Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:       Count categories in vertical direction
# COPYRIGHT:     (C) 2016 by Vaclav Petras, and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Count categories in vertical direction
# % keyword: raster3d
# % keyword: conversion
# % keyword: raster
# % keyword: category
# % keyword: voxel
# %end
# %option G_OPT_R3_INPUT
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % required: yes
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % key: slices
# TODO: required: no
# % required: yes
# % label: Basename for horizontal slices of the 3D raster
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
# %option
# % key: size
# % type: integer
# % required: no
# % label: Moving window size
# % description: By default, only the given cell is considered
# %end
# %option G_OPT_R_INPUT
# % key: surface
# % required: no
# % description: Count only those cells which are under the surface (in cells)
# %end
# %flag
# % key: d
# % description: Divide count by the number of cells in the surface
# %end
# %flag
# % key: s
# % label: Expect the slices to be already present
# % description: When running the module over and over, this saves the slicing 3D raster step
# %end
# %rules
# % exclusive: size, surface
# %end


import grass.script as gs
from grass.exceptions import CalledModuleError


def check_raster3d_exists(name):
    """Check if the raster map exists, call GRASS fatal otherwise"""
    file_info = gs.find_file(name, element="grid3")
    if not file_info["fullname"]:
        gs.fatal(_("3D raster map <%s> not found") % name)


def check_raster2d_exists(name):
    """Check if the raster map exists, call GRASS fatal otherwise"""
    file_info = gs.find_file(name, element="cell")
    if not file_info["fullname"]:
        gs.fatal(_("2D raster map <%s> not found") % name)


def remove(maps):
    """Remove raster maps"""
    if maps:
        gs.run_command("g.remove", flags="f", quiet=True, type="rast", name=maps)


def list_in_current_mapset(pattern):
    """List names of raster maps in the current mapset"""
    maps = gs.list_pairs(type="rast", mapset=".", pattern=pattern, flag="e")
    maps = [name for name, mapset in maps]
    return maps


def basename_in_use_message(basename, rasters):
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


# TODO: create name for slices if not provided
def create_tmp_map_name(name):
    return "{mod}_{pid}_{map_}_tmp".format(mod="r3_reduce", pid=os.getpid(), map_=name)


def main():
    options, flags = gs.parser()

    # TODO: allow using existing slices with a flag
    input_ = options["input"]
    output_basename = options["output"]
    slices_basename = options["slices"]
    surface = options["surface"]

    divide = flags["d"]
    use_slices = flags["s"]

    check_raster3d_exists(input_)
    if surface:
        check_raster2d_exists(surface)

    size = None
    if options["size"]:
        size = int(options["size"])
        if size % 2 == 0:
            gs.fatal(
                _("Please provide an odd number for the moving" " window size, not %d")
                % size
            )

    # options to be passed to r3.to.rast
    additional_options = {}
    for option in ["multiply", "add"]:
        if options[option]:
            additional_options[option] = options[option]
    additional_options["type"] = "CELL"

    basename_sep = "_"
    output_pattern = "^%s%s[0-9]+$" % (output_basename, basename_sep)
    slices_pattern = "^%s%s[0-9]+$" % (slices_basename, basename_sep)
    # TODO: slices test seems to be broken

    overwrite = gs.overwrite()
    rasters = list_in_current_mapset(output_pattern)
    if not overwrite and rasters:
        basename_in_use_message(output_basename, rasters)
    rasters = list_in_current_mapset(slices_pattern)
    if not use_slices and not overwrite and rasters:
        basename_in_use_message(slices_basename, rasters)

    # TODO: list of categories would be better
    info = gs.parse_command("r3.info", map=input_, flags="r")
    map_min = int(float(info["min"]))
    map_max = int(float(info["max"]))
    gs.verbose(_("Categories from %d to %d") % (map_min, map_max))

    rasters = []
    try:
        # TODO: we should switch to 3D region for the following computations?
        # or should we require resolutions to be the same?
        if not use_slices:
            gs.run_command(
                "r3.to.rast", input=input_, output=slices_basename, **additional_options
            )
        # it's clear we created just the ones in the current mapset
        # and we need to make the command line as short as possible
        rasters = list_in_current_mapset(slices_pattern)
        if size:
            base_expr = "int({m}[{a},{b}] == $num)"
            size = int((size - 1) / 2)  # window size to max index
            expr_list = []
            for raster in rasters:
                for j in range(-size, size + 1):
                    for i in range(-size, size + 1):
                        expr_list.append(base_expr.format(m=raster, a=i, b=j))
            expr = " + ".join(expr_list)
            expr = "{out}{sep}$num = {inp}".format(
                out=output_basename, sep=basename_sep, inp=expr
            )
        else:
            if surface:
                # TODO: < or <= ?
                base_expr = "if({d} < {s}, int({m} == $num), 0)"
                expr_list = []
                for depth, raster in enumerate(rasters):
                    expr_list.append(base_expr.format(m=raster, d=depth + 1, s=surface))
                expr = " + ".join(expr_list)
                if divide:
                    expr = "({e}) / {otype}({s})".format(
                        e=expr, otype="float", s=surface
                    )
                expr = "{out}{sep}$num = {inp}".format(
                    out=output_basename, sep=basename_sep, inp=expr
                )
            else:
                expr = "{out}{sep}$num = int({inp} == $num)".format(
                    out=output_basename,
                    sep=basename_sep,
                    inp=" == $num) + int(".join(rasters),
                )
        # TODO: define behavior when the map is empty or has just one class
        try:
            # TODO: this uses uncommitted experimental code for trunk
            from grass.script.parallel import ModuleCallList, execute_by_module

            call = ModuleCallList()
            parallel = True
        except ImportError:
            call = gs  # fall back to grass.script
            parallel = False
        for i in range(map_min, map_max + 1):
            call.mapcalc(expr, num=i)
        if parallel:
            execute_by_module(call, nprocs=4)
    except CalledModuleError as error:
        remove(rasters)
        gs.fatal(_("Module %s failed. Check the above error messages.") % error.cmd)


if __name__ == "__main__":
    main()
