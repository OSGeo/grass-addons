#!/usr/bin/env python

#
########################################################################
#
# MODULE:       r.category.trim
# AUTHOR(S):    Paulo van Breugel (paulo AT ecodiv DOT earth)
# DESCRIPTION:  Export the categories, category labels and color codes (RGB)
#               as csv file or as a QGIS color map file. It will first remove
#               non-existing categories and their color definitions.
#               Optionally, map values can be reclassed into consecutive
#               categories values, whereby the category labels and colors are
#               retained.
#
# COPYRIGHT: (C) 2015-2021 Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: Export categories and corresponding colors as QGIS color file or csv file. Non-existing categories and their color definitions will be removed.
# % keyword: raster
# % keyword: color
# % keyword: color table
# % keyword: category
# %End

# %option
# % key: input
# % type: string
# % gisprompt: old,cell,raster
# % description: input map
# % key_desc: name
# % required: yes
# % multiple: no
# % guisection: Raster
# %end

# %option
# % key: output
# % type: string
# % gisprompt: new,cell,raster
# % description: output map
# % key_desc: name
# % required: no
# % multiple: no
# % guisection: Raster
# %end

# %option G_OPT_F_OUTPUT
# % key:csv
# % description: Attribute table (csv format)
# % key_desc: name
# % required: no
# % guisection: Export
# %end

# %option G_OPT_F_OUTPUT
# % key:qgis
# % description: QGIS color file (txt format)
# % key_desc: name
# % required: no
# % guisection: Export
# %end

# %flag:
# % key: n
# % description: Recode layer to get consecutive category values
# %end

# %rules
# % requires_all: -n, output
# %end

# =======================================================================
## General
# =======================================================================

# import libraries
import os
import sys
from subprocess import PIPE
from grass.pygrass.modules import Module
import grass.script as gs
import re


def main(options, flags):

    # Check if running in GRASS
    gisbase = os.getenv("GISBASE")
    if not gisbase:
        gs.fatal(
            _(
                "$GISBASE not defined. You must be in GRASS GIS to run \
        this program"
            )
        )
        return 0

    # Input
    IP = options["input"]
    OP = options["output"]
    CSV = options["csv"]
    QGIS = options["qgis"]
    flags_n = flags["n"]

    # Check if raster is integer
    iscell = gs.raster.raster_info(IP)["datatype"]
    if iscell != "CELL":
        gs.error(_("Input should be an integer raster layer"))

    # Get map category values and their labels
    CATV = Module("r.category", map=IP, stdout_=PIPE).outputs.stdout
    RCAT = CATV.split("\n")
    RCAT = [_f for _f in RCAT if _f]
    RID = [z.split("\t")[0] for z in RCAT]
    RIDI = list(map(int, RID))

    # Get full color table
    RCOL = gs.read_command("r.colors.out", map=IP).split("\n")
    RCOL = [x for x in RCOL if "nv" not in x and "default" not in x]
    RCOL = [_f for _f in RCOL if _f]
    CCAT = [z.split(" ")[0] for z in RCOL]
    idx = [i for i, item in enumerate(CCAT) if not re.search("\.", item)]
    CCAT = [CCAT[i] for i in idx]
    RCOL = [RCOL[i] for i in idx]
    CCAT = list(map(int, CCAT))

    # Set strings / list to be used in loop
    CR = ""
    RECO = ""
    CL = ""
    CV = []

    # recode to consecutive category values
    if flags_n:
        RIDN = list(range(1, len(RID) + 1))
        RLAB = [z.split("\t")[1] for z in RCAT]
        for j in range(len(RID)):
            RECO = "{0}{1}:{1}:{2}\n".format(RECO, RID[j], RIDN[j])
            A = list(map(int, [i for i, x in enumerate(CCAT) if x == RIDI[j]]))
            if A:
                ADCR = RCOL[A[0]].split(" ")[1]
                CR = "{}{} {}\n".format(CR, RIDN[j], ADCR)
                CL = "{}{}|{}\n".format(CL, RIDN[j], RLAB[j])
                CV.append(ADCR)

        CR = "{}nv 255:255:255\ndefault 255:255:255\n".format(CR)
        Module(
            "r.recode",
            flags="a",
            input=IP,
            output=OP,
            rules="-",
            stdin_=RECO,
            quiet=True,
        )
        Module("r.colors", map=OP, rules="-", stdin_=CR, quiet=True)
        Module("r.category", map=OP, rules="-", stdin_=CL, quiet=True, separator="pipe")
    else:
        # Check if new layer should be created
        if len(OP) > 0:
            k = "{},{}".format(IP, OP)
            gs.run_command("g.copy", raster=k)
        else:
            OP = IP

        # Remove redundant categories
        Module("r.category", map=OP, rules="-", stdin_=CATV, quiet=True)

        # Write color rules and assign colors
        for j in range(len(RIDI)):
            A = list(map(int, [i for i, x in enumerate(CCAT) if x == RIDI[j]]))
            if A:
                ADCR = RCOL[A[0]].split(" ")[1]
                CR = CR + str(RIDI[j]) + " " + ADCR + "\n"
                CV.append(ADCR)
        CR = "{}nv 255:255:255\ndefault 255:255:255\n".format(CR)
        Module("r.colors", map=OP, rules="-", stdin_=CR, quiet=True)

    # If attribute table (csv format) should be written
    if len(CSV) > 0:
        if flags_n:
            RCAT1 = [w.replace("|", ",'") for w in [_f for _f in CL.split("\n") if _f]]
        else:
            RCAT1 = [w.replace("\t", ",'") for w in RCAT]
        RCAT1 = ["{}'".format(w) for w in RCAT1]
        RCAT1.insert(0, "CATEGORY,CATEGORY LABEL")
        CV1 = list(CV)
        CV1.insert(0, "RGB")
        with open(CSV, "w") as text_file:
            for k in range(len(RCAT1)):
                text_file.write("{},{}\n".format(RCAT1[k], CV1[k]))

    # If QGIS Color Map text files should be written
    if len(QGIS) > 0:
        RGB = [w.replace(":", ",") for w in CV]
        if flags_n:
            RCAT = [_f for _f in CL.split("\n") if _f]
        else:
            RCAT = [w.replace("\t", "|") for w in RCAT]
        with open(QGIS, "w") as text_file:
            text_file.write("# QGIS color map for {}\n".format(OP))
            text_file.write("INTERPOLATION:EXACT\n")
            for k in range(len(RCAT)):
                RC2 = RCAT[k].split("|")
                if RC2[1]:
                    text_file.write("{},{},255,{}\n".format(RC2[0], RGB[k], RC2[1]))
                else:
                    text_file.write("{},{},255,{}\n".format(RC2[0], RGB[k], "-"))


if __name__ == "__main__":
    sys.exit(main(*gs.parser()))
