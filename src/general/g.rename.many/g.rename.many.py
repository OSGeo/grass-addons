#!/usr/bin/env python

############################################################################
#
# MODULE:       g.rename.many
# AUTHOR(S):    Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:      Rename multiple maps using g.rename
# COPYRIGHT:    (C) 2014-2015 by the authors above, and the GRASS Development Team
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

# %module
# % description: Renames multiple maps in the current mapset.
# % keyword: general
# % keyword: map management
# % keyword: rename
# %end

# %option G_OPT_F_INPUT
# % key: raster
# % required: no
# % multiple: no
# % label: File with rasters to be renamed
# % description: Format of the file is one raster map per line. Old name first, new name second (separated by comma by default)
# % guisection: Raster
# %end

# %option G_OPT_F_INPUT
# % key: raster_3d
# % required: no
# % multiple: no
# % label: File with 3D rasters to be renamed
# % description: Format of the file is one raster map per line. Old name first, new name second (separated by comma by default)
# % guisection: Raster
# %end

# %option G_OPT_F_INPUT
# % key: vector
# % required: no
# % multiple: no
# % label: File with vectors to be renamed
# % description: Format of the file is one vector map per line. Old name first, new name second (separated by comma by default)
# % guisection: Vector
# %end

# %option G_OPT_F_SEP
# % answer: comma
# %end

# %flag
# % key: s
# % label: Skip file format and map existence checks
# % description: By default a file format check is performed and existence of map is checked before the actual renaming. This requires going through each file two times. It might be advantageous to disable the checks for renames of large number of maps. However, when this flag is used an error occurs, some maps might be renamed while some others not.
# %end

# %flag
# % key: d
# % label: Do the checks only (dry run)
# % description: This will only perform the file format and map existence checks but it will not do the actual rename. This is useful when writing the file with renames.
# %end

# %rules
# % required: raster,raster_3d,vector
# % exclusive: -s,-d
# %end


from grass.script.utils import parse_key_val, separator
from grass.script import core as gcore
from grass.script.core import start_command, read_command, PIPE

# TODO: move some functions to the library if they prove useful
# TODO: create tests for error cases and dry run
# TODO: support text delimiter in CSV at least in some basic way
# TODO: add other elements such as group if needed


# there is a same function in gunittest.gutils
def get_current_mapset():
    """Get curret mapset name as a string"""
    return read_command("g.mapset", flags="p").strip()


# there is a similar function in gunittest.gutils but this one is general
# in fact, this works for any element/file in GRASS Database but
# it's better to keep it focused on maps, find_file is the general function
# TODO: should this support names with a Mapset?
def map_exists(name, type, mapset=None):
    """Check if map exists

    :param name: name of the map (without a Mapset)
    :param type: data type ('raster', 'raster_3d', and 'vector')
    :param mapset: Mapset (you can use dot to refer to the current Mapset)
    """
    # change type to element used by find file
    # otherwise, we are not checking the input,
    # so anything accepted by g.findfile will work
    # also supporting both short and full names
    # but this can change in the
    # future (this function documentation is clear about what's legal)
    if type == "raster" or type == "rast":
        type = "cell"
    elif type == "raster_3d" or type == "rast3d" or type == "raster3d":
        type = "grid3"
    elif type == "vect":
        type = "vector"

    extra_params = {}
    if mapset:
        if mapset == ".":
            mapset = get_current_mapset()
        extra_params.update({"mapset": mapset})

    # g.findfile returns non-zero when file was not found
    # so we ignore return code and just focus on stdout
    process = start_command(
        "g.findfile",
        flags="n",
        element=type,
        file=name,
        mapset=mapset,
        stdout=PIPE,
        stderr=PIPE,
        **extra_params,
    )
    output, errors = process.communicate()
    info = parse_key_val(output)
    # file is the key questioned in grass.script.core find_file()
    # return code should be equivalent to checking the output
    # g.findfile returns non-zero when nothing found but scripts are used to
    # check the output, so it is unclear what should be or is the actual
    # g.findfile interface
    # see also #2475 for discussion about types/files
    if info["file"]:
        return True
    else:
        return False


def check_file(filename, map_type, sep):
    with open(filename) as names_file:
        for line in names_file:
            line = line.strip()
            names = line.split(sep)
            if len(names) != 2:
                max_display_chars_for_line = 10
                if len(line) > max_display_chars_for_line:
                    line = line[:max_display_chars_for_line]
                gcore.fatal(
                    _(
                        "Cannot parse line <{line}> using separator"
                        " <{sep}> in file <{file}>. Nothing renamed."
                    ).format(line=line, sep=sep, file=filename)
                )
            if not map_exists(names[0], type=map_type):
                gcore.fatal(
                    _(
                        "Map <{name}> (type <{type}>) does not exist"
                        " in the current Mapset."
                        " Nothing renamed. Note that maps in other Mapsets cannot"
                        " be renamed, however they can be copied."
                    ).format(name=names[0], type=map_type)
                )
            if not gcore.overwrite() and map_exists(names[1], type=map_type):
                gcore.fatal(
                    _(
                        "Map <{name}> (type <{type}>) already exists."
                        " Nothing renamed."
                        " Use overwrite flag if you want to overwrite"
                        " the existing maps."
                    ).format(name=names[0], type=map_type)
                )


def rename_from_file(filename, map_type, sep, safe_input):
    with open(filename) as rasters_file:
        for line in rasters_file:
            line = line.strip()
            names = line.split(sep)
            if not safe_input:
                if len(names) != 2:
                    # we have to fatal here in any case because wrong separator
                    # would just cause warning for each line which can be too
                    # much for a long file
                    gcore.fatal(
                        _(
                            "Cannot parse line <{line}> using separator"
                            " <{sep}> in file <{file}>"
                        ).format(line=line, sep=sep, file=filename)
                    )
            # g.rename currently only warns when map does not exist
            # so we don't need to do anything special here in any case
            gcore.run_command("g.rename", **{map_type: names})


def main():
    options, flags = gcore.parser()

    raster = options["raster"]
    raster_3d = options["raster_3d"]
    vector = options["vector"]
    sep = separator(options["separator"])

    perform_pre_checks = not flags["s"]
    dry_run = flags["d"]

    if perform_pre_checks:
        if raster:
            check_file(raster, "raster", sep=sep)
        if raster_3d:
            check_file(raster_3d, "raster_3d", sep=sep)
        if vector:
            check_file(vector, "vector", sep=sep)

    if dry_run:
        gcore.message(_("Checks successful"))
        return

    if raster:
        rename_from_file(
            filename=raster, map_type="raster", sep=sep, safe_input=perform_pre_checks
        )
    if raster_3d:
        rename_from_file(
            filename=raster_3d,
            map_type="raster_3d",
            sep=sep,
            safe_input=perform_pre_checks,
        )
    if vector:
        rename_from_file(
            filename=vector, map_type="vector", sep=sep, safe_input=perform_pre_checks
        )


if __name__ == "__main__":
    main()
