#!/usr/bin/env python

############################################################################
#
# MODULE:        v.concave.hull
# AUTHOR(S):        Markus Metz
# PURPOSE:        Creates a concave hull around points
# COPYRIGHT:        (C) 2013-2014 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################


# %module
# % description: Creates a concave hull around points.
# % keyword: vector
# % keyword: geometry
# % keyword: alpha shape
# %end
# %option G_OPT_V_INPUT
# % label: Input points
# %end
# %option G_OPT_V_OUTPUT
# %end
# %option
# % key: threshold
# % type: double
# % description: Lower values make the hull more concave
# % required : no
# % answer: 7
# % options: 0-10
# %end

import sys
import os
import atexit
import math
import grass.script as grass


def cleanup():
    for ext in ["", ".sort"]:
        grass.try_remove(tmp + ext)
    grass.run_command(
        "g.remove", flags="f", type="vector", pattern=prefix + "_*", quiet=True
    )


def sortfile(infile, outfile):
    inf = open(infile, "r")
    outf = open(outfile, "w")

    if grass.find_program("sort", "-n"):
        grass.run_command("sort", flags="n", stdin=inf, stdout=outf)
    else:
        # FIXME: we need a large-file sorting function
        grass.warning(_("'sort' not found: sorting in memory"))
        lines = inf.readlines()
        for i in range(len(lines)):
            lines[i] = float(lines[i].rstrip("\r\n"))
        lines.sort()
        for line in lines:
            outf.write(str(line) + "\n")

    inf.close()
    outf.close()


def main():
    global tmp, prefix
    tmp = grass.tempfile()
    prefix = "concave_hull_tmp_%d" % os.getpid()

    input = options["input"]
    output = options["output"]
    perc = options["threshold"]

    perc = float(perc) + 90

    delaunay = prefix + "_delaunay"

    grass.message(_("Delaunay triangulation..."))
    grass.run_command("v.delaunay", input=input, output=delaunay, quiet=True)

    out_points = prefix + "_delaunay_pnts"
    out_lines_nocat = prefix + "_delaunay_lines_nocat"
    out_lines = prefix + "_delaunay_lines"
    out_lines_tmp = prefix + "_delaunay_lines_tmp"

    grass.message(_("Geometry conversion..."))
    grass.run_command(
        "v.extract",
        input=delaunay,
        output=out_lines_tmp,
        type="boundary",
        layer="-1",
        quiet=True,
    )
    grass.run_command(
        "v.type",
        input=out_lines_tmp,
        output=out_lines_nocat,
        from_type="boundary",
        to_type="line",
        quiet=True,
    )
    grass.run_command(
        "v.type",
        input=delaunay,
        output=out_points,
        from_type="centroid",
        to_type="point",
        quiet=True,
    )

    grass.run_command(
        "v.category",
        input=out_lines_nocat,
        output=out_lines,
        op="add",
        type="line",
        quiet=True,
    )
    grass.run_command(
        "v.db.addtable",
        map=out_lines,
        col="cat integer,length double precision",
        quiet=True,
    )

    grass.message(_("Evaluating threshold..."))
    grass.run_command(
        "v.to.db", map=out_lines, type="line", op="length", col="length", quiet=True
    )

    db_info = grass.vector_db(map=out_lines, layer="1")[1]
    table = db_info["table"]
    database = db_info["database"]
    driver = db_info["driver"]
    sql = "SELECT length FROM %s" % (table)
    tmpf = open(tmp, "w")
    grass.run_command(
        "db.select",
        flags="c",
        table=table,
        database=database,
        driver=driver,
        sql=sql,
        stdout=tmpf,
    )
    tmpf.close()

    # check if result is empty
    tmpf = open(tmp, "r")
    if tmpf.read(1) == "":
        grass.fatal(_("Table <%s> contains no data.") % table)
    tmpf.close()

    N = 0
    tmpf = open(tmp)
    for line in tmpf:
        N += 1
    tmpf.close()

    max_length = 0.0
    sortfile(tmp, tmp + ".sort")
    ppos = round(N * perc / 100)

    perc_orig = perc
    while ppos >= N and perc >= 90:
        perc -= 1
        ppos = round(N * perc / 100)

    if perc == 89:
        grass.fatal(_("Cannot calculate hull. Too few points."))

    if perc_orig > perc:
        thresh = int(perc) - 90
        grass.warning(_("Threshold reduced to %d to calculate hull" % thresh))

    inf = open(tmp + ".sort", "r")
    l = 0
    for line in inf:
        if l == ppos:
            max_length = float(line.rstrip("\r\n"))
            break
        l += 1
    inf.close()

    grass.message(_("Feature selection..."))
    lines_concave = prefix + "_delaunay_lines_select"
    lines_concave_nocat = prefix + "_delaunay_lines_select_nocat"
    grass.run_command(
        "v.extract",
        input=out_lines,
        output=lines_concave,
        type="line",
        where="length < %f" % max_length,
        quiet=True,
    )

    grass.run_command(
        "v.category",
        input=lines_concave,
        output=lines_concave_nocat,
        type="line",
        op="del",
        cat="-1",
        quiet=True,
    )

    borders_concave = prefix + "_delaunay_borders_select"
    grass.run_command(
        "v.type",
        input=lines_concave_nocat,
        output=borders_concave,
        from_type="line",
        to_type="boundary",
        quiet=True,
    )

    areas_concave = prefix + "_delaunay_areas_select"
    grass.run_command(
        "v.centroids", input=borders_concave, output=areas_concave, quiet=True
    )
    grass.run_command("v.db.droptable", map=areas_concave, flags="f", quiet=True)
    grass.run_command(
        "v.db.addtable", map=areas_concave, col="cat integer,count integer", quiet=True
    )

    grass.run_command(
        "v.vect.stats",
        points=out_points,
        areas=areas_concave,
        ccolumn="count",
        quiet=True,
    )

    areas_concave_extr = prefix + "_delaunay_areas_extract"

    grass.run_command(
        "v.extract",
        input=areas_concave,
        output=areas_concave_extr,
        type="area",
        where="count = 1",
        quiet=True,
    )

    grass.message(_("The following warnings can be ignored"), flag="i")
    grass.run_command(
        "v.dissolve",
        input=areas_concave_extr,
        output=output,
        col="count",
        layer="1",
        quiet=True,
    )
    grass.message(_("Concave hull successfully created"))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
