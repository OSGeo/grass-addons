#!/usr/bin/env python
#
#########################################################################
#
# MODULE:       v.profile.points
#
# AUTHOR(S):    Vaclav Petras
#
# PURPOSE:      Takes a point map and creates a profile (transect)
#               which is a point map but with x showing distance and y
#               showing height
#
# COPYRIGHT:    (C) 2016 by Vaclav Petras and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#########################################################################

# %module
# % description: Creates a profile (transect) from points
# % keyword: vector
# % keyword: points
# % keyword: profile
# % keyword: transect
# % keyword: lidar
# % keyword: point cloud
# %end
# %option G_OPT_V_INPUT
# % key: line_input
# % required: no
# % label: Vector map with a single line (with 2 points)
# % description: Vector line prepared ahead
# % guisection: Line
# %end
# %option G_OPT_M_COORDS
# % required: no
# % multiple: yes
# % label: Line coordinates (x,y,x,y)
# % description: Two pairs of coordinates as an alternative to a vector line
# % guisection: Line
# %end
# %option G_OPT_V_INPUT
# % key: point_input
# % required: no
# % label: Vector map with points
# % guisection: Points
# %end
# %option G_OPT_F_BIN_INPUT
# % key: file_input
# % required: no
# % label: LAS (or LAZ) file with a point cloud
# % description: File to be imported using v.in.lidar
# % guisection: Points
# %end
# %option G_OPT_V_OUTPUT
# % required: yes
# % guisection: Output
# %end
# %option
# % key: width
# % type: double
# % required: no
# % label: Width of profile in map units
# % description: Default with is 5% of the profile length
# % guisection: Line
# %end
# %flag
# % key: z
# % description: Start the z coordinates at 0 instead of the actual height
# % guisection: Output
# %end
# %rules
# % required: line_input, coordinates
# % exclusive: line_input, coordinates
# % required: point_input, file_input
# % exclusive: point_input, file_input
# %end

# TODO: support more than one line with 2 points
# TODO: shift x coordinates to zero
# TODO: flags to place the result in region or near the input

import sys
import os
import atexit
import uuid

import grass.script as gs


TMP = []


def cleanup():
    if len(TMP):
        gs.info(_("Cleaning %d temporary maps...") % len(TMP))
    for rast in TMP:
        gs.run_command("g.remove", type="vector", name=rast, flags="f", quiet=True)


def create_tmp_map_name(name):
    return "tmp_{mod}_{pid}_{map_}".format(
        mod="v_profile_points", pid=os.getpid(), map_=name
    )


def main():
    options, flags = gs.parser()
    input_line = options["line_input"]
    coords = options["coordinates"]
    input_points = options["point_input"]
    input_file = options["file_input"]
    output = options["output"]
    width = options["width"]
    lidar_flags = ""
    quiet = True
    profile_area_output = None
    profile_points_output = None
    profile_line_output = None

    extra_transform_flags = ""
    if flags["z"]:
        extra_transform_flags = "t"

    atexit.register(cleanup)

    if not profile_area_output:
        profile_area = create_tmp_map_name("profile_area")
        TMP.append(profile_area)
    else:
        profile_area = profile_area_output
    if not profile_points_output:
        profile_points = create_tmp_map_name("profile_points")
        TMP.append(profile_points)
    else:
        profile_points = profile_points_output
    if not input_line:
        if not profile_line_output:
            input_line = create_tmp_map_name("input_line")
            TMP.append(input_line)
        else:
            input_line = profile_line_output
        numbers = coords.split(",")
        if len(numbers) != 4:
            gs.fatal(_("Provide exactly two pairs of coordinates"))
        line_ascii = "L 2 1\n%s %s\n%s %s\n\n1 1\n" % tuple(numbers)
        gs.write_command(
            "v.in.ascii",
            input="-",
            output=input_line,
            format="standard",
            flags="n",
            quiet=quiet,
            stdin=line_ascii,
        )

    text = gs.read_command(
        "v.to.db",
        map=input_line,
        option="azimuth",
        flags="p",
        separator="pipe",
        quiet=quiet,
        errors="exit",
    )
    gs.debug("azimuth: %s" % text.splitlines())
    rotation = float(text.splitlines()[0].split("|")[1])
    # north + cw -> x + ccw (v.to.db ignores line dir)
    rotation = rotation - 90
    gs.debug("rotation: %s" % rotation)

    if width:
        buffer_distance = float(width) / 2
    else:
        text = gs.read_command(
            "v.to.db",
            map=input_line,
            option="azimuth",
            flags="p",
            separator="pipe",
            quiet=quiet,
        )
        length = float(text.splitlines()[0].split("|")[1])
        buffer_distance = 0.025 * length  # width 5% of profile length
        gs.debug("line length: %s" % length)
    gs.debug("buffer: %s" % buffer_distance)
    gs.run_command(
        "v.buffer",
        input=input_line,
        output=profile_area,
        flags="c",
        distance=buffer_distance,
        quiet=quiet,
    )

    # TODO: also limit by region
    if input_file:
        gs.message("Importing...")
        gs.run_command(
            "v.in.lidar",
            input=input_file,
            output=profile_points,
            flags=lidar_flags,
            mask=profile_area,
            quiet=quiet,
            errors="exit",
        )
    else:
        gs.message("Selecting...")
        gs.run_command(
            "v.select",
            ainput=input_points,
            binput=profile_area,
            output=profile_points,
            flags="c",
            quiet=quiet,
        )

    gs.message("Rotating...")
    gs.run_command(
        "v.transform",
        flags="ya" + extra_transform_flags,
        input=profile_points,
        output=output,
        zrotation=rotation,
    )


if __name__ == "__main__":
    sys.exit(main())
