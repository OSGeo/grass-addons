#!/usr/bin/env python
############################################################################
#
# MODULE:       v.centerline
# AUTHOR:       Moritz Lennert
# PURPOSE:      Takes a map of vector lines and creates a new map containing
#               a central line
#
# COPYRIGHT:    (c) 2014 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Creates a central line of a map of lines
# % keyword: vector
# % keyword: lines central
# %end
# %option G_OPT_V_INPUT
# %end
# %option G_OPT_V_OUTPUT
# %end
# %option
# % key: range
# % type: double
# % description: Distance (in map units) of search radius
# % required: no
# %end
# %option
# % key: refline
# % type: integer
# % description: Category of the line to use as initial reference
# % required: no
# %end
# %option
# % key: vertices
# % description: Number of vertices for center line
# % type: integer
# % answer: 20
# % required: no
# %end
# %flag
# % key: t
# % description: Use transversal line algorithm
# %end
# %flag
# % key: m
# % description: Use approximate median instead of mean
# %end

import os
import atexit
import grass.script as grass
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector import geometry as geo

tmp_points_map = None
tmp_line_map = None
tmp_centerpoints_map = None


def cleanup():
    if grass.find_file(tmp_points_map, element="vector")["name"]:
        grass.run_command(
            "g.remove", flags="f", type="vector", name=tmp_points_map, quiet=True
        )
    if grass.find_file(tmp_line_map, element="vector")["name"]:
        grass.run_command(
            "g.remove", flags="f", type="vector", name=tmp_line_map, quiet=True
        )
    if grass.find_file(tmp_cleaned_map, element="vector")["name"]:
        grass.run_command(
            "g.remove", flags="f", type="vector", name=tmp_cleaned_map, quiet=True
        )
    if grass.find_file(tmp_centerpoints_map, element="vector")["name"]:
        grass.run_command(
            "g.remove", flags="f", type="vector", name=tmp_centerpoints_map, quiet=True
        )
    if grass.find_file(tmp_map, element="vector")["name"]:
        grass.run_command(
            "g.remove", flags="f", type="vector", name=tmp_map, quiet=True
        )


def main():

    input = options["input"]
    if options["refline"]:
        refline_cat = int(options["refline"])
    else:
        refline_cat = None
    nb_vertices = int(options["vertices"])
    if options["range"]:
        search_range = float(options["range"])
    else:
        search_range = None
    output = options["output"]
    transversals = flags["t"]
    median = flags["m"]

    global tmp_points_map
    global tmp_centerpoints_map
    global tmp_line_map
    global tmp_cleaned_map
    global tmp_map
    tmp_points_map = "points_map_tmp_%d" % os.getpid()
    tmp_centerpoints_map = "centerpoints_map_tmp_%d" % os.getpid()
    tmp_line_map = "line_map_tmp_%d" % os.getpid()
    tmp_cleaned_map = "cleaned_map_tmp_%d" % os.getpid()
    tmp_map = "generaluse_map_tmp_%d" % os.getpid()

    nb_lines = grass.vector_info_topo(input)["lines"]

    # Find best reference line and max distance between centerpoints of lines
    segment_input = ""
    categories = grass.read_command(
        "v.category", input=input, option="print", quiet=True
    ).splitlines()
    for category in categories:
        segment_input += "P {}".format(category.strip())
        segment_input += " {} {}".format(category.strip(), " 50%")
        segment_input += os.linesep

    grass.write_command(
        "v.segment",
        input=input,
        output=tmp_centerpoints_map,
        rules="-",
        stdin=segment_input,
        quiet=True,
    )

    center_distances = grass.read_command(
        "v.distance",
        from_=tmp_centerpoints_map,
        to=tmp_centerpoints_map,
        upload="dist",
        flags="pa",
        quiet=True,
    ).splitlines()

    cats = []
    mean_dists = []
    count = 0
    distmax = 0
    for center in center_distances:
        if count < 2:
            count += 1
            continue
        cat = center.strip().split("|")[0]
        distsum = 0
        for x in center.strip().split("|")[1:]:
            distsum += float(x)
        mean_dist = distsum / len(center.strip().split("|")[1:])
        cats.append(cat)
        mean_dists.append(mean_dist)

    if transversals and not search_range:
        search_range = sum(mean_dists) / len(mean_dists)
        grass.message(_("Calculated search range:  %.5f." % search_range))

    if not refline_cat:
        refline_cat = sorted(zip(cats, mean_dists), key=lambda tup: tup[1])[0][0]

        grass.message(_("Category number of chosen reference line: %s." % refline_cat))

    # Use transversals algorithm
    if transversals:

        # Break any intersections in the original lines so that
        # they do not interfere further on
        grass.run_command(
            "v.clean", input=input, output=tmp_cleaned_map, tool="break", quiet=True
        )

        xmean = []
        ymean = []
        xmedian = []
        ymedian = []
        step = 100.0 / nb_vertices

        os.environ["GRASS_VERBOSE"] = "-1"

        for vertice in range(0, nb_vertices + 1):
            # v.segment sometimes cannot find points when
            # using 0% or 100% offset
            length_offset = step * vertice
            if length_offset < 0.00001:
                length_offset = 0.00001
            if length_offset > 99.99999:
                length_offset = 99.9999
            # Create endpoints of transversal
            segment_input = "P 1 %s %.5f%% %f\n" % (
                refline_cat,
                length_offset,
                search_range,
            )
            segment_input += "P 2 %s %.5f%% %f\n" % (
                refline_cat,
                length_offset,
                -search_range,
            )
            grass.write_command(
                "v.segment",
                input=input,
                output=tmp_points_map,
                stdin=segment_input,
                overwrite=True,
            )

            # Create transversal
            grass.write_command(
                "v.net",
                points=tmp_points_map,
                output=tmp_line_map,
                operation="arcs",
                file="-",
                stdin="99999 1 2",
                overwrite=True,
            )

            # Patch transversal onto cleaned input lines
            maps = tmp_cleaned_map + "," + tmp_line_map
            grass.run_command("v.patch", input=maps, out=tmp_map, overwrite=True)

            # Find intersections
            grass.run_command(
                "v.clean",
                input=tmp_map,
                out=tmp_line_map,
                tool="break",
                error=tmp_points_map,
                overwrite=True,
            )

            # Add categories to intersection points
            grass.run_command(
                "v.category",
                input=tmp_points_map,
                out=tmp_map,
                op="add",
                overwrite=True,
            )

            # Get coordinates of points
            coords = grass.read_command(
                "v.to.db", map=tmp_map, op="coor", flags="p"
            ).splitlines()

            count = 0
            x = []
            y = []
            for coord in coords:
                x.append(float(coord.strip().split("|")[1]))
                y.append(float(coord.strip().split("|")[2]))

            # Calculate mean and median for this transversal
            if len(x) > 0:
                xmean.append(sum(x) / len(x))
                ymean.append(sum(y) / len(y))

                x.sort()
                y.sort()

                xmedian.append((x[(len(x) - 1) // 2] + x[(len(x)) // 2]) / 2)
                ymedian.append((y[(len(y) - 1) // 2] + y[(len(y)) // 2]) / 2)

        del os.environ["GRASS_VERBOSE"]

    # Use closest point algorithm
    else:

        # Get reference line calculate its length
        grass.run_command(
            "v.extract", input=input, output=tmp_line_map, cats=refline_cat, quiet=True
        )

        os.environ["GRASS_VERBOSE"] = "0"
        lpipe = grass.read_command(
            "v.to.db", map=tmp_line_map, op="length", flags="p"
        ).splitlines()
        del os.environ["GRASS_VERBOSE"]

        for l in lpipe:
            linelength = float(l.strip().split("|")[1])

        step = linelength / nb_vertices

        # Create reference points for vertice calculation
        grass.run_command(
            "v.to.points",
            input=tmp_line_map,
            output=tmp_points_map,
            dmax=step,
            quiet=True,
        )

        nb_points = grass.vector_info_topo(tmp_points_map)["points"]

        cat = []
        x = []
        y = []

        # Get coordinates of closest points on all input lines
        if search_range:
            points = grass.read_command(
                "v.distance",
                from_=tmp_points_map,
                from_layer=2,
                to=input,
                upload="to_x,to_y",
                dmax=search_range,
                flags="pa",
                quiet=True,
            ).splitlines()
        else:
            points = grass.read_command(
                "v.distance",
                from_=tmp_points_map,
                from_layer=2,
                to=input,
                upload="to_x,to_y",
                flags="pa",
                quiet=True,
            ).splitlines()

        firstline = True
        for point in points:
            if firstline:
                firstline = False
                continue
            cat.append((int(point.strip().split("|")[0])))
            x.append(float(point.strip().split("|")[2]))
            y.append(float(point.strip().split("|")[3]))

        # Calculate mean coordinates
        xsum = [0] * nb_points
        ysum = [0] * nb_points
        linecount = [0] * nb_points

        for i in range(len(cat)):
            index = cat[i] - 1
            linecount[index] += 1
            xsum[index] = xsum[index] + x[i]
            ysum[index] = ysum[index] + y[i]

        xmean = [0] * nb_points
        ymean = [0] * nb_points

        for c in range(0, nb_points):
            xmean[c] = xsum[c] / linecount[c]
            ymean[c] = ysum[c] / linecount[c]

        # Calculate the median

        xmedian = [0] * nb_points
        ymedian = [0] * nb_points

        for c in range(0, nb_points):
            xtemp = []
            ytemp = []
            for i in range(len(cat)):
                if cat[i] == c + 1:
                    xtemp.append(x[i])
                    ytemp.append(y[i])
            xtemp.sort()
            ytemp.sort()
            xmedian[c] = (xtemp[(len(xtemp) - 1) // 2] + xtemp[(len(xtemp)) // 2]) / 2
            ymedian[c] = (ytemp[(len(ytemp) - 1) // 2] + ytemp[(len(ytemp)) // 2]) / 2

    # Create new line and write to file
    if median and nb_lines > 2:
        line = geo.Line(list(zip(xmedian, ymedian)))
    else:
        if median and nb_lines <= 2:
            grass.message(_("More than 2 lines necesary for median, using mean."))
        line = geo.Line(list(zip(xmean, ymean)))

    new = VectorTopo(output)
    new.open("w")

    new.write(line)
    new.close()


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
