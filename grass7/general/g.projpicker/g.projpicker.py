#!/usr/bin/env python3

############################################################################
#
# MODULE:       g.projpicker
#
# AUTHOR(S):    Huidae Cho
#
# PURPOSE:      Queries projection information spatially. This module is a
#               wrapper around ProjPicker
#               <https://pypi.org/project/projpicker/>.
#
# COPYRIGHT:    (C) 2021 by Huidae Cho and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Queries projection information spatially
# % keyword: general
# % keyword: projection
# % keyword: create location
# %end
# %option G_OPT_M_COORDS
# % multiple: yes
# %end
# %option
# % key: operator
# % type: string
# % options: and,or,xor
# % answer: and
# % description: Logical operator
# %end
# %option
# % key: query
# % type: string
# % description: Query string
# %end
# %option G_OPT_F_INPUT
# % description: Name of input query file (- for stdin)
# % required: no
# %end
# %option G_OPT_F_OUTPUT
# % answer: -
# % description: Name for output file (- for stdout)
# % required: no
# %end
# %option
# % key: format
# % type: string
# % options: plain,json,pretty,sqlite,srid
# % answer: plain
# % description: Output file format
# %end
# %option G_OPT_F_SEP
# % answer: pipe for plain; newline for srid
# % label: Separator for plain and srid output formats; some projection names contain commas
# %end
# %flag
# % key: l
# % description: Coordinates in latitude and longitude instead of x and y
# %end
# %flag
# % key: p
# % description: Print parsed geometries in a list form for input validation and exit
# %end
# %flag
# % key: n
# % description: Do not print header for plain output format
# %end
# %flag
# % key: g
# % description: Start GUI for selecting a subset of queried projections
# %end
# %flag
# % key: 1
# % description: Allow only one selection in GUI
# %end
# %rules
# % required: coordinates, query, input
# % exclusive: coordinates, query, input
# % exclusive: -l, query, input
# % excludes: operator, query, input
# % requires: -1, -g
# %end

import sys
import re
import grass.script as grass
import projpicker as ppik


def main():
    coords = options["coordinates"]
    operator = options["operator"]
    query = options["query"]
    infile = options["input"]
    outfile = options["output"]
    fmt = options["format"]
    separator = options["separator"]
    overwrite = grass.overwrite()

    latlon = flags["l"]
    print_geoms = flags["p"]
    no_header = flags["n"]
    single = flags["1"]
    start_gui = flags["g"]

    # ppik.projpicker() appends input file contents to geometries from
    # arguments, but it can be confusing and is not supported in this module
    if coords:
        query = f"{operator}"
        coords = coords.split(",")
        for x, y in zip(coords[0::2], coords[1::2]):
            if latlon:
                x, y = y, x
            query += f" {y},{x}"

    if infile:
        geoms = ppik.read_file(infile)
    else:
        geoms = query.split()
        n = len(geoms)
        idx = []
        i = 0
        while i < n - 1:
            m = re.match("""^(|unit=)(["'])(.*)$""", geoms[i])
            if m:
                geoms[i] = m[1] + m[3]
                quote = m[2]
                if geoms[i].endswith(quote):
                    geoms[i] = geoms[i][: -len(quote)]
                else:
                    for j in range(i + 1, n):
                        idx.append(j)
                        m = re.match(f"^(.*){quote}$", geoms[j])
                        if m:
                            geoms[i] += f" {m[1]}"
                            break
                        else:
                            geoms[i] += f" {geoms[j]}"
                    i = j
            i += 1
        for i in reversed(idx):
            del geoms[i]

    if separator == "pipe for plain; newline for srid":
        if fmt == "plain":
            separator = "|"
        elif fmt == "srid":
            separator = "\n"
    else:
        separator = grass.utils.separator(separator)

    ppik.projpicker(
        geoms=geoms,
        outfile=outfile,
        fmt=fmt,
        no_header=no_header,
        separator=separator,
        print_geoms=print_geoms,
        overwrite=overwrite,
        start_gui=start_gui,
        single=single,
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
