#!/usr/bin/env python
#
#############################################################################
#
# MODULE:      v.transects.py
# AUTHOR(S):   Eric Hardin
# PURPOSE:     Creates lines or quadrilateral areas perpendicular to a polyline
# COPYRIGHT:   (C) 2013
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
# UPDATES:     John Lloyd November 2011
#              Anna Petrasova 2013 (update for GRASS 7)
#
#############################################################################
# %module
# % description: Creates transect lines or quadrilateral areas at regular intervals perpendicular to a polyline.
# % keyword: vector
# % keyword: transect
# %end
# %option G_OPT_V_INPUT
# %end
# %option G_OPT_V_OUTPUT
# %end
# %option
# % key: transect_spacing
# % type: double
# % description: Transect spacing along input polyline
# % required: yes
# %end
# %option
# % key: dleft
# % type: double
# % label: Distance transect extends to the left of input line
# % description: Default is the same as the transect spacing
# % required: no
# %end
# %option
# % key: dright
# % type: double
# % label: Distance transect extends to the right of input line
# % description: Default is the same as the transect spacing
# % required: no
# %end
# %option G_OPT_V_TYPE
# % multiple: no
# % options: point,line,area
# % answer: line
# %end
# %option
# % key: metric
# % type: string
# % description: Determines how transect spacing is measured
# % multiple: no
# % options: straight, along
# % descriptions: straight;Straight distance between transect points;along;Distance along the line
# % answer: straight
# %end
# %option
# % key: transect_perpendicular
# % type: string
# % description: Determines which line is the transect perpendicular to
# % multiple: no
# % options: trend, line
# % descriptions: trend;Perpendicular to the line connecting transect points;line;Perpendicular to the particular segment of the original line
# % answer: trend
# %end
# %flag
# % key: l
# % description: Use the last point of the line to create transect
# %end

from subprocess import Popen, PIPE, STDOUT
from numpy import array
from math import sqrt
import grass.script as grass
import tempfile
import random


def tempmap():
    """!Returns the name of a vector map not in the current mapset.

    Mapname is of the form temp_xxxxxx where xxxxxx is a random number.
    """
    rand_number = [random.randint(0, 9) for i in range(6)]
    rand_number_str = "".join(map(str, rand_number))
    mapname = "temp_" + rand_number_str
    maplist = grass.read_command("g.list", type="vector", mapset=".").split()
    while mapname in maplist:
        rand_number = [random.randint(0, 9) for i in range(6)]
        rand_number_str = "".join(map(str, rand_number))
        mapname = "temp_" + rand_number_str
        maplist = grass.read_command("g.list", type="vector", mapset=".").split()
    return mapname


def loadVector(vector):
    """!Load vector lines into python list.

    Returns v:
    len(v) = number of lines in vector map
    len(v[i]) = number of vertices in ith line
    v[i][j] = [ xij, yij ] ,i.e., jth vertex in ith line
    """
    # expVecCmmd = grass.encode('v.out.ascii format=standard input={}'.format(vector))
    # JL    p = Popen(expVecCmmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    # p = Popen(expVecCmmd, shell=True, stdin=PIPE, stdout=PIPE,
    #          stderr=STDOUT, close_fds=False)
    vectorAscii = (
        grass.read_command("v.out.ascii", format="standard", input=vector)
        .strip("\n")
        .split("\n")
    )
    l = 0
    while "ORGANIZATION" not in vectorAscii[l]:
        l += 1
    while ":" in vectorAscii[l]:
        l += 1
    v = []
    while l < len(vectorAscii):
        line = vectorAscii[l].split()
        if line[0] in ["L", "B", "A"]:
            skip = len(line) - 2
            vertices = int(line[1])
            l += 1
            v.append([])
            for i in range(vertices):
                v[-1].append(list(map(float, vectorAscii[l].split()[:2])))
                l += 1
            l += skip
        elif line[0] in ["P", "C", "F", "K"]:
            skip = len(line) - 2
            vertices = int(line[1])
            l += 1
            for i in range(vertices):
                l += 1
            l += skip
        else:
            grass.fatal(_("Problem with line: <%s>") % vectorAscii[l])
    if len(v) < 1:
        grass.fatal(_("Zero lines found in vector map <%s>") % vector)
    return v


def get_transects_locs(vector, transect_spacing, dist_function, last_point):
    """!Get transects locations along input vector lines."""
    # holds locations where transects should intersect input vector lines
    transect_locs = []
    vectors = []
    for line in vector:
        transect_locs.append([line[0]])
        vectors.append([[line[0], line[1]]])
        # i starts at the beginning of the line.
        # j walks along the line until j and i are separated by a distance of transect_spacing.
        # then, a transect is placed at j, i is moved to j, and this is iterated until the end of the line is reached
        i = 0
        j = i + 1
        while j < len(line):
            d = dist_function(line, i, j)
            if d > transect_spacing:
                r = (transect_spacing - dist_function(line, i, j - 1)) / (
                    dist_function(line, i, j) - dist_function(line, i, j - 1)
                )
                transect_locs[-1].append(
                    (r * array(line[j]) + (1 - r) * array(line[j - 1])).tolist()
                )
                vectors[-1].append([line[j - 1], transect_locs[-1][-1]])
                i = j - 1
                line[i] = transect_locs[-1][-1]
            else:
                j += 1
        if last_point:
            transect_locs[-1].append(line[j - 1])
            vectors[-1].append([line[j - 2], line[j - 1]])
    return transect_locs, vectors


def get_transect_ends(transect_locs, vectors, trend, dleft, dright):
    """!From transects locations along input vector lines, get transect ends."""
    transect_ends = []
    if not trend:
        for k, transect in enumerate(transect_locs):
            # if a line in input vec was shorter than transect_spacing
            if len(transect) < 2:
                continue  # then don't put a transect on it
            transect_ends.append([])
            transect = array(transect)
            v = NR(*vectors[k][0])  # vector pointing parallel to transect
            transect_ends[-1].append(
                [transect[0] + dleft * v, transect[0] - dright * v]
            )
            for i in range(1, len(transect)):
                v = NR(*vectors[k][i])
                transect_ends[-1].append(
                    [transect[i] + dleft * v, transect[i] - dright * v]
                )
    else:
        for transect in transect_locs:
            # if a line in input vec was shorter than transect_spacing
            if len(transect) < 2:
                continue  # then don't put a transect on it
            transect_ends.append([])
            transect = array(transect)
            v = NR(transect[0], transect[1])  # vector pointing parallel to transect
            transect_ends[-1].append(
                [transect[0] + dleft * v, transect[0] - dright * v]
            )
            for i in range(1, len(transect) - 1, 1):
                v = NR(transect[i - 1], transect[i + 1])
                transect_ends[-1].append(
                    [transect[i] + dleft * v, transect[i] - dright * v]
                )
            v = NR(transect[-2], transect[-1])
            transect_ends[-1].append(
                [transect[-1] + dleft * v, transect[-1] - dright * v]
            )
    return transect_ends


def dist_euclidean(line, i1, i2):
    """!Calculates distance between two points"""
    return sqrt((line[i1][0] - line[i2][0]) ** 2 + (line[i1][1] - line[i2][1]) ** 2)


def dist_along_line(line, i1, i2):
    distance = 0
    for i in range(i1, i2):
        distance += dist_euclidean(line, i, i + 1)
    return distance


def NR(ip, fp):
    """!Take a vector, normalize and rotate it 90 degrees."""
    x = fp[0] - ip[0]
    y = fp[1] - ip[1]
    r = sqrt(x**2 + y**2)
    return array([-y / r, x / r])


def writeTransects(transects, output):
    """!Writes transects."""
    transects_str = ""
    for transect in transects:
        transects_str += "\n".join(
            [
                "L 2\n"
                + " ".join(map(str, end_points[0]))
                + "\n"
                + " ".join(map(str, end_points[1]))
                + "\n"
                for end_points in transect
            ]
        )
    # JL Rewrote Temporary File Logic for Windows
    _, temp_path = tempfile.mkstemp()
    a = open(temp_path, "w")
    a.write(transects_str)
    a.seek(0)
    a.close()
    grass.run_command(
        "v.in.ascii", flags="n", input=temp_path, output=output, format="standard"
    )


def writeQuads(transects, output):
    """!Writes areas."""
    quad_str = ""
    cnt = 1
    for line in transects:
        for tran in range(len(line) - 1):
            pt1 = " ".join(map(str, line[tran][0]))
            pt2 = " ".join(map(str, line[tran][1]))
            pt3 = " ".join(map(str, line[tran + 1][1]))
            pt4 = " ".join(map(str, line[tran + 1][0]))
            pt5 = pt1
            # centroid is the average of the four corners
            c = " ".join(
                map(
                    str,
                    [
                        0.25
                        * (
                            line[tran][0][0]
                            + line[tran][1][0]
                            + line[tran + 1][0][0]
                            + line[tran + 1][1][0]
                        ),
                        0.25
                        * (
                            line[tran][0][1]
                            + line[tran][1][1]
                            + line[tran + 1][0][1]
                            + line[tran + 1][1][1]
                        ),
                    ],
                )
            )
            quad_str += "B 5\n" + "\n".join([pt1, pt2, pt3, pt4, pt5]) + "\n"
            quad_str += "C 1 1\n" + c + "\n1 " + str(cnt) + "\n"
            cnt += 1
    # JL Rewrote Temporary File Logic for Windows
    _, temp_path = tempfile.mkstemp()
    a = open(temp_path, "w")
    a.write(quad_str)
    a.seek(0)
    a.close()
    grass.run_command(
        "v.in.ascii", flags="n", input=a.name, output=output, format="standard"
    )


def writePoints(transect_locs, output):
    """!Writes points."""
    pt_str = ""
    for pts in transect_locs:
        pt_str += "\n".join([",".join(map(str, pt)) for pt in pts]) + "\n"
    _, temp_path = tempfile.mkstemp()
    a = open(temp_path, "w")
    a.write(pt_str)
    a.seek(0)
    a.close()
    grass.run_command(
        "v.in.ascii",
        input=a.name,
        output=output,
        format="point",
        separator=",",
        x=1,
        y=2,
    )


def main():
    vector = options["input"]
    output = options["output"]
    # JL Handling Invalid transect_spacing parameter
    try:
        transect_spacing = float(options["transect_spacing"])
    except:
        grass.fatal(_("Invalid transect_spacing value."))
    if transect_spacing == 0.0:
        grass.fatal(_("Zero invalid transect_spacing value."))
    dleft = options["dleft"]
    dright = options["dright"]
    shape = options["type"]
    last_point = flags["l"]

    if not dleft:
        dleft = transect_spacing
    else:
        # JL Handling Invalid dleft parameter
        try:
            dleft = float(dleft)
        except:
            grass.fatal(_("Invalid dleft value."))
    if not dright:
        dright = transect_spacing
    else:
        # JL Handling Invalid dright parameter
        try:
            dright = float(dright)
        except:
            grass.fatal(_("Invalid dright value."))
    # check if input file does not exists
    if not grass.find_file(vector, element="vector")["file"]:
        grass.fatal(_("<%s> does not exist.") % vector)
    # check if output file exists
    if grass.find_file(output, element="vector")["mapset"] == grass.gisenv()["MAPSET"]:
        if not grass.overwrite():
            grass.fatal(_("output map <%s> exists") % output)

    # JL Is the vector a line and does if have at least one feature?
    info = grass.parse_command("v.info", flags="t", map=vector)
    if info["lines"] == "0":
        grass.fatal(_("vector <%s> does not contain lines") % vector)

    #################################
    v = loadVector(vector)
    if options["metric"] == "straight":
        dist = dist_euclidean
    else:
        dist = dist_along_line
    if options["transect_perpendicular"] == "trend":
        trend = True
    else:
        trend = False
    transect_locs, vectors = get_transects_locs(v, transect_spacing, dist, last_point)
    temp_map = tempmap()
    if shape == "line" or not shape:
        transect_ends = get_transect_ends(transect_locs, vectors, trend, dleft, dright)
        writeTransects(transect_ends, temp_map)
    elif shape == "area":
        transect_ends = get_transect_ends(transect_locs, vectors, trend, dleft, dright)
        writeQuads(transect_ends, temp_map)
    else:
        writePoints(transect_locs, temp_map)

    grass.run_command(
        "v.category", input=temp_map, output=output, option="add", type=shape
    )
    grass.run_command("g.remove", flags="f", type="vector", name=temp_map)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
