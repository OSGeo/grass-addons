#!/usr/bin/env python

"""
MODULE:    r.windfetch

AUTHOR(S): Anna Petrasova <kratochanna@gmail.com>

PURPOSE:   Computes wind fetch.

COPYRIGHT: (C) 2024 by Anna Petrasova and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

# %module
# % description: Computes wind fetch which is the length of water over which winds blow without obstruction
# % keyword: raster
# % keyword: distance
# % keyword: wind
# %end
# %option G_OPT_R_INPUT
# % label: Name of input land/water land use map
# % description: Binary input where 1 is land and 0 is water
# %end
# %option G_OPT_M_COORDS
# % multiple: yes
# % description: Coordinates for which to compute wind fetch
# %end
# %option G_OPT_V_INPUT
# % key: points
# % multiple: no
# % required: no
# % label: Name of vector points map for fetch computation
# %end
# %option
# % key: step
# % type: integer
# % required: yes
# % multiple: no
# % options: 0-360
# % answer: 15
# % description: Angular step at which to compute wind fetch (0 is East, counterclockwise)
# %end
# %option
# % key: direction
# % type: integer
# % required: yes
# % multiple: no
# % options: 0-359
# % answer: 0
# % description: Direction at which to start calculating fetch.
# %end
# %option
# % key: minor_directions
# % type: integer
# % required: yes
# % multiple: no
# % options: 1-360
# % answer: 5
# % label: Number of minor directions (must be odd number).
# % description: Fetch computed as an average of multiple minor directions around each direction.
# %end
# %option
# % key: minor_step
# % type: integer
# % required: yes
# % multiple: no
# % options: 1-180
# % answer: 3
# % label: Angular step size between minor directions.
# % description: Fetch computed as an average of multiple minor directions around each direction.
# %end
# %option G_OPT_F_OUTPUT
# % key: output_file
# % required: no
# % description: If not given write to standard output
# %end
# %option
# % key: format
# % type: string
# % required: no
# % multiple: no
# % options: csv,json
# % label: Output format
# % descriptions: csv;CSV (Comma Separated Values);json;JSON (JavaScript Object Notation);
# % answer: csv
# %end
# %rules
# % exclusive: coordinates, points
# %end
# %rules
# % required: coordinates, points
# %end


import sys
import atexit
import json
import csv
from io import StringIO

import grass.script as gs


def check_version():
    if gs.version()["version"].split(".")[:2] >= ["8", "4"]:
        return True
    return False


def clean(name):
    gs.run_command("g.remove", type="raster", name=name, flags="f", superquiet=True)


def point_fetch(land, coordinates, direction, step, minor_directions, minor_step):
    gs.verbose(_("Computing distances..."))
    data = gs.read_command(
        "r.horizon",
        elevation=land,
        direction=0,
        coordinates=coordinates,
        step=1,
        format="json",
    )
    gs.verbose(_("Computing wind fetch..."))
    offset = minor_step * (minor_directions - 1) / 2
    output = []
    for point in json.loads(data):
        distances_dict = dict(zip(point["azimuth"], point["horizon_distance"]))
        output.append({"x": point["x"], "y": point["y"], "directions": [], "fetch": []})
        i = 0
        while i < 360:
            # first compute direction and associated minor directions
            real_direction = (i + direction) % 360
            output[-1]["directions"].append(real_direction)
            directions = [
                (real_direction - offset + j * minor_step) % 360
                for j in range(minor_directions)
            ]
            # get distances for minor directions and average them
            distances = [distances_dict[key] for key in directions]
            fetch = sum(distances) / minor_directions
            output[-1]["fetch"].append(fetch)
            # next direction
            i += step
    return output


def main():
    options, flags = gs.parser()

    if check_version():
        gs.fatal(_("r.windfetch requires GRASS GIS version >= 8.4"))

    input_raster = options["input"]
    coordinates = options["coordinates"]
    points_map = options["points"]
    direction = int(options["direction"])
    step = int(options["step"])
    minor_directions = int(options["minor_directions"])
    minor_step = int(options["minor_step"])
    output_file = options["output_file"]
    output_format = options["format"]

    if minor_directions % 2 == 0:
        gs.fatal(_("Number of minor directions should be odd, not even."))
    temporary_raster = gs.append_node_pid("windfetch")
    atexit.register(clean, temporary_raster)
    info = gs.raster_info(input_raster)
    height = int((info["north"] - info["south"]) / 10) + 1
    rules = f"1 = {height}\n* = 0"
    gs.write_command(
        "r.reclass", input=input_raster, output=temporary_raster, stdin=rules, rules="-"
    )
    if points_map:
        point_data = gs.read_command(
            "v.out.ascii",
            input=points_map,
            type="point",
            format="point",
            separator="comma",
        )
        point_data = StringIO(point_data)
        reader = csv.reader(point_data)
        coordinates = ",".join([f"{row[0]},{row[1]}" for row in reader])

    fetch = point_fetch(
        land=temporary_raster,
        coordinates=coordinates,
        direction=direction,
        step=step,
        minor_directions=minor_directions,
        minor_step=minor_step,
    )
    if output_format == "csv":
        text_output = []
        columns = [f"direction_{a}" for a in fetch[0]["directions"]]
        text_output.append(",".join(["x", "y", *columns]))
        for each in fetch:
            item = [each["x"], each["y"], *each["fetch"]]
            text_output.append(",".join([str(i) for i in item]))
        text_output = "\n".join(text_output)
    else:
        text_output = json.dumps(fetch, indent=4)
    if output_file == "" or output_file == "-":
        print(text_output)
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text_output)


if __name__ == "__main__":
    sys.exit(main())
