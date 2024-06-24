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
# % description: Queries projection information spatially.
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
# % description: Logical operator for coordinates
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
# %option G_OPT_V_OUTPUT
# % key: bbox_map
# % description: Name for output vector map with bounding box lines
# % required: no
# %end
# %flag
# % key: l
# % description: Coordinates in latitude and longitude instead of east and north
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
# % description: Start GUI
# %end
# %flag
# % key: 1
# % description: Allow only one selection in GUI
# %end
# %rules
# % required: -g, coordinates, query, input
# % exclusive: coordinates, query, input
# % requires: operator, coordinates
# % requires: -l, coordinates
# % requires: -1, -g
# %end

import sys
import re
import grass.script as grass


def message(msg="", end=None):
    print(msg, end=end, file=sys.stderr, flush=True)


def main():
    try:
        import projpicker as ppik
    except ImportError:
        grass.fatal(_("ProjPicker not installed. Use 'pip install projpicker'"))

    coords = options["coordinates"]
    operator = options["operator"]
    query = options["query"]
    infile = options["input"]
    outfile = options["output"]
    fmt = options["format"]
    separator = options["separator"]
    bbox_map = options["bbox_map"]
    overwrite = grass.overwrite()

    latlon = flags["l"]
    print_geoms = flags["p"]
    no_header = flags["n"]
    single = flags["1"]
    if flags["g"]:
        if coords or query or infile:
            start_gui = "select"
        else:
            start_gui = "gui"
    else:
        start_gui = None

    if bbox_map and grass.parse_command("g.proj", flags="g")["unit"] != "degree":
        grass.fatal(_("Cannot create vector in degree in a non-degree mapset"))

    # ppik.start() appends input file contents to geometries from arguments,
    # but it can be confusing and is not supported in this module
    if coords:
        query = f"{operator}"
        coords = coords.split(",")
        for x, y in zip(coords[0::2], coords[1::2]):
            if latlon:
                x, y = y, x
            query += f" {y},{x}"

    geoms = ppik.read_file(infile) if infile else query.split()

    if separator == "pipe for plain; newline for srid":
        if fmt == "plain":
            separator = "|"
        elif fmt == "srid":
            separator = "\n"
    else:
        separator = grass.utils.separator(separator)

    bbox = ppik.start(
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

    if bbox_map:
        p = grass.feed_command(
            "v.in.ascii",
            input="-",
            output=bbox_map,
            format="standard",
            flags="n",
        )
        nbbox = len(bbox)
        for i in range(0, nbbox):
            b = bbox[i]
            cat = i + 1
            s = b.south_lat
            n = b.north_lat
            w = b.west_lon
            e = b.east_lon
            x = (w + e) / 2
            y = (s + n) / 2
            line = f"L 5 1\n{w} {s}\n{w} {n}\n{e} {n}\n{e} {s}\n{w} {s}\n1 {cat}\n"
            # XXX: these two lines don't work probably because areas overlap?
            # line = (
            #    f"B 5 1\n{w} {s}\n{w} {n}\n{e} {n}\n{e} {s}\n{w} {s}\n"
            #    f"1 {cat}\nC 1 1\n{x} {y}\n1 {cat}\n"
            # )
            # line = (
            #    f"B 5\n{w} {s}\n{w} {n}\n{e} {n}\n{e} {s}\n{w} {s}\n"
            #    f"C 1 1\n{x} {y}\n1 {cat}\n"
            # )
            line = line.encode()
            p.stdin.write(line)
        p.stdin.close()
        p.wait()

        if p.returncode != 0:
            grass.fatal(_("Error creating output vector map %s") % bbox_map)

        grass.run_command("v.db.addtable", map=bbox_map, columns="srid text, name text")
        for i in range(0, nbbox):
            message("\b" * 80 + _("Populating table...") + f" {i + 1}/{nbbox}", "")
            b = bbox[i]
            srid = f"{b.crs_auth_name}:{b.crs_code}"
            cat = i + 1
            grass.run_command(
                "db.execute",
                sql=(
                    f"UPDATE {bbox_map} "
                    f"SET srid='{srid}', "
                    f"""name='{b.crs_name.replace("'", "''")}' """
                    f"WHERE cat={cat}"
                ),
            )
        message()


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
