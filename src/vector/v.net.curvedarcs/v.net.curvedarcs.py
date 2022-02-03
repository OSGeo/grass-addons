#!/usr/bin/env python
#
############################################################################
#
# MODULE:       v.net.curvedarcs
# AUTHOR(S):    Moritz Lennert
# PURPOSE:      Draws curved arcs
# COPYRIGHT:    (C) 2017 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################


# %module
# % description: Draws curved arcs between points (e.g. flows)
# % keyword: vector
# % keyword: network
# % keyword: flows
# %end

# %option G_OPT_V_INPUT
# % label: Point map containing origins and destinations
# %end

# %option G_OPT_V_FIELD
# % label: Layer number where to find point categories
# %end

# %option G_OPT_F_INPUT
# % key: flow_input_file
# % label: File containing origins, destinations and flow volumes
# %end

# %option G_OPT_F_SEP
# % label: Separator used in input text file
# %end

# %option G_OPT_V_OUTPUT
# % label: Output map with curved lines
# %end

# %option
# % key: minimum_offset
# % type: double
# % label: minimum offset at furthest point from straight line
# % required: yes
# %end

# %option
# % key: maximum_offset
# % type: double
# % label: maximum offset at furthest point from straight line
# % required: yes
# %end

# %option
# % key: vertices
# % type: integer
# % label: number of vertices used to draw curved lines
# % answer: 30
# %end

# %flag
# % key: s
# % description: Draw also short line for flow from and to same node
# %end

import os
import atexit
import math
import grass.script as gscript


def cleanup():
    if tmplines:
        gscript.run_command(
            "g.remove", flags="f", type="vector", name=tmplines, quiet=True
        )
    if tmplines2:
        gscript.run_command(
            "g.remove", flags="f", type="vector", name=tmplines2, quiet=True
        )
    if tmppoints:
        gscript.run_command(
            "g.remove", flags="f", type="vector", name=tmppoints, quiet=True
        )

    gscript.try_remove(vseginfile)
    gscript.try_remove(vnetinfile)


def write_segmentdefs(lineinfo, minoffset, maxoffset, nbvertices):

    filename = gscript.tempfile()
    maxlength = max(lineinfo.values())
    step = 100000 / nbvertices
    t = [x / 100000.0 for x in range(0, int(math.pi * 100000), step)]
    x = [a / max(t) * 100 for a in t]
    x[-1] -= 0.001
    with open(filename, "w") as fout:
        for linecat in lineinfo:
            offset = lineinfo[linecat] / maxlength * maxoffset
            if offset < minoffset:
                offset = minoffset
            y = [math.sin(a) * offset for a in t]
            P = list(zip(x, y))
            cat = linecat * 10000
            for px, py in P:
                cat += 1
                fout.write("P %d %d %f%% %f\n" % (cat, linecat, px, py))

    return filename, len(x)


def write_segarcdefs(lineinfo, maxcat):

    filename = gscript.tempfile()
    with open(filename, "w") as fout:
        for arccat in lineinfo:
            for cat in range(1, maxcat):
                pointcat = arccat * 10000 + cat
                fout.write("%d %d %d\n" % (arccat, pointcat, pointcat + 1))

    return filename


def process_infile(flow_file, separator, header, sameok, outputfile):

    vnetinfile = gscript.tempfile()
    sqlfile = gscript.tempfile()
    cat = 0

    with open(vnetinfile, "w") as fout:
        with open(sqlfile, "w") as sqlout:
            sqlout.write("BEGIN TRANSACTION;\n")
            with open(flow_file, "r") as fin:
                for line in fin:
                    cat += 1
                    if header:
                        header = False
                        continue
                    data = line.rstrip().split(separator)
                    print(data)
                    if sameok or not (data[0] == data[1]):
                        fout.write("%s %s %s\n" % (cat, data[0], data[1]))
                        sqlout.write(
                            "UPDATE %s SET from_node = %s, to_node = %s, volume = %s WHERE cat = %d;\n"
                            % (outputfile, data[0], data[1], data[2], cat)
                        )
            sqlout.write("END TRANSACTION;\n")

    return vnetinfile, sqlfile


def main():
    orig_point_map = options["input"]
    flow_file = options["flow_input_file"]
    minoffset = float(options["minimum_offset"])
    maxoffset = float(options["maximum_offset"])
    vertices = int(options["vertices"])
    outputfile = options["output"]
    separator = gscript.separator(options["separator"])
    sameok = flags["s"]
    header = True

    pid = os.getpid()

    global tmplines, tmplines2, tmppoints, vseginfile, vnetinfile
    tmplines = "tmp_vnetcurvedarcs_tmplines_%d" % pid
    tmplines2 = "tmp_vnetcurvedarcs_tmplines2_%d" % pid
    tmppoints = "tmp_vnetcurvedarcs_tmppoints_%d" % pid

    vnetinfile, sqlfile = process_infile(
        flow_file, separator, header, sameok, outputfile
    )
    gscript.message(_("Creating straight flow lines..."))
    gscript.run_command(
        "v.net",
        points=orig_point_map,
        operation="arcs",
        file_=vnetinfile,
        out=tmplines,
        overwrite=True,
        quiet=True,
    )

    linedata = gscript.read_command(
        "v.to.db", flags="p", map_=tmplines, option="length", quiet=True
    ).splitlines()

    lineinfo = {}
    for line in linedata:
        data = line.split("|")
        if int(data[0]) > 0:
            lineinfo[int(data[0])] = float(data[1])

    vseginfile, maxcat = write_segmentdefs(lineinfo, minoffset, maxoffset, vertices)

    gscript.message(_("Creating points of curved lines..."))
    gscript.run_command(
        "v.segment",
        input_=tmplines,
        out=tmppoints,
        rules=vseginfile,
        overwrite=True,
        quiet=True,
    )

    gscript.message(_("Creating curved lines from points..."))

    vnetinfile = write_segarcdefs(lineinfo, maxcat)
    gscript.run_command(
        "v.net",
        points=tmppoints,
        output=tmplines,
        operation="arcs",
        file_=vnetinfile,
        overwrite=True,
        quiet=True,
    )

    gscript.run_command(
        "v.extract",
        input_=tmplines,
        output=tmplines2,
        layer=1,
        overwrite=True,
        quiet=True,
    )

    gscript.message(_("Creating polylines..."))
    gscript.run_command(
        "v.build.polylines",
        input_=tmplines2,
        output=outputfile,
        cats="multi",
        overwrite=True,
        quiet=True,
    )

    gscript.run_command(
        "v.db.addtable",
        map_=outputfile,
        columns="from_node int, to_node int, volume double precision",
        quiet=True,
        overwrite=True,
    )

    gscript.run_command("db.execute", input_=sqlfile, quiet=True)


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
