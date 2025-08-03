#!/usr/bin/env python

"""
MODULE:    v.fixed.segmentpoints

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Creates segment points along a vector line with fixed distances
           by using the v.segment module

COPYRIGHT: (C) 2014 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: segment points along a vector line with fixed distances
# % keyword: vector
# % keyword: geometry
# %end

# %option G_OPT_V_INPUT
# % key: vector
# % required: yes
# %end

# %option G_OPT_V_CAT
# % key: cat
# % description: Category of a vector line
# % required: yes
# %end

# %option G_OPT_M_DIR
# % key: dir
# % description: Directory where the output will be found
# % required : yes
# %end

# %option
# % key: prefix
# % type: string
# % key_desc: prefix
# % description: output prefix (must start with a letter)
# % required: yes
# %end

# %option
# % key: distance
# % type: integer
# % key_desc: integer
# % description: fixed distance between segment points
# % required : no
# % answer: 100
# %end

import sys
import os
import math
import grass.script as gs


def main():
    vlines = options["vector"].split("@")[0]
    vcat = options["cat"]
    directory = options["dir"]
    sdistance = options["distance"]
    prefix = options["prefix"]
    voutline = prefix + "_singleline"
    voutpoint = prefix + "_segmentpoints"
    fpointscsv = prefix + "_t_segmentpoints.csv"
    fpointscsv_export = prefix + "_segmentpoints.csv"
    fpoints = prefix + "_segmentpoints.txt"
    global tmp

    # Extract vector line
    gs.message("Extract vector line for which segment points should be calculated ...")
    gs.run_command("v.extract", input=vlines, output=voutline, cats=vcat)
    gs.message("Extraction done.")
    gs.message("----")

    # Calculate vector line length and populate it to the attribute table
    gs.message(
        "Calculate vector line length and populate it to the attribute table ..."
    )
    gs.run_command("v.db.addcolumn", map=voutline, layer=1, columns="vlength double")

    gs.run_command(
        "v.to.db",
        map=voutline,
        option="length",
        layer=1,
        columns="vlength",
        overwrite=True,
    )

    gs.message("Calculate vector line length done.")
    gs.message("----")

    # Read length
    tmp = gs.read_command(
        "v.to.db",
        map=voutline,
        type="line",
        layer=1,
        qlayer=1,
        option="length",
        units="meters",
        column="vlength",
        flags="p",
        quiet=True,
    )
    vector_line_length = float(tmp.split("|")[1])

    # Print vector line length
    gs.message("Vector line length in meter:")
    gs.message(vector_line_length)
    gs.message("----")

    # Calculation number of segment points (start and end point included)
    # number of segment points without end point

    number_segmentpoints_without_end = math.floor(vector_line_length / float(sdistance))

    number_segmentpoints_with_end = int(number_segmentpoints_without_end + 2)

    gs.message("Number of segment points (start and end point included):")
    gs.message(number_segmentpoints_with_end)
    gs.message("----")

    segmentpointsrange_without_end = range(1, number_segmentpoints_with_end, 1)
    max_distancerange = float(sdistance) * number_segmentpoints_with_end
    distancesrange_without_end = range(0, int(max_distancerange), int(sdistance))

    # Write segment point input file for g.segment to G_OPT_M_DIR
    gs.message("Write segment point input file for g.segment ...")
    segment_points_file = os.path.join(directory, fpoints)
    file = open(segment_points_file, "a")
    for f, b in zip(segmentpointsrange_without_end, distancesrange_without_end):
        file.write("P %s %s %s\n" % (f, vcat, b))
    file.close()

    file = open(segment_points_file, "a")
    file.write("P %s %s -0" % (number_segmentpoints_with_end, vcat))
    file.close()

    # Give information where output file
    gs.message("Segment points file:")
    gs.message(segment_points_file)
    gs.message("----")

    # Run v.segment with the segment point input
    gs.message("Run v.segment ...")
    gs.run_command(
        "v.segment", input=voutline, output=voutpoint, rules=segment_points_file
    )

    gs.run_command("v.db.addtable", map=voutpoint)
    gs.message("v.segment done.")
    gs.message("----")

    # Adding coordinates to segment points attribute table.
    gs.message("Adding coordinates to segment points attribute table ...")

    gs.run_command(
        "v.db.addcolumn", map=voutpoint, layer=1, columns="xcoor double,ycoor double"
    )

    gs.run_command(
        "v.to.db",
        map=voutpoint,
        option="coor",
        layer=1,
        columns="xcoor,ycoor",
        overwrite=True,
    )

    gs.message("Coordinates added.")
    gs.message("----")

    # join point segment file data to point vector
    gs.message("Join distance information to segment point vector ...")
    segment_points_file_csv = os.path.join(directory, fpointscsv)
    with open("%s" % (segment_points_file), "r") as d:
        with open("%s" % (segment_points_file_csv), "w") as f:
            for line in d:
                new_line = line.replace(" ", ";")
                f.write(new_line)

    gs.run_command(
        "db.in.ogr", output="t_segmentpoints_csv", input="%s" % segment_points_file_csv
    )

    gs.run_command(
        "v.db.join",
        map=voutpoint,
        column="cat",
        otable="t_segmentpoints_csv",
        ocolumn="field_2",
        scolumns="field_2,field_4",
    )

    gs.run_command("db.droptable", table="t_segmentpoints_csv", flags="f")

    gs.run_command(
        "v.db.addcolumn",
        map=voutpoint,
        layer=1,
        columns="cat_2 integer,distance double,cat_line integer",
    )

    gs.run_command("db.execute", sql="UPDATE %s SET cat_2 =  field_2" % (voutpoint))
    gs.run_command("db.execute", sql="UPDATE %s SET distance =  field_4" % (voutpoint))
    gs.run_command(
        "db.execute", sql="UPDATE %s SET cat_line =  %d" % (voutpoint, int(vcat))
    )
    gs.run_command(
        "db.execute",
        sql="UPDATE %s SET distance =  %s WHERE cat = %s"
        % (voutpoint, vector_line_length, number_segmentpoints_with_end),
    )

    gs.run_command("db.dropcolumn", table=voutpoint, column="field_2", flags="f")

    gs.run_command("db.dropcolumn", table=voutpoint, column="field_4", flags="f")

    gs.message("Distance information added to attribute table.")
    gs.message("----")

    # export segment point attribute table as csv
    gs.message("Export segment point attribute table as CSV file ...")

    csv_to_export = os.path.join(directory, fpointscsv_export)

    gs.run_command(
        "db.out.ogr", input=voutpoint, output="%s" % (csv_to_export), format="CSV"
    )

    gs.message("Export done.")
    gs.message("----")

    # clean up some temporay files and maps
    gs.message("Some clean up ...")
    os.remove("%s" % segment_points_file_csv)
    gs.message("Clean up done.")
    gs.message("----")

    # v.fixed.segmentpoints done!
    gs.message("v.fixed.segmentpoints done!")


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
